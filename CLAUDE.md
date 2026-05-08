# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Korean daily fortune Discord bot (매일 사주 운세 디스코드 알림 봇). Calculates a user's 사주 (four pillars of destiny) natal chart, computes daily pillar relationships, and sends a formatted embed to a Discord channel via webhook.

## Running the Bot

```bash
pip install -r requirements.txt
cp .env.example .env   # then set DISCORD_WEBHOOK_URL in .env
python daily_fortune.py
```

Scheduled execution options:
- **Cron (Linux/macOS):** `0 7 * * * cd /path/to/repo && python3 daily_fortune.py`
- **GitHub Actions:** UTC 22:00 trigger (= KST 07:00)
- **Windows Task Scheduler:** GUI

## Architecture

```
config.py          → user birth data (name, year/month/day/hour, gender)
saju_engine.py     → all astrology logic (SajuAnalyzer class)
daily_fortune.py   → entry point: calls engine, builds Discord embed, POSTs webhook
```

**Data flow:** `config.py` birth info → `SajuAnalyzer.__init__()` computes natal chart (4 pillars, 오행 distribution) → `analyze_today()` computes today's pillar, 십신 relationships, 충합, 6-domain scores (work/study/money/relationships/love/health), lucky hours → `daily_fortune.py` formats into Discord embed JSON → webhook POST.

**Key internals in `saju_engine.py`:**
- `get_sipsin(day_stem, target_stem)` — returns 十神 relationship label
- `get_chunggap(stem_or_branch_a, b)` — detects 충(clash) / 합(harmony)
- `SajuAnalyzer._calculate_scores()` — 1–5 star scoring per life domain with 오행 bonuses
- `SajuAnalyzer._calc_natal_chart()` — uses `sxtwl` library for calendar conversion and pillar extraction

## User Configuration

Edit `config.py` to change the target person's birth info — this is the only file end-users need to modify.

The `DISCORD_WEBHOOK_URL` must be set in `.env` (never commit `.env`).
