"""
사주 분석 엔진 v2
- 십신/오행/충합 (기존)
- 십이운성, 신살(천을귀인/역마/도화/공망) (신규)
- 절기 정보 (신규)
- 대운/세운/월운 계산 및 점수 반영 (신규)
"""

import logging
import sxtwl
from datetime import datetime, timedelta, timezone

_KST = timezone(timedelta(hours=9))

logger = logging.getLogger(__name__)

# ── 천간/지지 기초 ──────────────────────────────────────────────────────────

GAN    = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
ZHI    = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
GAN_KR = ['갑', '을', '병', '정', '무', '기', '경', '신', '임', '계']
ZHI_KR = ['자', '축', '인', '묘', '진', '사', '오', '미', '신', '유', '술', '해']

GAN_ELEMENT  = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]   # 목화토금수
GAN_YINYANG  = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]   # 양=0, 음=1
ZHI_ELEMENT  = [4, 2, 0, 0, 2, 1, 1, 2, 3, 3, 2, 4]
ZHI_YINYANG  = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
ELEMENT_KR   = ['목(木)', '화(火)', '토(土)', '금(金)', '수(水)']

HOUR_RANGES = [
    ("23:30~01:30",  0, "자시(子時)"),
    ("01:30~03:30",  1, "축시(丑時)"),
    ("03:30~05:30",  2, "인시(寅時)"),
    ("05:30~07:30",  3, "묘시(卯時)"),
    ("07:30~09:30",  4, "진시(辰時)"),
    ("09:30~11:30",  5, "사시(巳時)"),
    ("11:30~13:30",  6, "오시(午時)"),
    ("13:30~15:30",  7, "미시(未時)"),
    ("15:30~17:30",  8, "신시(申時)"),
    ("17:30~19:30",  9, "유시(酉時)"),
    ("19:30~21:30", 10, "술시(戌時)"),
    ("21:30~23:30", 11, "해시(亥時)"),
]

# ── 십이운성 ────────────────────────────────────────────────────────────────

SIBIUNSUNG = ['장생', '목욕', '관대', '건록', '제왕', '쇠', '병', '사', '묘', '절', '태', '양']
# 일간별 장생지 (지지 인덱스)
SIBIUNSUNG_START = {0: 11, 1: 6, 2: 2, 3: 9, 4: 2, 5: 9, 6: 5, 7: 0, 8: 8, 9: 3}


def get_sibiunsung(day_gan_idx: int, target_zhi_idx: int) -> str:
    start     = SIBIUNSUNG_START[day_gan_idx]
    direction = 1 if day_gan_idx % 2 == 0 else -1   # 양간=순, 음간=역
    offset    = (target_zhi_idx - start) * direction % 12
    return SIBIUNSUNG[offset]


# ── 신살 ────────────────────────────────────────────────────────────────────

# 천을귀인: 일간 → 귀인 지지 목록
CHEONEUL_MAP = {
    0: [1, 7], 1: [0, 8],
    2: [11, 9], 3: [11, 9],
    4: [1, 7], 5: [0, 8],
    6: [6, 2], 7: [6, 2],
    8: [3, 5], 9: [3, 5],
}
# 역마살: 년지/일지 → 역마 지지
YEOKMA_MAP = {8: 2, 0: 2, 4: 2, 2: 8, 6: 8, 10: 8, 11: 5, 3: 5, 7: 5, 5: 11, 9: 11, 1: 11}
# 도화살: 년지 → 도화 지지
DOHWA_MAP  = {8: 9, 0: 9, 4: 9, 2: 3, 6: 3, 10: 3, 11: 0, 3: 0, 7: 0, 5: 6, 9: 6, 1: 6}


def get_gongmang(gan_idx: int, zhi_idx: int) -> list:
    """일주의 공망 지지 2개 반환"""
    for i in range(60):
        if i % 10 == gan_idx and i % 12 == zhi_idx:
            group_start_zhi = (i - i % 10) % 12
            covered = {(group_start_zhi + k) % 12 for k in range(10)}
            return [z for z in range(12) if z not in covered]
    return []


# ── 절기 ────────────────────────────────────────────────────────────────────

# sxtwl getJieQi() 인덱스 순서: 0=冬至, 1=小寒, 2=大寒, 3=立春 …
JEOLGI_KR = {
     0: '동지(冬至)',  1: '소한(小寒)',  2: '대한(大寒)',  3: '입춘(立春)',
     4: '우수(雨水)',  5: '경칩(驚蟄)',  6: '춘분(春分)',  7: '청명(清明)',
     8: '곡우(穀雨)',  9: '입하(立夏)', 10: '소만(小滿)', 11: '망종(芒種)',
    12: '하지(夏至)', 13: '소서(小暑)', 14: '대서(大暑)', 15: '입추(立秋)',
    16: '처서(處暑)', 17: '백로(白露)', 18: '추분(秋分)', 19: '한로(寒露)',
    20: '상강(霜降)', 21: '입동(立冬)', 22: '소설(小雪)', 23: '대설(大雪)',
}

# 십신별 길흉 수치 (대운/세운 반영에 사용)
SIPSIN_LUCK = {
    "비견":  0.0, "겁재": -0.5, "식신":  0.5, "상관":  0.0,
    "정재":  0.5, "편재":  0.3, "정관":  0.5, "편관": -0.5,
    "정인":  0.3, "편인": -0.2,
}

# 십신별 한 줄 요약 (세운/월운 표시용)
SIPSIN_FORECAST = {
    "비견": "독립·자립의 기운",    "겁재": "경쟁·갈등 주의",
    "식신": "여유·표현 좋음",      "상관": "창의력↑, 말조심",
    "정재": "꾸준한 노력으로 결실", "편재": "활발한 외부 활동",
    "정관": "안정·책임감",         "편관": "압박·도전",
    "정인": "학습·내실 다지기",    "편인": "직관·전문성",
}


# ── 기본 함수 ────────────────────────────────────────────────────────────────

def get_sipsin(day_gan_idx: int, target_gan_idx: int = None,
               target_zhi_idx: int = None) -> str:
    if target_gan_idx is not None:
        target_elem = GAN_ELEMENT[target_gan_idx]
        target_yy   = GAN_YINYANG[target_gan_idx]
    else:
        target_elem = ZHI_ELEMENT[target_zhi_idx]
        target_yy   = ZHI_YINYANG[target_zhi_idx]

    day_elem = GAN_ELEMENT[day_gan_idx]
    day_yy   = GAN_YINYANG[day_gan_idx]
    same_yy  = (day_yy == target_yy)

    if target_elem == day_elem:
        return "비견" if same_yy else "겁재"
    elif (day_elem + 1) % 5 == target_elem:
        return "식신" if same_yy else "상관"
    elif (day_elem + 2) % 5 == target_elem:
        return "편재" if same_yy else "정재"
    elif (day_elem + 3) % 5 == target_elem:
        return "편관" if same_yy else "정관"
    else:
        return "편인" if same_yy else "정인"


def get_chunggap(zhi_idx_a: int, zhi_idx_b: int) -> str:
    if (zhi_idx_a + 6) % 12 == zhi_idx_b:
        return "충"
    six_he = {(0, 1), (2, 11), (3, 10), (4, 9), (5, 8), (6, 7)}
    pair = (min(zhi_idx_a, zhi_idx_b), max(zhi_idx_a, zhi_idx_b))
    if pair in six_he:
        return "육합"
    san_he = {
        frozenset([0, 4, 8]),
        frozenset([2, 6, 10]),
        frozenset([3, 7, 11]),
        frozenset([1, 5, 9]),
    }
    for sh in san_he:
        if zhi_idx_a in sh and zhi_idx_b in sh and zhi_idx_a != zhi_idx_b:
            return "반합"
    return ""


# ── SajuAnalyzer ────────────────────────────────────────────────────────────

class SajuAnalyzer:
    def __init__(self, birth: dict):
        self.birth = birth
        self._calc_natal_chart()
        self._calc_daewun()

    # ── 내부: 사주 계산 ──────────────────────────────────────────────────────

    def _calc_natal_chart(self):
        """본인 사주 4주 계산 + 오행 분포"""
        b = self.birth
        day_obj = sxtwl.fromSolar(b['year'], b['month'], b['day'])

        year_gz  = day_obj.getYearGZ()
        month_gz = day_obj.getMonthGZ()
        day_gz   = day_obj.getDayGZ()

        self.natal_year_gan  = year_gz.tg
        self.natal_year_zhi  = year_gz.dz
        self.natal_month_gan = month_gz.tg
        self.natal_month_zhi = month_gz.dz
        self.natal_day_gan   = day_gz.tg
        self.natal_day_zhi   = day_gz.dz

        # 시주
        hour_total = b['hour'] + b['minute'] / 60
        if hour_total >= 23.5 or hour_total < 1.5:
            shi_zhi = 0
        else:
            shi_zhi = int((hour_total - 1.5) // 2) + 1

        zi_start = {0: 0, 5: 0, 1: 2, 6: 2, 2: 4, 7: 4, 3: 6, 8: 6, 4: 8, 9: 8}
        shi_gan  = (zi_start[self.natal_day_gan] + shi_zhi) % 10

        self.natal_hour_gan = shi_gan
        self.natal_hour_zhi = shi_zhi

        all_gans = [self.natal_year_gan, self.natal_month_gan,
                    self.natal_day_gan, self.natal_hour_gan]
        all_zhis = [self.natal_year_zhi, self.natal_month_zhi,
                    self.natal_day_zhi, self.natal_hour_zhi]

        self.element_count   = [0, 0, 0, 0, 0]
        for g in all_gans:
            self.element_count[GAN_ELEMENT[g]] += 1
        for z in all_zhis:
            self.element_count[ZHI_ELEMENT[z]] += 1

        self.weak_elements   = [i for i, c in enumerate(self.element_count) if c == 0]
        self.strong_elements = [i for i, c in enumerate(self.element_count) if c >= 3]

        # 일주 공망 (고정값, 한 번만 계산)
        self.natal_gongmang = get_gongmang(self.natal_day_gan, self.natal_day_zhi)

        self._log_natal()

    def _log_natal(self):
        """사주 원국 로깅 (윤달/절기 경계 검증 포함)"""
        b = self.birth
        logger.info(
            "%s 원국: %s%s년 %s%s월 %s%s일 %s%s시",
            b.get('name', '사용자'),
            GAN[self.natal_year_gan],  ZHI[self.natal_year_zhi],
            GAN[self.natal_month_gan], ZHI[self.natal_month_zhi],
            GAN[self.natal_day_gan],   ZHI[self.natal_day_zhi],
            GAN[self.natal_hour_gan],  ZHI[self.natal_hour_zhi],
        )
        # 절기 경계일 근접 여부 확인 (±1일 이내면 월주가 달라질 수 있음)
        try:
            d = sxtwl.fromSolar(b['year'], b['month'], b['day'])
            prev_day = sxtwl.fromSolar(
                *( (datetime(b['year'], b['month'], b['day']) - timedelta(days=1)).timetuple()[:3] )
            )
            next_day = sxtwl.fromSolar(
                *( (datetime(b['year'], b['month'], b['day']) + timedelta(days=1)).timetuple()[:3] )
            )
            if d.hasJieQi() or prev_day.hasJieQi() or next_day.hasJieQi():
                logger.warning(
                    "%s 생일이 절기 경계 ±1일 이내 — 월주 확인 권장",
                    b.get('name', '사용자')
                )
        except Exception as e:
            logger.debug("절기 경계 검증 오류: %s", e)

    def _calc_daewun(self):
        """대운 방향·시작 나이·기둥 시퀀스 계산"""
        year_yy  = GAN_YINYANG[self.natal_year_gan]
        is_male  = self.birth.get('is_male', True)
        # 양남/음녀=순행, 음남/양녀=역행
        self.daewun_forward = (year_yy == 0) == is_male

        b        = self.birth
        birth_dt = datetime(b['year'], b['month'], b['day'])
        days_diff = None

        scan = range(1, 60)
        if not self.daewun_forward:
            for i in scan:
                check = birth_dt - timedelta(days=i)
                d = sxtwl.fromSolar(check.year, check.month, check.day)
                if d.hasJieQi():
                    days_diff = i
                    break
        else:
            for i in scan:
                check = birth_dt + timedelta(days=i)
                d = sxtwl.fromSolar(check.year, check.month, check.day)
                if d.hasJieQi():
                    days_diff = i
                    break

        self.daewun_start_age = round((days_diff or 15) / 3)

        # 60갑자 인덱스에서 월주 기준으로 순/역 10개 기둥 생성
        mg, mz = self.natal_month_gan, self.natal_month_zhi
        birth_cycle = next(
            (i for i in range(60) if i % 10 == mg and i % 12 == mz), 0
        )
        step = 1 if self.daewun_forward else -1
        self.daewun_sequence = [
            ((birth_cycle + n * step) % 60 % 10,
             (birth_cycle + n * step) % 60 % 12)
            for n in range(1, 11)
        ]

    def _get_current_daewun(self, analysis_year: int) -> tuple:
        """분석 연도 기준 현재 대운 (gan, zhi, start_age, end_age)"""
        age = analysis_year - self.birth['year']
        for i, (g, z) in enumerate(self.daewun_sequence):
            start = self.daewun_start_age + i * 10
            if start <= age < start + 10:
                return g, z, start, start + 10
        return None, None, self.daewun_start_age, self.daewun_start_age + 10

    def _get_jeolgi_info(self, year: int, month: int, day: int) -> dict:
        """현재·다음 절기 정보"""
        today = datetime(year, month, day)
        current_name = current_date = next_name = next_date = None

        try:
            for i in range(46):
                check = today - timedelta(days=i)
                d = sxtwl.fromSolar(check.year, check.month, check.day)
                if d.hasJieQi():
                    current_name = JEOLGI_KR.get(d.getJieQi(), f"절기{d.getJieQi()}")
                    current_date = check
                    break

            for i in range(1, 46):
                check = today + timedelta(days=i)
                d = sxtwl.fromSolar(check.year, check.month, check.day)
                if d.hasJieQi():
                    next_name = JEOLGI_KR.get(d.getJieQi(), f"절기{d.getJieQi()}")
                    next_date = check
                    break
        except Exception as e:
            logger.warning("절기 계산 오류: %s", e)

        return {
            "current":          current_name or "알 수 없음",
            "current_date":     current_date.strftime("%m/%d") if current_date else "",
            "next":             next_name or "알 수 없음",
            "next_date":        next_date.strftime("%m/%d") if next_date else "",
            "days_until_next":  (next_date - today).days if next_date else 0,
        }

    # ── 공개: 운세 분석 ──────────────────────────────────────────────────────

    def analyze_today(self) -> dict:
        today = datetime.now(_KST)
        return self.analyze_date(today.year, today.month, today.day)

    def analyze_date(self, year: int, month: int, day: int) -> dict:
        day_obj  = sxtwl.fromSolar(year, month, day)
        day_gz   = day_obj.getDayGZ()
        today_gan = day_gz.tg
        today_zhi = day_gz.dz

        # 십신
        gan_sipsin  = get_sipsin(self.natal_day_gan, target_gan_idx=today_gan)
        zhi_sipsin  = get_sipsin(self.natal_day_gan, target_zhi_idx=today_zhi)
        zhi_relation = get_chunggap(self.natal_day_zhi, today_zhi)

        today_gan_elem = GAN_ELEMENT[today_gan]
        today_zhi_elem = ZHI_ELEMENT[today_zhi]

        # 십이운성
        sibiunsung = get_sibiunsung(self.natal_day_gan, today_zhi)

        # 신살
        sinsal = []
        if today_zhi in CHEONEUL_MAP.get(self.natal_day_gan, []):
            sinsal.append("천을귀인(天乙貴人)")
        if YEOKMA_MAP.get(self.natal_year_zhi) == today_zhi:
            sinsal.append("역마살(驛馬殺)")
        if DOHWA_MAP.get(self.natal_year_zhi) == today_zhi:
            sinsal.append("도화살(桃花殺)")
        if today_zhi in self.natal_gongmang:
            sinsal.append("공망(空亡)")

        # 절기
        jeolgi = self._get_jeolgi_info(year, month, day)

        # 세운·월운
        sewun_gz   = day_obj.getYearGZ()
        wolwun_gz  = day_obj.getMonthGZ()
        sw_gan, sw_zhi = sewun_gz.tg, sewun_gz.dz
        ww_gan, ww_zhi = wolwun_gz.tg, wolwun_gz.dz

        sw_gan_ss = get_sipsin(self.natal_day_gan, target_gan_idx=sw_gan)
        sw_zhi_ss = get_sipsin(self.natal_day_gan, target_zhi_idx=sw_zhi)
        ww_gan_ss = get_sipsin(self.natal_day_gan, target_gan_idx=ww_gan)
        ww_zhi_ss = get_sipsin(self.natal_day_gan, target_zhi_idx=ww_zhi)

        # 대운
        dw_gan, dw_zhi, dw_start, dw_end = self._get_current_daewun(year)
        dw_gan_ss = get_sipsin(self.natal_day_gan, target_gan_idx=dw_gan) if dw_gan is not None else None
        dw_zhi_ss = get_sipsin(self.natal_day_gan, target_zhi_idx=dw_zhi) if dw_zhi is not None else None

        # 점수
        scores = self._calculate_scores(
            gan_sipsin, zhi_sipsin, zhi_relation,
            today_gan_elem, today_zhi_elem,
            dw_gan_ss, dw_zhi_ss,
            sw_gan_ss, sw_zhi_ss,
        )

        headline              = self._generate_headline(gan_sipsin, zhi_sipsin, zhi_relation,
                                                         today_gan_elem, today_zhi_elem)
        do_list, dont_list    = self._generate_advice(gan_sipsin, zhi_sipsin,
                                                       today_gan_elem, today_zhi_elem)
        lucky_hours           = self._calculate_lucky_hours(today_gan, today_zhi)
        overall               = round(sum(scores.values()) / len(scores), 1)

        logger.info(
            "분석 완료 %d-%02d-%02d: 일진=%s%s 총점=%.1f 신살=%s",
            year, month, day,
            GAN[today_gan], ZHI[today_zhi], overall,
            ",".join(sinsal) if sinsal else "없음",
        )

        return {
            # 일진
            "day_pillar":    f"{GAN[today_gan]}{ZHI[today_zhi]}",
            "day_pillar_kr": f"{GAN_KR[today_gan]}{ZHI_KR[today_zhi]}",
            "day_gan":       GAN[today_gan],
            "day_gan_kr":    GAN_KR[today_gan],
            "day_zhi":       ZHI[today_zhi],
            "day_zhi_kr":    ZHI_KR[today_zhi],
            "gan_sipsin":    gan_sipsin,
            "zhi_sipsin":    zhi_sipsin,
            "zhi_relation":  zhi_relation,
            # 십이운성·신살
            "sibiunsung":    sibiunsung,
            "sinsal":        sinsal,
            # 점수
            "scores":        scores,
            "overall_score": overall,
            # 텍스트
            "headline":      headline,
            "do_list":       do_list,
            "dont_list":     dont_list,
            "lucky_hours":   lucky_hours,
            # 절기
            "jeolgi":        jeolgi,
            # 세운
            "sewun": {
                "pillar":     f"{GAN[sw_gan]}{ZHI[sw_zhi]}",
                "pillar_kr":  f"{GAN_KR[sw_gan]}{ZHI_KR[sw_zhi]}",
                "gan_sipsin": sw_gan_ss,
                "zhi_sipsin": sw_zhi_ss,
            },
            # 월운
            "wolwun": {
                "pillar":     f"{GAN[ww_gan]}{ZHI[ww_zhi]}",
                "pillar_kr":  f"{GAN_KR[ww_gan]}{ZHI_KR[ww_zhi]}",
                "gan_sipsin": ww_gan_ss,
                "zhi_sipsin": ww_zhi_ss,
            },
            # 대운
            "daewun": {
                "pillar":     f"{GAN[dw_gan]}{ZHI[dw_zhi]}" if dw_gan is not None else "미진입",
                "pillar_kr":  f"{GAN_KR[dw_gan]}{ZHI_KR[dw_zhi]}" if dw_gan is not None else "미진입",
                "start_age":  dw_start,
                "end_age":    dw_end,
                "gan_sipsin": dw_gan_ss,
                "zhi_sipsin": dw_zhi_ss,
            },
        }

    # ── 내부: 점수/텍스트 ────────────────────────────────────────────────────

    def _sipsin_modifier(self, gan_ss: str, zhi_ss: str) -> float:
        g = SIPSIN_LUCK.get(gan_ss, 0)
        z = SIPSIN_LUCK.get(zhi_ss, 0)
        return g * 0.6 + z * 0.4

    def _calculate_scores(self, gan_sipsin, zhi_sipsin, zhi_relation,
                          gan_elem, zhi_elem,
                          dw_gan_ss=None, dw_zhi_ss=None,
                          sw_gan_ss=None, sw_zhi_ss=None) -> dict:
        sipsin_weights = {
            "비견": (3, 3, 2, 3, 2, 3),
            "겁재": (2, 2, 1, 2, 2, 3),
            "식신": (4, 4, 4, 4, 3, 4),
            "상관": (3, 4, 3, 3, 4, 3),
            "정재": (3, 3, 5, 3, 4, 3),
            "편재": (3, 3, 4, 3, 4, 3),
            "정관": (5, 4, 3, 4, 4, 3),
            "편관": (3, 3, 2, 2, 3, 2),
            "정인": (4, 5, 3, 3, 3, 4),
            "편인": (3, 4, 2, 3, 2, 3),
        }

        gan_w = sipsin_weights.get(gan_sipsin, (3, 3, 3, 3, 3, 3))
        zhi_w = sipsin_weights.get(zhi_sipsin, (3, 3, 3, 3, 3, 3))
        raw   = [gan_w[i] * 0.6 + zhi_w[i] * 0.4 for i in range(6)]

        # 오행 보정
        bonus = 0
        if gan_elem in self.weak_elements:
            bonus += 1.0
        if zhi_elem in self.weak_elements:
            bonus += 0.5
        if gan_elem in self.strong_elements:
            bonus -= 0.5

        # 충/합 보정
        if zhi_relation == "충":
            raw[5] = max(1, raw[5] - 1)
        elif zhi_relation in ("육합", "반합"):
            raw[3] = min(5, raw[3] + 1)

        raw = [s + bonus * (1 if i != 2 else 0.5) for i, s in enumerate(raw)]

        # 대운 반영 (±0.5 상한)
        if dw_gan_ss and dw_zhi_ss:
            dw_mod = max(-0.5, min(0.5, self._sipsin_modifier(dw_gan_ss, dw_zhi_ss) * 0.8))
            raw = [s + dw_mod for s in raw]

        # 세운 반영 (±0.3 상한)
        if sw_gan_ss and sw_zhi_ss:
            sw_mod = max(-0.3, min(0.3, self._sipsin_modifier(sw_gan_ss, sw_zhi_ss) * 0.5))
            raw = [s + sw_mod for s in raw]

        keys = ["work", "study", "money", "relationship", "love", "health"]
        return {k: min(5, max(1, round(raw[i]))) for i, k in enumerate(keys)}

    def _generate_headline(self, gan_sipsin, zhi_sipsin, zhi_relation,
                           gan_elem, zhi_elem) -> str:
        sipsin_phrase = {
            "비견": "독립적으로 움직이기 좋은 날",
            "겁재": "경쟁심이 강해지는 날, 충동 지출 주의",
            "식신": "여유와 표현력이 살아나는 날",
            "상관": "창의력 발휘에 좋은 날, 말조심",
            "정재": "꾸준한 노력이 결실로 이어지는 날",
            "편재": "활동량이 많고 기회가 보이는 날",
            "정관": "책임감을 발휘하기 좋은 날",
            "편관": "압박감이 있을 수 있는 날, 침착하게",
            "정인": "공부와 학습에 집중되는 날",
            "편인": "직관과 영감이 살아나는 날",
        }
        base   = sipsin_phrase.get(gan_sipsin, "평이한 흐름의 날")
        suffix = ""
        if gan_elem in self.weak_elements or zhi_elem in self.weak_elements:
            e      = gan_elem if gan_elem in self.weak_elements else zhi_elem
            suffix = f" 부족했던 {ELEMENT_KR[e]} 기운이 들어와 균형이 맞춰집니다."
        if zhi_relation == "충":
            suffix += " 변동·이동·갈등 가능성, 침착하게."
        return base + "." + suffix

    def _generate_advice(self, gan_sipsin, zhi_sipsin, gan_elem, zhi_elem):
        do_pool = {
            "비견": "혼자 집중하는 작업, 자기 페이스 유지",
            "겁재": "동료와 협력, 운동으로 에너지 발산",
            "식신": "취미 활동, 좋은 음식, 휴식",
            "상관": "창의적 작업, 글쓰기, 새로운 시도",
            "정재": "재정 관리, 꾸준한 일 처리",
            "편재": "외부 활동, 영업·미팅",
            "정관": "보고서 마무리, 공식 업무 처리",
            "편관": "어려운 도전 과제 정면 돌파",
            "정인": "공부, 독서, 자격증 준비",
            "편인": "전문 분야 깊이 파기, 명상",
        }
        dont_pool = {
            "비견": "독단적 결정 자제",
            "겁재": "충동 지출·도박성 결정 금지",
            "식신": "과식·과음 주의",
            "상관": "윗사람에게 말 함부로 하지 않기",
            "정재": "무리한 투자 자제",
            "편재": "큰 금액 대출·보증 금지",
            "정관": "규칙 위반·지각 주의",
            "편관": "갈등 상황에서 감정적 대응 자제",
            "정인": "결정 미루지 말기",
            "편인": "비주류 정보 과신 주의",
        }
        do_list   = f"• {do_pool.get(gan_sipsin, '평소대로')}\n• {do_pool.get(zhi_sipsin, '루틴 유지')}"
        extra_dont = ""
        if gan_elem in self.strong_elements:
            extra_dont = f"\n• {ELEMENT_KR[gan_elem]} 기운이 더 강해지니 고집 부리지 말 것"
        dont_list = f"• {dont_pool.get(gan_sipsin, '무리한 일정 자제')}\n• {dont_pool.get(zhi_sipsin, '늦은 시간 결정 자제')}{extra_dont}"
        if 4 in self.weak_elements:
            do_list += "\n• 물 자주 마시기, 산책으로 마음 식히기"
        return do_list, dont_list

    def _calculate_lucky_hours(self, today_gan: int, today_zhi: int) -> str:
        good_times = []
        for time_range, zhi_idx, name in HOUR_RANGES:
            if ZHI_ELEMENT[zhi_idx] in self.weak_elements:
                good_times.append(
                    f"**{time_range} {name}** — {ELEMENT_KR[ZHI_ELEMENT[zhi_idx]]} 보충"
                )
                if len(good_times) >= 3:
                    break
        if len(good_times) < 2:
            for time_range, zhi_idx, name in HOUR_RANGES:
                sipsin = get_sipsin(self.natal_day_gan, target_zhi_idx=zhi_idx)
                if sipsin in ("정인", "정관") and time_range not in str(good_times):
                    good_times.append(f"{time_range} {name} — {sipsin}")
                    if len(good_times) >= 3:
                        break
        return "\n".join(good_times[:3]) if good_times else "특별한 길시간 없음"
