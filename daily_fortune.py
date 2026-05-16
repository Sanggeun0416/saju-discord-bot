"""
매일 사주 기반 일진 운세를 디스코드 웹훅으로 전송

users.yaml에 사용자 목록을 정의하면 다중 사용자 지원.
실패 시 같은 웹훅으로 에러 알림 전송.
"""

import os
import sys
import json
import logging
import traceback
import requests
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
from dotenv import load_dotenv

# Windows 터미널 UTF-8 강제 설정
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# ── 로깅 설정 ────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("fortune.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# ── 사용자 로드 ──────────────────────────────────────────────────────────────

def load_users() -> list:
    """users.yaml 우선 로드, 없으면 config.py 폴백"""
    if os.path.exists("users.yaml"):
        try:
            import yaml
            with open("users.yaml", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            users = data.get("users", [])
            logger.info("users.yaml에서 %d명 로드", len(users))
            return users
        except Exception as e:
            logger.warning("users.yaml 로드 실패 (%s), config.py 사용", e)

    from config import USER_BIRTH, USER_NAME
    return [{"name": USER_NAME, **USER_BIRTH}]


# ── 디스코드 전송 ─────────────────────────────────────────────────────────────

def _post_discord(payload: dict):
    if not DISCORD_WEBHOOK_URL:
        raise RuntimeError("DISCORD_WEBHOOK_URL이 설정되지 않았습니다. .env 파일을 확인하세요.")
    response = requests.post(
        DISCORD_WEBHOOK_URL,
        data=json.dumps(payload, ensure_ascii=False),
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    response.raise_for_status()


def send_error_to_discord(error_msg: str):
    """실패 시 같은 채널에 에러 알림 전송"""
    if not DISCORD_WEBHOOK_URL:
        return
    payload = {
        "username": "사주 운세봇",
        "content": f"⚠️ **운세 전송 실패** ({datetime.now(KST).strftime('%Y-%m-%d %H:%M')})\n```\n{error_msg[:1800]}\n```",
    }
    try:
        requests.post(
            DISCORD_WEBHOOK_URL,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
    except Exception:
        pass  # 에러 알림 자체가 실패해도 프로세스 종료하지 않음


# ── 임베드 생성 ──────────────────────────────────────────────────────────────

def _star(n: int) -> str:
    return "⭐" * n + "☆" * (5 - n)


def build_discord_embed(fortune: dict, user_name: str) -> dict:
    today     = datetime.now(KST)
    date_str  = today.strftime("%Y년 %m월 %d일 (%a)")
    score     = fortune["overall_score"]

    if score >= 4.5:
        color = 0x2ECC71
    elif score >= 3.5:
        color = 0x3498DB
    elif score >= 2.5:
        color = 0xF1C40F
    else:
        color = 0xE74C3C

    sc = fortune["scores"]

    # ── 신살·십이운성 텍스트 ────────────────────────────────────────
    sinsal_text = "  ".join(fortune["sinsal"]) if fortune["sinsal"] else "해당 없음"
    sbu_text    = fortune["sibiunsung"]

    # ── 세운·월운·대운 텍스트 ───────────────────────────────────────
    def _period_line(label, pdata):
        g, z  = pdata["gan_sipsin"], pdata["zhi_sipsin"]
        brief = _SIPSIN_FORECAST.get(g, "")
        return f"**{label}** {pdata['pillar']} ({pdata['pillar_kr']}) — {g}·{z}  {brief}"

    dw = fortune["daewun"]
    if dw["gan_sipsin"]:
        dw_brief = _SIPSIN_FORECAST.get(dw["gan_sipsin"], "")
        daewun_line = (
            f"**대운** {dw['pillar']} ({dw['pillar_kr']}) {dw['start_age']}~{dw['end_age']}세"
            f" — {dw['gan_sipsin']}·{dw['zhi_sipsin']}  {dw_brief}"
        )
    else:
        daewun_line = f"**대운** 아직 미진입 ({dw['start_age']}세 시작 예정)"

    period_text = (
        _period_line("세운", fortune["sewun"]) + "\n"
        + _period_line("월운", fortune["wolwun"]) + "\n"
        + daewun_line
    )

    # ── 절기 텍스트 ─────────────────────────────────────────────────
    jg = fortune["jeolgi"]
    jeolgi_text = (
        f"현재 절기 **{jg['current']}** ({jg['current_date']})"
        f" → 다음 **{jg['next']}** ({jg['next_date']}, {jg['days_until_next']}일 후)"
    )

    fields = [
        {
            "name": "📅 오늘의 일진",
            "value": (
                f"**{fortune['day_pillar_kr']}** ({fortune['day_pillar']})\n"
                f"천간 **{fortune['day_gan_kr']}**({fortune['day_gan']}) — {fortune['gan_sipsin']}\n"
                f"지지 **{fortune['day_zhi_kr']}**({fortune['day_zhi']}) — {fortune['zhi_sipsin']}\n"
                f"십이운성: **{sbu_text}**"
            ),
            "inline": False,
        },
        {
            "name": "✨ 오늘의 핵심",
            "value": fortune["headline"],
            "inline": False,
        },
        {"name": "💼 업무",     "value": f"{_star(sc['work'])} ({sc['work']}/5)",         "inline": True},
        {"name": "📚 학습",     "value": f"{_star(sc['study'])} ({sc['study']}/5)",        "inline": True},
        {"name": "💰 재물",     "value": f"{_star(sc['money'])} ({sc['money']}/5)",        "inline": True},
        {"name": "👥 인간관계", "value": f"{_star(sc['relationship'])} ({sc['relationship']}/5)", "inline": True},
        {"name": "💕 연애",     "value": f"{_star(sc['love'])} ({sc['love']}/5)",          "inline": True},
        {"name": "🏃 건강",     "value": f"{_star(sc['health'])} ({sc['health']}/5)",      "inline": True},
        {
            "name":   "⚡ 신살",
            "value":  sinsal_text,
            "inline": False,
        },
        {
            "name":   "🌊 세운·월운·대운",
            "value":  period_text,
            "inline": False,
        },
        {
            "name":   "🌿 절기",
            "value":  jeolgi_text,
            "inline": False,
        },
        {
            "name":   "🕐 길한 시간대",
            "value":  fortune["lucky_hours"],
            "inline": False,
        },
        {
            "name":   "✅ 오늘 추천",
            "value":  fortune["do_list"],
            "inline": False,
        },
        {
            "name":   "⚠️ 오늘 주의",
            "value":  fortune["dont_list"],
            "inline": False,
        },
    ]

    return {
        "title":       f"🔮 {user_name}님의 오늘 운세",
        "description": f"**{date_str}**\n총평: {_star(round(score))} ({score}/5)",
        "color":       color,
        "fields":      fields,
        "footer":      {"text": "사주는 참고용이며, 실제 하루는 본인의 선택과 행동이 만듭니다."},
        "timestamp":   today.isoformat(),
    }


# 십신 한 줄 요약 (임베드 내부용)
_SIPSIN_FORECAST = {
    "비견": "독립·자립", "겁재": "경쟁·갈등 주의",
    "식신": "여유·표현 좋음", "상관": "창의력↑ 말조심",
    "정재": "꾸준한 결실", "편재": "활발한 활동",
    "정관": "안정·책임", "편관": "압박·도전",
    "정인": "학습·내실", "편인": "직관·전문성",
}


# ── 메인 ─────────────────────────────────────────────────────────────────────

def main():
    from saju_engine import SajuAnalyzer

    users   = load_users()
    success = 0
    errors  = []

    for user in users:
        name = user.get("name", "사용자")
        try:
            logger.info("=== %s 운세 분석 시작 ===", name)
            birth = {k: user[k] for k in ("year", "month", "day", "hour", "minute", "is_male")}
            birth["name"] = name
            analyzer = SajuAnalyzer(birth)
            fortune  = analyzer.analyze_today()

            logger.info("오늘 일진: %s  총점: %.1f", fortune["day_pillar_kr"], fortune["overall_score"])

            embed   = build_discord_embed(fortune, name)
            payload = {
                "username":   "사주 운세봇",
                "avatar_url": "https://cdn-icons-png.flaticon.com/512/2153/2153090.png",
                "embeds":     [embed],
            }
            _post_discord(payload)
            logger.info("%s 디스코드 전송 완료", name)
            success += 1

        except Exception as e:
            msg = f"{name}: {traceback.format_exc()}"
            logger.error("전송 실패\n%s", msg)
            errors.append(msg)

    if errors:
        send_error_to_discord("\n\n".join(errors))
        sys.exit(1)

    logger.info("=== 완료: %d/%d 명 전송 성공 ===", success, len(users))


if __name__ == "__main__":
    main()
