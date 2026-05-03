"""FastAPI server for SRT macro GUI.

Run:
    uvicorn server:app --host 127.0.0.1 --port 8765
or:
    python server.py
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ValidationError

import config
import srt_worker

ROOT = Path(__file__).parent
app = FastAPI(title="SRT Macro (개인용)")


class CredentialsIn(BaseModel):
    srt_id: str
    srt_password: str
    card_number: str
    card_password: str
    card_validation: str
    card_expire: str
    card_type: str = "J"
    card_installment: int = 0


class SearchIn(BaseModel):
    dep: str
    arr: str
    date: str
    time: str


class JobIn(BaseModel):
    dep: str
    arr: str
    date: str = Field(pattern=r"^\d{8}$")
    time: str = Field(pattern=r"^\d{6}$")
    train_number: Optional[str] = None
    passengers: int = Field(ge=1, le=9, default=1)
    seat_pref: str = Field(default="any", pattern="^(general|special|any)$")
    pay_mode: str = Field(default="manual", pattern="^(auto|manual)$")


@app.get("/")
def index():
    return FileResponse(ROOT / "static" / "index.html")


app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")


@app.get("/api/config/status")
def get_config_status():
    return config.public_status()


@app.post("/api/config")
def post_config(body: CredentialsIn):
    try:
        creds = config.Credentials(
            srt_id=body.srt_id,
            srt_password=body.srt_password,
            card_number=body.card_number.replace("-", "").replace(" ", ""),
            card_password=body.card_password,
            card_validation=body.card_validation,
            card_expire=body.card_expire,
            card_type=body.card_type,
            card_installment=body.card_installment,
        )
    except ValidationError as e:
        msgs = [f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors()]
        raise HTTPException(status_code=422, detail="; ".join(msgs))
    config.save(creds)
    return config.public_status()


@app.delete("/api/config")
def delete_config():
    config.clear()
    return {"ok": True}


@app.post("/api/search")
def post_search(body: SearchIn):
    try:
        return {"trains": srt_worker.search_preview(body.dep, body.arr, body.date, body.time)}
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"SRT 조회 실패: {e}")


def _job_to_dict(j: srt_worker.Job) -> dict:
    return {
        "id": j.id,
        "status": j.status,
        "spec": {
            "dep": j.spec.dep,
            "arr": j.spec.arr,
            "date": j.spec.date,
            "time": j.spec.time,
            "train_number": j.spec.train_number,
            "passengers": j.spec.passengers,
            "seat_pref": j.spec.seat_pref,
            "pay_mode": j.spec.pay_mode,
        },
        "created_at": j.created_at,
        "attempts": j.attempts,
        "reservation": j.reservation_summary,
        "payment_deadline": j.payment_deadline,
        "error": j.error,
    }


@app.get("/api/jobs")
def list_jobs():
    return {"jobs": [_job_to_dict(j) for j in srt_worker.manager.list()]}


@app.post("/api/jobs")
def create_job(body: JobIn):
    if not config.exists():
        raise HTTPException(status_code=400, detail="자격증명을 먼저 저장해주세요")
    spec = srt_worker.JobSpec(
        dep=body.dep,
        arr=body.arr,
        date=body.date,
        time=body.time,
        train_number=body.train_number,
        passengers=body.passengers,
        seat_pref=body.seat_pref,
        pay_mode=srt_worker.PayMode(body.pay_mode),
    )
    job = srt_worker.manager.create(spec)
    return _job_to_dict(job)


@app.delete("/api/jobs/{job_id}")
def stop_job(job_id: str):
    if not srt_worker.manager.stop(job_id):
        raise HTTPException(status_code=404, detail="job not found")
    return {"ok": True}


@app.post("/api/jobs/{job_id}/pay")
def confirm_pay(job_id: str):
    if not srt_worker.manager.confirm_pay(job_id):
        raise HTTPException(status_code=400, detail="job not in RESERVED state")
    return {"ok": True}


@app.get("/api/jobs/{job_id}/log")
def get_log(job_id: str, since: int = 0):
    job = srt_worker.manager.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    lines = list(job.logs)
    return {"lines": lines[since:], "next": len(lines), "status": job.status}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8910, reload=False)
