"""
매일 사주 기반 일진 운세를 디스코드 웹훅으로 전송하는 프로그램

사용법:
    1. .env 파일에 DISCORD_WEBHOOK_URL 설정
    2. config.py에 본인 사주 정보 입력
    3. python daily_fortune.py 실행 (또는 스케줄러로 매일 자동 실행)
"""

import os
import sys
import json
import requests
import sxtwl
from datetime import datetime
from dotenv import load_dotenv

# Windows 터미널에서 이모지/한글 출력을 위한 UTF-8 강제 설정
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from config import USER_BIRTH, USER_NAME
from saju_engine import SajuAnalyzer

load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def build_discord_embed(fortune: dict, user_name: str) -> dict:
    """운세 분석 결과를 디스코드 임베드 형식으로 변환"""

    today = datetime.now()
    date_str = today.strftime("%Y년 %m월 %d일 (%a)")

    # 별점에 따라 색상 결정 (왼쪽 사이드바)
    score = fortune["overall_score"]
    if score >= 4.5:
        color = 0x2ECC71   # 초록 (대길)
    elif score >= 3.5:
        color = 0x3498DB   # 파랑 (길)
    elif score >= 2.5:
        color = 0xF1C40F   # 노랑 (평)
    else:
        color = 0xE74C3C   # 빨강 (흉)

    # 임베드 필드 구성
    fields = [
        {
            "name": "📅 오늘의 일진",
            "value": (
                f"**{fortune['day_pillar_kr']}** ({fortune['day_pillar']})\n"
                f"천간 **{fortune['day_gan_kr']}**({fortune['day_gan']}) — {fortune['gan_sipsin']}\n"
                f"지지 **{fortune['day_zhi_kr']}**({fortune['day_zhi']}) — {fortune['zhi_sipsin']}"
            ),
            "inline": False,
        },
        {
            "name": "✨ 오늘의 핵심",
            "value": fortune["headline"],
            "inline": False,
        },
        {
            "name": "💼 업무",
            "value": f"{'⭐' * fortune['scores']['work']} ({fortune['scores']['work']}/5)",
            "inline": True,
        },
        {
            "name": "📚 학습",
            "value": f"{'⭐' * fortune['scores']['study']} ({fortune['scores']['study']}/5)",
            "inline": True,
        },
        {
            "name": "💰 재물",
            "value": f"{'⭐' * fortune['scores']['money']} ({fortune['scores']['money']}/5)",
            "inline": True,
        },
        {
            "name": "👥 인간관계",
            "value": f"{'⭐' * fortune['scores']['relationship']} ({fortune['scores']['relationship']}/5)",
            "inline": True,
        },
        {
            "name": "💕 연애",
            "value": f"{'⭐' * fortune['scores']['love']} ({fortune['scores']['love']}/5)",
            "inline": True,
        },
        {
            "name": "🏃 건강",
            "value": f"{'⭐' * fortune['scores']['health']} ({fortune['scores']['health']}/5)",
            "inline": True,
        },
        {
            "name": "🕐 길한 시간대",
            "value": fortune["lucky_hours"],
            "inline": False,
        },
        {
            "name": "✅ 오늘 추천",
            "value": fortune["do_list"],
            "inline": False,
        },
        {
            "name": "⚠️ 오늘 주의",
            "value": fortune["dont_list"],
            "inline": False,
        },
    ]

    embed = {
        "title": f"🔮 {user_name}님의 오늘 운세",
        "description": f"**{date_str}**\n총평: {'⭐' * round(score)} ({score}/5)",
        "color": color,
        "fields": fields,
        "footer": {
            "text": "사주는 참고용이며, 실제 하루는 본인의 선택과 행동이 만듭니다."
        },
        "timestamp": today.isoformat(),
    }

    return embed


def send_to_discord(embed: dict):
    """디스코드 웹훅으로 임베드 전송"""

    if not DISCORD_WEBHOOK_URL:
        print("❌ DISCORD_WEBHOOK_URL이 설정되지 않았습니다. .env 파일을 확인하세요.")
        sys.exit(1)

    payload = {
        "username": "사주 운세봇",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/2153/2153090.png",
        "embeds": [embed],
    }

    try:
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        response.raise_for_status()
        print(f"✅ 디스코드 전송 완료 ({datetime.now().strftime('%H:%M:%S')})")
    except requests.exceptions.RequestException as e:
        print(f"❌ 디스코드 전송 실패: {e}")
        sys.exit(1)


def main():
    print(f"🔮 {USER_NAME}님의 운세를 분석합니다...")

    analyzer = SajuAnalyzer(USER_BIRTH)
    fortune = analyzer.analyze_today()

    print(f"   오늘 일진: {fortune['day_pillar_kr']} ({fortune['day_pillar']})")
    print(f"   총평: {fortune['overall_score']}/5")

    embed = build_discord_embed(fortune, USER_NAME)
    send_to_discord(embed)


if __name__ == "__main__":
    main()
