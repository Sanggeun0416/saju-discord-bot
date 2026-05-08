# 매일 사주 운세 디스코드 알림 봇

본인 사주와 오늘 일진의 십신·오행 관계를 분석해 매일 디스코드로 운세를 보내주는 파이썬 프로그램.

## 주요 기능

- **본인 사주 4주(연·월·일·시) 자동 계산** (`sxtwl` 만세력 라이브러리 사용)
- **오늘 일진의 십신 분석** (비견/겁재/식신/상관/재성/관성/인성)
- **본인 일지와 오늘 지지의 충·합 관계** 판단
- **6개 영역별 점수**: 업무/학습/재물/인간관계/연애/건강
- **부족한 오행 보충 여부**에 따른 보너스 점수
- **길한 시간대** 자동 추천
- 디스코드 임베드로 깔끔하게 출력

## 설치

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경 변수 파일 생성
cp .env.example .env
# .env 파일을 열어 DISCORD_WEBHOOK_URL 입력

# 3. config.py 에서 본인 생년월일시로 수정
```

## 디스코드 웹훅 URL 발급

1. 디스코드 서버에서 운세를 받을 채널 선택
2. 채널 이름 옆 ⚙️(채널 편집) 클릭
3. **연동(Integrations) → 웹후크(Webhooks) → 새 웹후크**
4. 봇 이름·아이콘 설정 후 **웹후크 URL 복사**
5. `.env` 파일의 `DISCORD_WEBHOOK_URL` 에 붙여넣기

## 실행

```bash
python daily_fortune.py
```

## 매일 자동 실행

### Linux/macOS — cron

```bash
crontab -e
# 매일 오전 7시 실행
0 7 * * * cd /path/to/saju_discord && /usr/bin/python3 daily_fortune.py >> fortune.log 2>&1
```

### Windows — 작업 스케줄러

1. 작업 스케줄러 → 기본 작업 만들기
2. 트리거: 매일, 원하는 시간
3. 동작: 프로그램 시작
   - 프로그램: `python.exe` 전체 경로
   - 인수 추가: `daily_fortune.py`
   - 시작 위치: 프로젝트 폴더 경로

### GitHub Actions (서버 없이 무료 운영)

`.github/workflows/daily.yml`:

```yaml
name: Daily Fortune
on:
  schedule:
    - cron: '0 22 * * *'  # UTC 22시 = KST 07시
  workflow_dispatch:

jobs:
  fortune:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - env:
          DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
        run: python daily_fortune.py
```

## 파일 구조

```
saju_discord/
├── daily_fortune.py    # 메인 실행 스크립트 (디스코드 전송)
├── saju_engine.py      # 사주 분석 엔진
├── config.py           # 본인 사주 정보
├── requirements.txt    # 의존성
├── .env                # 웹훅 URL (gitignore 필수)
├── .env.example        # 환경변수 예시
└── README.md
```

## 분석 로직 요약

1. **사주 4주 계산**: 양력 생년월일시 → `sxtwl` 라이브러리로 간지 계산
2. **십신 도출**: 일간 기준 오행·음양 관계로 비견~정인 10가지 분류
3. **오행 분포**: 본인 사주의 약한 오행/강한 오행 식별
4. **점수 산출**:
   - 십신별 영역 가중치 테이블 적용 (천간 60% + 지지 40%)
   - 부족한 오행이 들어오면 +1 보너스
   - 충(沖) 발생 시 건강 -1, 합(合) 발생 시 인간관계 +1
5. **추천/주의 행동**: 십신별 행동 풀에서 매칭

## 주의

사주 해석은 통계적·전통적 참고 자료로, 절대적 예언이 아닙니다. 즐거운 일상의 가벼운 길잡이로만 활용하세요.
