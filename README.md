# SRT Macro

본인 SRT 계정·본인 카드로 매진된 SRT 좌석을 폴링·예매·결제하는 macOS 개인 도구.

> ⚠ **개인용.** 자격증명·카드정보는 본인 Mac의 **macOS Keychain** (Security.framework, login keychain)에 암호화 저장되며, 서버는 `127.0.0.1:8910`에만 바인딩됩니다. 디스크 평문 파일이 만들어지지 않습니다.
>
> ⚠ **법적 책임은 사용자 본인에게 있습니다.** 본인 계정·본인 카드 외 사용 금지.

---

## 친구한테 보낼 1줄 가이드 (설치)

친구가 본인 Mac에서 **터미널을 열어** 아래 한 줄 붙여넣고 엔터:

```bash
curl -fsSL https://raw.githubusercontent.com/Chihun-Lee/srt-macro/main/install.sh | bash
```

> 또는 [`SRT_매크로_설치.command`](https://github.com/Chihun-Lee/srt-macro/raw/main/SRT_매크로_설치.command) 파일 다운로드 → Finder에서 **우클릭 → 열기** (처음 한 번만)

설치 끝나면 **Launchpad → "SRT 매크로"** 검색 → 더블클릭 → 자동으로 브라우저가 열립니다.

종료는 **"SRT 매크로 종료"** 더블클릭.

### 친구 입장에서 일어나는 일

1. macOS가 명령행 도구 설치 안내 (이미 있으면 스킵, 없으면 5분 정도)
2. `~/.srt-macro/`에 코드 다운로드, 가상환경 생성
3. `~/Applications/SRT 매크로.app` + `SRT 매크로 종료.app` 생성
4. 처음 자격증명 저장 시 macOS Keychain 접근 허용 팝업 → **[항상 허용]** 클릭
5. 끝. 친구의 SRT/카드 정보는 친구 Mac의 Keychain에만 있고 외부로 나가지 않음

---

## 기능

- 출발/도착/날짜/시각/특정 열차번호 지정 → 백그라운드 폴링
- **폴링 간격: 1~30초 균등 랜덤** (트래픽 패턴 분산)
- 좌석 풀리면 즉시 예약, 결제는 두 가지 모드:
  - **수동** — 예약만 잡고 GUI에 안내, 사용자가 "결제 진행" 버튼 눌러야 카드결제
  - **자동** — 예약 직후 즉시 카드결제까지 자동 진행
- 여러 작업 동시 실행 가능
- 실시간 로그 (2초 갱신)
- 토스트 알림으로 행동 피드백

---

## 직접 빌드 / 개발

```bash
git clone https://github.com/Chihun-Lee/srt-macro.git
cd srt-macro
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py
# → http://127.0.0.1:8910
```

### 파일 구조

- `server.py` — FastAPI 엔트리
- `srt_worker.py` — JobManager + 폴링/예약/결제 워커
- `config.py` — 자격증명 Keychain 저장
- `static/index.html` — single-page GUI
- `install.sh` / `SRT_매크로_설치.command` — 친구용 원클릭 설치

### Notes

- 결제 타이밍: SRT는 예약 후 약 10분 안에 결제 안 하면 자동 취소. 수동 모드는 9분(540초) 사용자 확인 대기 후 timeout error 처리.
- NetFunnel rate-limit (anti-bot) 가 뜨면 잠시 멈췄다가 자동 재시도.
- 결제는 SRTrain `pay_with_card`를 통해 진행되며, 카드정보는 사용 시점에 Keychain에서 1회 읽어 메모리에서만 사용 후 폐기.
