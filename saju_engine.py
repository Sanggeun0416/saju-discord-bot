"""
사주 분석 엔진
- 본인 사주와 오늘 일진의 관계를 십신/오행 기반으로 분석
- 영역별 점수 및 길흉 판단
"""

import sxtwl
from datetime import datetime


# 천간/지지 한자 및 한글
GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
GAN_KR = ['갑', '을', '병', '정', '무', '기', '경', '신', '임', '계']
ZHI_KR = ['자', '축', '인', '묘', '진', '사', '오', '미', '신', '유', '술', '해']

# 천간 오행 (목=0, 화=1, 토=2, 금=3, 수=4)
GAN_ELEMENT = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]
# 천간 음양 (양=0, 음=1)
GAN_YINYANG = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]

# 지지 오행
ZHI_ELEMENT = [4, 2, 0, 0, 2, 1, 1, 2, 3, 3, 2, 4]
# 지지 음양
ZHI_YINYANG = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1]

ELEMENT_KR = ['목(木)', '화(火)', '토(土)', '금(金)', '수(水)']

# 시간대(시진) - 십이지시
HOUR_RANGES = [
    ("23:30~01:30", 0, "자시(子時)"),
    ("01:30~03:30", 1, "축시(丑時)"),
    ("03:30~05:30", 2, "인시(寅時)"),
    ("05:30~07:30", 3, "묘시(卯時)"),
    ("07:30~09:30", 4, "진시(辰時)"),
    ("09:30~11:30", 5, "사시(巳時)"),
    ("11:30~13:30", 6, "오시(午時)"),
    ("13:30~15:30", 7, "미시(未時)"),
    ("15:30~17:30", 8, "신시(申時)"),
    ("17:30~19:30", 9, "유시(酉時)"),
    ("19:30~21:30", 10, "술시(戌時)"),
    ("21:30~23:30", 11, "해시(亥時)"),
]


def get_sipsin(day_gan_idx: int, target_gan_idx: int = None,
               target_zhi_idx: int = None) -> str:
    """
    일간 기준으로 대상 천간 또는 지지의 십신을 계산
    """
    if target_gan_idx is not None:
        target_elem = GAN_ELEMENT[target_gan_idx]
        target_yy = GAN_YINYANG[target_gan_idx]
    else:
        target_elem = ZHI_ELEMENT[target_zhi_idx]
        target_yy = ZHI_YINYANG[target_zhi_idx]

    day_elem = GAN_ELEMENT[day_gan_idx]
    day_yy = GAN_YINYANG[day_gan_idx]

    # 음양 동일 여부
    same_yy = (day_yy == target_yy)

    # 오행 관계
    # 비겁: 같은 오행 / 식상: 내가 생함 / 재성: 내가 극함
    # 관성: 나를 극함 / 인성: 나를 생함
    if target_elem == day_elem:
        return "비견" if same_yy else "겁재"
    elif (day_elem + 1) % 5 == target_elem:  # 내가 생하는 것 (목→화)
        return "식신" if same_yy else "상관"
    elif (day_elem + 2) % 5 == target_elem:  # 내가 극하는 것 (목→토)
        return "편재" if same_yy else "정재"
    elif (day_elem + 3) % 5 == target_elem:  # 나를 극하는 것 (목←금)
        return "편관" if same_yy else "정관"
    else:  # (day_elem + 4) % 5 == target_elem: 나를 생하는 것 (목←수)
        return "편인" if same_yy else "정인"


def get_chunggap(zhi_idx_a: int, zhi_idx_b: int) -> str:
    """지지 충/합 관계 판단"""
    # 육충 (서로 정반대)
    if (zhi_idx_a + 6) % 12 == zhi_idx_b:
        return "충"
    # 육합
    six_he = {(0, 1), (2, 11), (3, 10), (4, 9), (5, 8), (6, 7)}
    pair = (min(zhi_idx_a, zhi_idx_b), max(zhi_idx_a, zhi_idx_b))
    if pair in six_he:
        return "육합"
    # 삼합 일부
    san_he = {
        frozenset([0, 4, 8]),   # 신자진 - 수
        frozenset([2, 6, 10]),  # 인오술 - 화
        frozenset([3, 7, 11]),  # 해묘미 - 목
        frozenset([1, 5, 9]),   # 사유축 - 금
    }
    for sh in san_he:
        if zhi_idx_a in sh and zhi_idx_b in sh and zhi_idx_a != zhi_idx_b:
            return "반합"
    return ""


class SajuAnalyzer:
    def __init__(self, birth: dict):
        """
        birth: {
            'year': 2005, 'month': 4, 'day': 16,
            'hour': 2, 'minute': 39,
            'is_male': True
        }
        """
        self.birth = birth
        self._calc_natal_chart()

    def _calc_natal_chart(self):
        """본인 사주 4주 계산"""
        b = self.birth
        day_obj = sxtwl.fromSolar(b['year'], b['month'], b['day'])

        year_gz = day_obj.getYearGZ()
        month_gz = day_obj.getMonthGZ()
        day_gz = day_obj.getDayGZ()

        self.natal_year_gan = year_gz.tg
        self.natal_year_zhi = year_gz.dz
        self.natal_month_gan = month_gz.tg
        self.natal_month_zhi = month_gz.dz
        self.natal_day_gan = day_gz.tg   # 일간 = 본인
        self.natal_day_zhi = day_gz.dz

        # 시주 계산
        hour_total = b['hour'] + b['minute'] / 60
        # 23:30~01:30 → 자시 등
        if hour_total >= 23.5 or hour_total < 1.5:
            shi_zhi = 0
        else:
            # 1.5 → 축시(1), 3.5 → 인시(2) ...
            shi_zhi = int((hour_total - 1.5) // 2) + 1

        zi_start = {0: 0, 5: 0, 1: 2, 6: 2, 2: 4, 7: 4, 3: 6, 8: 6, 4: 8, 9: 8}
        shi_gan = (zi_start[self.natal_day_gan] + shi_zhi) % 10

        self.natal_hour_gan = shi_gan
        self.natal_hour_zhi = shi_zhi

        # 본인 오행 분포
        all_gans = [self.natal_year_gan, self.natal_month_gan,
                    self.natal_day_gan, self.natal_hour_gan]
        all_zhis = [self.natal_year_zhi, self.natal_month_zhi,
                    self.natal_day_zhi, self.natal_hour_zhi]

        self.element_count = [0, 0, 0, 0, 0]  # 목화토금수
        for g in all_gans:
            self.element_count[GAN_ELEMENT[g]] += 1
        for z in all_zhis:
            self.element_count[ZHI_ELEMENT[z]] += 1

        # 부족한 오행 / 강한 오행
        self.weak_elements = [i for i, c in enumerate(self.element_count) if c == 0]
        self.strong_elements = [i for i, c in enumerate(self.element_count) if c >= 3]

    def analyze_today(self) -> dict:
        """오늘 일진을 분석"""
        today = datetime.now()
        return self.analyze_date(today.year, today.month, today.day)

    def analyze_date(self, year: int, month: int, day: int) -> dict:
        """특정 날짜의 운세 분석"""
        day_obj = sxtwl.fromSolar(year, month, day)
        day_gz = day_obj.getDayGZ()

        today_gan = day_gz.tg
        today_zhi = day_gz.dz

        # 오늘 천간/지지의 십신 (본인 일간 기준)
        gan_sipsin = get_sipsin(self.natal_day_gan, target_gan_idx=today_gan)
        zhi_sipsin = get_sipsin(self.natal_day_gan, target_zhi_idx=today_zhi)

        # 본인 일지와 오늘 지지의 충/합
        zhi_relation = get_chunggap(self.natal_day_zhi, today_zhi)

        # 오늘 들어오는 오행
        today_gan_elem = GAN_ELEMENT[today_gan]
        today_zhi_elem = ZHI_ELEMENT[today_zhi]

        # 영역별 점수 계산
        scores = self._calculate_scores(
            gan_sipsin, zhi_sipsin, zhi_relation,
            today_gan_elem, today_zhi_elem
        )

        # 헤드라인 생성
        headline = self._generate_headline(gan_sipsin, zhi_sipsin, zhi_relation,
                                           today_gan_elem, today_zhi_elem)

        # 추천/주의 행동
        do_list, dont_list = self._generate_advice(
            gan_sipsin, zhi_sipsin, today_gan_elem, today_zhi_elem
        )

        # 길한 시간대
        lucky_hours = self._calculate_lucky_hours(today_gan, today_zhi)

        # 총평 (영역 평균)
        overall = round(sum(scores.values()) / len(scores), 1)

        return {
            "day_pillar": f"{GAN[today_gan]}{ZHI[today_zhi]}",
            "day_pillar_kr": f"{GAN_KR[today_gan]}{ZHI_KR[today_zhi]}",
            "day_gan": GAN[today_gan],
            "day_gan_kr": GAN_KR[today_gan],
            "day_zhi": ZHI[today_zhi],
            "day_zhi_kr": ZHI_KR[today_zhi],
            "gan_sipsin": gan_sipsin,
            "zhi_sipsin": zhi_sipsin,
            "zhi_relation": zhi_relation,
            "scores": scores,
            "overall_score": overall,
            "headline": headline,
            "do_list": do_list,
            "dont_list": dont_list,
            "lucky_hours": lucky_hours,
        }

    def _calculate_scores(self, gan_sipsin, zhi_sipsin, zhi_relation,
                          gan_elem, zhi_elem) -> dict:
        """6개 영역별 점수 (1~5)"""

        # 십신별 영역 가중치 (업무, 학습, 재물, 인간관계, 연애, 건강)
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

        # 천간이 60%, 지지가 40% 가중치
        scores_raw = [round(gan_w[i] * 0.6 + zhi_w[i] * 0.4) for i in range(6)]

        # 보정: 부족한 오행 들어오면 +1, 강한 오행이 더 들어오면 -0.5
        bonus = 0
        if gan_elem in self.weak_elements:
            bonus += 1
        if zhi_elem in self.weak_elements:
            bonus += 0.5
        if gan_elem in self.strong_elements:
            bonus -= 0.5

        # 충은 변화/스트레스, 합은 안정 (단, 일지 충은 컨디션·이동에 영향)
        if zhi_relation == "충":
            scores_raw[5] = max(1, scores_raw[5] - 1)  # 건강
            # 변화는 양면성 - 업무는 약간 + 또는 -
        elif zhi_relation in ("육합", "반합"):
            scores_raw[3] = min(5, scores_raw[3] + 1)  # 인간관계

        # 보너스 적용 (영역별 적용 강도 다르게)
        scores_raw = [
            min(5, max(1, round(s + bonus * (1 if i not in [2] else 0.5))))
            for i, s in enumerate(scores_raw)
        ]

        return {
            "work": scores_raw[0],
            "study": scores_raw[1],
            "money": scores_raw[2],
            "relationship": scores_raw[3],
            "love": scores_raw[4],
            "health": scores_raw[5],
        }

    def _generate_headline(self, gan_sipsin, zhi_sipsin, zhi_relation,
                           gan_elem, zhi_elem) -> str:
        """오늘 한 줄 요약 생성"""

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

        base = sipsin_phrase.get(gan_sipsin, "평이한 흐름의 날")

        # 부족한 오행 보충 여부
        suffix = ""
        if gan_elem in self.weak_elements or zhi_elem in self.weak_elements:
            elem_kr = ELEMENT_KR[gan_elem if gan_elem in self.weak_elements else zhi_elem]
            suffix = f" 부족했던 {elem_kr} 기운이 들어와 균형이 맞춰집니다."

        # 충 경고
        if zhi_relation == "충":
            suffix += " 변동·이동·갈등 가능성이 있으니 침착하게."

        return base + "." + suffix

    def _generate_advice(self, gan_sipsin, zhi_sipsin, gan_elem, zhi_elem):
        """추천 행동 / 주의 사항"""

        do_pool = {
            "비견": "혼자 집중하는 작업, 자기 페이스 유지",
            "겁재": "동료와 협력, 운동으로 에너지 발산",
            "식신": "취미 활동, 좋은 음식, 휴식",
            "상관": "창의적 작업, 글쓰기, 새로운 시도",
            "정재": "재정 관리, 꾸준한 일 처리",
            "편재": "외부 활동, 영업·미팅",
            "정관": "보고서 마무리, 공식적인 업무 처리",
            "편관": "어려운 도전 과제 정면 돌파",
            "정인": "공부, 독서, 자격증 준비",
            "편인": "전문 분야 깊이 파기, 명상",
        }

        dont_pool = {
            "비견": "독단적 결정 자제",
            "겁재": "충동 지출, 도박성 결정 금지",
            "식신": "과식·과음 주의",
            "상관": "윗사람에게 말 함부로 하지 않기",
            "정재": "무리한 투자 자제",
            "편재": "큰 금액 대출·보증 금지",
            "정관": "규칙 위반·지각 주의",
            "편관": "갈등 상황에서 감정적 대응 자제",
            "정인": "결정 미루지 말기",
            "편인": "음모론·비주류 정보 과신 주의",
        }

        do_list = f"• {do_pool.get(gan_sipsin, '평소대로')}\n• {do_pool.get(zhi_sipsin, '루틴 유지')}"

        # 강한 오행 추가 경고
        extra_dont = ""
        if gan_elem in self.strong_elements:
            elem_kr = ELEMENT_KR[gan_elem]
            extra_dont = f"\n• {elem_kr} 기운이 더 강해지니 고집 부리지 말 것"

        dont_list = f"• {dont_pool.get(gan_sipsin, '무리한 일정 자제')}\n• {dont_pool.get(zhi_sipsin, '늦은 시간 결정 자제')}{extra_dont}"

        # 부족한 오행 보충 팁
        if 4 in self.weak_elements:  # 수 부족 (일간 이상근님 케이스)
            do_list += "\n• 물 자주 마시기, 산책으로 마음 식히기"

        return do_list, dont_list

    def _calculate_lucky_hours(self, today_gan: int, today_zhi: int) -> str:
        """오늘 시간대 중 길한 시간 추천 (간략)"""

        # 본인 일간과 오행 상생인 시간 + 부족한 오행이 들어오는 시간을 길로 봄
        day_elem = GAN_ELEMENT[self.natal_day_gan]

        good_times = []
        for time_range, zhi_idx, name in HOUR_RANGES:
            zhi_elem = ZHI_ELEMENT[zhi_idx]

            # 부족한 오행 시간 우선
            if zhi_elem in self.weak_elements:
                good_times.append(f"**{time_range} {name}** — {ELEMENT_KR[zhi_elem]} 보충")
                if len(good_times) >= 3:
                    break

        # 부족 오행 시간이 부족하면 인성/관성 시간 추가
        if len(good_times) < 2:
            for time_range, zhi_idx, name in HOUR_RANGES:
                sipsin = get_sipsin(self.natal_day_gan, target_zhi_idx=zhi_idx)
                if sipsin in ("정인", "정관") and time_range not in str(good_times):
                    good_times.append(f"{time_range} {name} — {sipsin}")
                    if len(good_times) >= 3:
                        break

        return "\n".join(good_times[:3]) if good_times else "특별한 길시간 없음"
