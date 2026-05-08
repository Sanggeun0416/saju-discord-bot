# 사주 운세 디스코드 봇 - 프로젝트 핸드오프

> 이 문서는 Claude.ai 웹에서 시작한 작업을 로컬 Claude Code로 이어가기 위한 컨텍스트 요약본입니다.

---

## 1. 프로젝트 목표

사용자(이상근, 2005-04-16 02:39 생, 남)의 사주를 기반으로 **매일 오늘의 일진 운세를 분석**하고, **GitHub Actions로 자동 실행**되어 **디스코드 웹훅으로 알림**을 보내는 파이썬 프로그램.

---

## 2. 사용자 사주 정보 (하드코딩 대상)

```python
USER_NAME = "이상근"
USER_BIRTH = {
    "year": 2005, "month": 4, "day": 16,
    "hour": 2, "minute": 39,
    "is_male": True,
}
```

**사주 4주 (자동 계산 결과)**
- 년주: 乙酉 (을유)
- 월주: 庚辰 (경진)
- 일주: 庚午 (경오) ← **일간 庚金 = 본인**
- 시주: 丁丑 (정축, 축시 01:30~03:30)

**오행 분포**: 금 3, 토 2, 화 2, 목 1, **수 0** (수가 가장 부족 → 운세 분석 시 핵심 보정 포인트)

---

## 3. 현재까지 완성된 파일 구조

```
saju_discord/
├── daily_fortune.py    # 메인: 분석 → 디스코드 임베드 → 웹훅 전송
├── saju_engine.py      # 분석 엔진: 십신/오행/충합 계산
├── config.py           # 사용자 사주 정보
├── requirements.txt    # sxtwl, requests, python-dotenv
├── .env.example        # DISCORD_WEBHOOK_URL 예시
└── README.md           # 설치/실행/자동화 가이드
```

전체 코드는 이미 작성·테스트 완료 상태. 로컬에서는 **첨부된 saju_discord 폴더를 그대로 사용**하시거나 Claude Code에 "기존 코드 그대로 가져와줘"라고 하시면 됩니다.

---

## 4. 핵심 분석 로직 (saju_engine.py)

### 4-1. 십신 도출
- 일간(庚金) 기준으로 오늘 일진의 천간/지지 → 비견·겁재·식신·상관·정재·편재·정관·편관·정인·편인 자동 분류
- 오행 관계 + 음양 동일 여부로 판정

### 4-2. 충/합 판정
- 본인 일지(午)와 오늘 지지의 육충/육합/삼합 관계 체크

### 4-3. 점수 산출 (1~5점, 6개 영역)
- 영역: `work, study, money, relationship, love, health`
- 십신별 가중치 테이블 (`sipsin_weights` 딕셔너리)
- 천간 60% + 지지 40% 가중평균
- **부족 오행(수) 들어오면 +1 보너스**
- 충 발생 시 health -1, 합 발생 시 relationship +1

### 4-4. 헤드라인/추천/주의/길시간
- 십신별 메시지 풀에서 매칭
- 길한 시간대: 부족한 오행이 들어오는 시진 우선 추천

---

## 5. 디스코드 임베드 구조 (daily_fortune.py)

- **색상**: 총평 점수에 따라 초록(4.5+)/파랑(3.5+)/노랑(2.5+)/빨강(그 이하)
- **필드**: 일진 / 핵심 / 6개 영역 별점 / 길한 시간 / 추천 / 주의
- 봇 이름: "사주 운세봇"

---

## 6. GitHub Actions 자동화 (이번 차례에서 다음 단계)

### 6-1. 워크플로우 파일 위치
`.github/workflows/daily.yml`

### 6-2. 필수 구성 요소
```yaml
name: Daily Fortune
on:
  schedule:
    - cron: '0 22 * * *'  # UTC 22시 = KST 07시
  workflow_dispatch:       # 수동 실행 버튼

jobs:
  send-fortune:
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

### 6-3. GitHub 설정 체크리스트
- [ ] GitHub 저장소 생성 (Public 권장 - 무료 무제한)
- [ ] 코드 push (단, **`.env` 파일은 절대 커밋 금지** → `.gitignore` 추가 필요)
- [ ] Settings → Secrets and variables → Actions → `DISCORD_WEBHOOK_URL` 등록
- [ ] Actions 탭에서 수동 실행으로 테스트
- [ ] cron 시간 검증 (UTC 기준이라 한국 시간 -9시간)

### 6-4. 추가 필요 파일
- `.gitignore`: `.env`, `__pycache__/`, `*.pyc`, `fortune.log` 등 제외

---

## 7. 로컬 Claude Code에서 다음으로 할 일

### 우선순위 1: GitHub Actions 워크플로우 작성
- `.github/workflows/daily.yml` 생성
- `.gitignore` 생성

### 우선순위 2: 로컬 테스트
```bash
pip install -r requirements.txt
cp .env.example .env
# .env에 실제 디스코드 웹훅 URL 입력
python daily_fortune.py
```

### 우선순위 3: GitHub 푸시 & Secret 등록 & 수동 실행 테스트

### (선택) 추후 개선 아이디어
- **로깅 추가**: 실행 결과를 파일/디스코드 다른 채널로 저장
- **에러 알림**: 실패 시 별도 채널로 알림
- **연간 운세, 월운**: 일진뿐 아니라 더 큰 흐름 추가
- **여러 사용자 지원**: `users.yaml`로 다중 사용자 운세 일괄 발송
- **십이운성/신살 추가**: 천을귀인, 역마살 등 추가 분석
- **절기 정보**: 입춘·청명 등 절기 변동 알림
- **윤달 처리 검증**: sxtwl이 윤달 자동 처리하지만 엣지 케이스 테스트 필요
- **대운/세운 반영**: 현재 임오/계미 대운을 점수 계산에 반영

---

## 8. 알려진 이슈 / 검토 필요 사항

1. **시주 경계**: 02:39는 축시(01:30~03:30) 끝자락. 야자시·조자시 학파에 따라 인시(寅時)로 보는 견해도 있음. 현재는 표준 시진(축시) 적용.
2. **출생 지역 보정**: 현재 코드는 한국 표준시 기준. 진태양시(longitude 보정)는 미적용. 필요 시 수원(127.0286°E) 기준으로 약 -32분 보정 옵션 추가 가능.
3. **라이브러리 의존**: `sxtwl`이 중국 만세력 기반이라 한국 사주 표준과 99% 일치하지만 일부 절기 경계일에서 차이 가능성. 검증 권장.
4. **디스코드 임베드 길이 제한**: 필드 값 1024자, 전체 6000자 제한. 현재 메시지는 충분히 안전.

---

## 9. 핵심 코드 스니펫 (참고용)

### 십신 계산 함수 (saju_engine.py 핵심)
```python
def get_sipsin(day_gan_idx, target_gan_idx=None, target_zhi_idx=None):
    # 일간 기준으로 대상의 십신 반환
    # 오행 관계: 비겁(같음) / 식상(내가 생) / 재성(내가 극)
    #           / 관성(나를 극) / 인성(나를 생)
    # 음양 동일이면 정/비, 다르면 편/겁
```

### 점수 계산 (saju_engine.py)
```python
sipsin_weights = {
    "정관": (5, 4, 3, 4, 4, 3),  # work, study, money, rel, love, health
    "식신": (4, 4, 4, 4, 3, 4),
    # ... (10개 십신 모두 정의됨)
}
gan_w = sipsin_weights[gan_sipsin]
zhi_w = sipsin_weights[zhi_sipsin]
score = round(gan_w[i] * 0.6 + zhi_w[i] * 0.4)
```

---

## 10. Claude Code에 줄 첫 프롬프트 예시

```
이 폴더는 사주 기반 디스코드 알림 봇 프로젝트야.
HANDOFF.md를 먼저 읽어줘.
이어서 GitHub Actions 워크플로우 파일(.github/workflows/daily.yml)과
.gitignore 파일을 만들고, 로컬에서 한 번 테스트 실행해줘.
```

또는

```
HANDOFF.md 읽고, 다음 작업 우선순위대로 진행해줘.
중간에 막히는 부분 있으면 물어봐.
```
