# SRT Macro (개인용)

본인 SRT 계정·본인 카드로 매진된 SRT 좌석을 폴링·예매·결제하는 개인 도구.

> ⚠ **개인용 한정.** 본인 PC 로컬에서만 띄우세요. 서버는 `127.0.0.1:8910`에만 바인딩되며,
> 자격증명·카드정보는 `~/.config/k-skill/srt_macro.env` (mode 0600)에 저장됩니다.
> git 저장소에는 절대 올라가지 않습니다 (`.gitignore` 참고).

## Features

- GUI 첫 실행 시 SRT 아이디/비밀번호 + 카드정보를 한 번 입력하면 로컬 보안 파일에 저장
- 출발/도착/날짜/시각/특정 열차번호 지정 후 백그라운드 폴링
- **폴링 간격은 1~30초 사이 균등 랜덤** (트래픽 패턴 분산)
- 좌석 풀리면 즉시 예약, 결제는 두 가지 모드:
  - **수동 (manual)** — 예약만 잡고 GUI에 안내, 사용자가 "결제 진행" 버튼 눌러야 카드결제
  - **자동 (auto)** — 예약 직후 즉시 카드결제까지 자동 진행
- 여러 작업 동시 실행 가능
- 실시간 로그 표시 (2초 폴링)

## Setup

```bash
# miniforge env (project root)
conda activate srt
pip install -r requirements.txt
```

## Run

```bash
conda activate srt
python server.py
# → 브라우저에서 http://127.0.0.1:8910 열기
```

또는:

```bash
uvicorn server:app --host 127.0.0.1 --port 8910
```

## Files

- `server.py` — FastAPI 엔트리
- `srt_worker.py` — JobManager + 폴링/예약/결제 워커
- `config.py` — 자격증명 보안 저장 (0600)
- `static/index.html` — single-page GUI

## Notes

- 결제 타이밍: SRT는 예약 후 약 10분 안에 결제 안 하면 자동 취소.
  manual 모드는 9분(540초) 사용자 확인 대기 후 timeout error 처리.
- NetFunnel rate-limit (anti-bot) 가 뜨면 잠시 멈췄다가 자동 재시도.
- 결제는 SRTrain `pay_with_card`를 통해 진행되며, 카드정보는 메모리에서만 사용 후 즉시 폐기.
