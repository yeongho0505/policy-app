import hashlib
import re
import sqlite3
from io import BytesIO
from urllib.parse import urlparse

import pandas as pd
import streamlit as st


# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(
    page_title="정책자금 맞춤 조회",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = "policy_funds.db"

# 반드시 실제 네이버폼 또는 상담 페이지 주소로 변경하세요.
CONSULT_URL = "https://naver.me/네이버폼주소"

conn = sqlite3.connect(
    DB_PATH,
    check_same_thread=False,
)


# =========================================================
# 공식 기관 링크
# 기관명이 조금 다르게 저장돼 있어도 찾을 수 있도록 키워드 방식 사용
# =========================================================
OFFICIAL_LINKS = {
    "소상공인시장진흥공단": "https://ols.semas.or.kr",
    "소진공": "https://ols.semas.or.kr",

    "중소벤처기업진흥공단": "https://www.kosmes.or.kr",
    "중진공": "https://www.kosmes.or.kr",

    "기업마당": "https://www.bizinfo.go.kr",

    "중소벤처기업부": "https://www.mss.go.kr",
    "중기부": "https://www.mss.go.kr",

    "신용보증기금": "https://www.kodit.co.kr",
    "신보": "https://www.kodit.co.kr",

    "기술보증기금": "https://www.kibo.or.kr",
    "기보": "https://www.kibo.or.kr",

    "신용보증재단중앙회": "https://www.koreg.or.kr",
    "지역신용보증재단": "https://www.koreg.or.kr",
    "신용보증재단": "https://www.koreg.or.kr",
    "지역재단": "https://www.koreg.or.kr",

    "한국산업은행": "https://www.kdb.co.kr",
    "산업은행": "https://www.kdb.co.kr",

    "IBK기업은행": "https://www.ibk.co.kr",
    "기업은행": "https://www.ibk.co.kr",

    "NH농협은행": "https://banking.nonghyup.com",
    "농협은행": "https://banking.nonghyup.com",

    "한국수출입은행": "https://www.koreaexim.go.kr",
    "수출입은행": "https://www.koreaexim.go.kr",

    "소상공인24": "https://www.sbiz24.kr",
    "정부24": "https://www.gov.kr",
}


# 공식 링크로 인정할 도메인
ALLOWED_DOMAINS = {
    "ols.semas.or.kr",
    "semas.or.kr",
    "www.semas.or.kr",
    "kosmes.or.kr",
    "www.kosmes.or.kr",
    "bizinfo.go.kr",
    "www.bizinfo.go.kr",
    "mss.go.kr",
    "www.mss.go.kr",
    "kodit.co.kr",
    "www.kodit.co.kr",
    "kibo.or.kr",
    "www.kibo.or.kr",
    "koreg.or.kr",
    "www.koreg.or.kr",
    "kdb.co.kr",
    "www.kdb.co.kr",
    "ibk.co.kr",
    "www.ibk.co.kr",
    "banking.nonghyup.com",
    "koreaexim.go.kr",
    "www.koreaexim.go.kr",
    "sbiz24.kr",
    "www.sbiz24.kr",
    "gov.kr",
    "www.gov.kr",
}


# =========================================================
# CSS 디자인
# =========================================================
st.markdown(
    """
    <style>
    .block-container {
        max-width: 1250px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .main-title {
        font-size: 2.1rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }

    .main-description {
        color: #555;
        margin-bottom: 1.8rem;
    }

    .policy-card {
        border: 1px solid #e3e6eb;
        border-radius: 16px;
        padding: 22px;
        margin: 14px 0;
        background: #ffffff;
        box-shadow: 0 3px 12px rgba(0, 0, 0, 0.05);
    }

    .policy-title {
        font-size: 1.3rem;
        font-weight: 800;
        margin-bottom: 6px;
    }

    .policy-agency {
        color: #555;
        font-size: 0.95rem;
        margin-bottom: 16px;
    }

    .info-label {
        color: #6b7280;
        font-size: 0.85rem;
        margin-bottom: 2px;
    }

    .info-value {
        font-size: 1rem;
        font-weight: 650;
        margin-bottom: 12px;
    }

    .money-value {
        font-size: 1.3rem;
        font-weight: 800;
        color: #1d4ed8;
        margin-bottom: 12px;
    }

    .rate-value {
        font-size: 1.3rem;
        font-weight: 800;
        color: #b45309;
        margin-bottom: 12px;
    }

    .recommendation {
        display: inline-block;
        border-radius: 20px;
        padding: 6px 12px;
        background: #eef4ff;
        font-weight: 750;
        margin-bottom: 12px;
    }

    .description-box {
        background: #f8fafc;
        border-radius: 10px;
        padding: 14px;
        line-height: 1.65;
        margin-top: 10px;
        margin-bottom: 12px;
    }

    .notice-box {
        background: #fff8e6;
        border: 1px solid #f4d27a;
        border-radius: 10px;
        padding: 14px;
        margin-bottom: 18px;
    }

    div[data-testid="stLinkButton"] a {
        background-color: #1565c0;
        color: white;
        border: none;
        font-weight: 700;
    }

    div[data-testid="stLinkButton"] a:hover {
        background-color: #0d47a1;
        color: white;
    }

    @media (max-width: 768px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .main-title {
            font-size: 1.65rem;
        }

        .policy-card {
            padding: 16px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 공통 함수
# =========================================================
def clean_text(value) -> str:
    """None, NaN 등을 안전한 문자열로 변환합니다."""
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    return str(value).strip()


def clean_number(value, default=0):
    """숫자 필드의 오류를 방지합니다."""
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def format_money(value) -> str:
    amount = int(clean_number(value, 0))

    if amount <= 0:
        return "공고 확인 필요"

    return f"최대 {amount:,}원"


def format_rate(value) -> str:
    rate = clean_number(value, 0)

    if rate <= 0:
        return "공고 확인 필요"

    return f"{rate:.2f}%"


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_admin_password() -> str:
    """
    Streamlit Secrets에 ADMIN_PASSWORD가 있으면 우선 사용합니다.
    없는 경우 임시 기본 비밀번호를 사용합니다.
    """
    try:
        return st.secrets["ADMIN_PASSWORD"]
    except (KeyError, FileNotFoundError):
        return "#n10090425"


def check_admin_password(input_password: str) -> bool:
    admin_password = get_admin_password()

    return hash_password(input_password) == hash_password(admin_password)


def normalize_phone(phone: str) -> str:
    return re.sub(r"[^0-9]", "", clean_text(phone))


def is_valid_phone(phone: str) -> bool:
    normalized = normalize_phone(phone)
    return normalized.isdigit() and 10 <= len(normalized) <= 11


def is_valid_http_url(url: str) -> bool:
    url = clean_text(url)

    if not url:
        return False

    try:
        parsed = urlparse(url)

        return (
            parsed.scheme in {"http", "https"}
            and bool(parsed.netloc)
        )
    except ValueError:
        return False


def is_official_url(url: str) -> bool:
    """
    DB에 저장된 링크가 허용된 공식 기관 도메인인지 확인합니다.
    """
    if not is_valid_http_url(url):
        return False

    parsed = urlparse(url)
    domain = parsed.netloc.lower().split(":")[0]

    return any(
        domain == allowed_domain
        or domain.endswith(f".{allowed_domain}")
        for allowed_domain in ALLOWED_DOMAINS
    )


def find_official_link(agency: str, saved_link: str = ""):
    """
    1순위: DB에 저장된 공식 공고 또는 신청 URL
    2순위: 기관명에 맞는 공식 기관 홈페이지
    3순위: 링크 없음
    """
    saved_link = clean_text(saved_link)

    if is_official_url(saved_link):
        return saved_link, "공식 공고·신청 페이지"

    agency = clean_text(agency).replace(" ", "")

    for agency_keyword, official_link in OFFICIAL_LINKS.items():
        normalized_keyword = agency_keyword.replace(" ", "")

        if normalized_keyword in agency:
            return official_link, "공식 기관 페이지"

    return None, None


def calculate_recommendation(row) -> tuple[str, int]:
    """
    저장된 정책 정보의 충실도를 기준으로 추천도를 계산합니다.

    실제 승인 가능성을 보장하는 점수가 아니며,
    검색 결과의 정보 완성도와 접근성을 표시합니다.
    """
    score = 2

    if clean_number(row.get("최대금액"), 0) > 0:
        score += 1

    if clean_text(row.get("조건")):
        score += 1

    official_link, _ = find_official_link(
        row.get("기관"),
        row.get("링크"),
    )

    if official_link:
        score += 1

    score = min(score, 5)

    labels = {
        5: "★★★★★ 매우 추천",
        4: "★★★★☆ 추천",
        3: "★★★☆☆ 보통",
        2: "★★☆☆☆ 확인 필요",
        1: "★☆☆☆☆ 정보 부족",
    }

    return labels[score], score


def get_description(row) -> str:
    """
    DB의 조건·대상·업종 정보를 활용해 설명을 작성합니다.
    새로운 자격요건을 임의로 만들지 않습니다.
    """
    condition = clean_text(row.get("조건"))

    if condition:
        return condition

    target = clean_text(row.get("대상")) or "사업자"
    industry = clean_text(row.get("업종")) or "해당 업종"
    support_type = clean_text(row.get("지원형태")) or "정책지원"

    return (
        f"{target}을 대상으로 하는 {support_type} 정책입니다. "
        f"{industry} 해당 여부와 세부 자격요건은 공식 공고에서 확인해야 합니다."
    )


def is_dummy_policy_name(name: str) -> bool:
    """
    정책자금_97과 같은 기존 샘플 명칭을 판별합니다.
    """
    name = clean_text(name)

    return bool(re.fullmatch(r"정책자금_\d+", name))


# =========================================================
# DB 생성 및 마이그레이션
# =========================================================
def get_table_columns(table_name: str) -> list[str]:
    safe_tables = {
        "policy_funds",
        "consult_requests",
    }

    if table_name not in safe_tables:
        raise ValueError("허용되지 않은 테이블입니다.")

    table_info = pd.read_sql(
        f"PRAGMA table_info({table_name})",
        conn,
    )

    if "name" not in table_info.columns:
        return []

    return table_info["name"].tolist()


def add_missing_columns(
    table_name: str,
    required_columns: dict[str, str],
) -> None:
    existing_columns = get_table_columns(table_name)

    for column, column_type in required_columns.items():
        if column not in existing_columns:
            conn.execute(
                f'ALTER TABLE {table_name} '
                f'ADD COLUMN "{column}" {column_type}'
            )

    conn.commit()


def create_tables() -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS policy_funds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            기관 TEXT,
            대상 TEXT,
            업종 TEXT,
            지역 TEXT,
            최대금액 INTEGER,
            금리 REAL,
            지원형태 TEXT,
            조건 TEXT,
            신청기간 TEXT,
            링크 TEXT
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS consult_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            business TEXT NOT NULL,
            region TEXT,
            industry TEXT,
            amount INTEGER,
            message TEXT,
            selected_policy TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()

    add_missing_columns(
        "policy_funds",
        {
            "기관": "TEXT",
            "대상": "TEXT",
            "업종": "TEXT",
            "지역": "TEXT",
            "최대금액": "INTEGER",
            "금리": "REAL",
            "지원형태": "TEXT",
            "조건": "TEXT",
            "신청기간": "TEXT",
            "링크": "TEXT",
        },
    )

    add_missing_columns(
        "consult_requests",
        {
            "business": "TEXT",
            "region": "TEXT",
            "industry": "TEXT",
            "amount": "INTEGER",
            "message": "TEXT",
            "selected_policy": "TEXT",
            "created_at": "TIMESTAMP",
        },
    )


create_tables()


# =========================================================
# 정책 검색
# =========================================================
def search_data(
    region: str,
    target: str,
    industry: str,
    min_money: int,
) -> pd.DataFrame:
    query = """
        SELECT *
        FROM policy_funds
        WHERE COALESCE(최대금액, 0) >= ?
    """

    params = [int(min_money)]

    if region != "전체":
        query += " AND COALESCE(지역, '') LIKE ?"
        params.append(f"%{region}%")

    if target != "전체":
        query += " AND COALESCE(대상, '') LIKE ?"
        params.append(f"%{target}%")

    if industry != "전체":
        query += " AND COALESCE(업종, '') LIKE ?"
        params.append(f"%{industry}%")

    query += " ORDER BY id DESC"

    return pd.read_sql(
        query,
        conn,
        params=params,
    )


def get_policy_options(column_name: str, defaults: list[str]) -> list[str]:
    allowed_columns = {
        "지역",
        "대상",
        "업종",
    }

    if column_name not in allowed_columns:
        return ["전체"] + defaults

    try:
        result = pd.read_sql(
            f"""
            SELECT DISTINCT "{column_name}" AS value
            FROM policy_funds
            WHERE "{column_name}" IS NOT NULL
              AND TRIM("{column_name}") != ''
            ORDER BY "{column_name}"
            """,
            conn,
        )

        values = [
            clean_text(value)
            for value in result["value"].tolist()
            if clean_text(value)
        ]

        combined = list(dict.fromkeys(defaults + values))

        return ["전체"] + combined

    except Exception:
        return ["전체"] + defaults


# =========================================================
# 정책 카드
# =========================================================
def render_policy_card(row) -> None:
    policy_name = clean_text(row.get("name")) or "정책명 확인 필요"
    agency = clean_text(row.get("기관")) or "기관 확인 필요"
    target = clean_text(row.get("대상")) or "공고 확인 필요"
    industry = clean_text(row.get("업종")) or "공고 확인 필요"
    region = clean_text(row.get("지역")) or "전국 또는 공고 확인"
    support_type = clean_text(row.get("지원형태")) or "공고 확인 필요"
    application_period = clean_text(row.get("신청기간")) or "공고 확인 필요"

    recommendation, _ = calculate_recommendation(row)
    description = get_description(row)

    official_link, link_label = find_official_link(
        agency,
        row.get("링크"),
    )

    st.markdown('<div class="policy-card">', unsafe_allow_html=True)

    title_col, rating_col = st.columns([3, 1])

    with title_col:
        st.markdown(
            f'<div class="policy-title">📌 {policy_name}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="policy-agency">🏢 지원기관: {agency}</div>',
            unsafe_allow_html=True,
        )

    with rating_col:
        st.markdown(
            f'<div class="recommendation">{recommendation}</div>',
            unsafe_allow_html=True,
        )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="info-label">👤 지원 대상</div>
            <div class="info-value">{target}</div>

            <div class="info-label">🏭 대상 업종</div>
            <div class="info-value">{industry}</div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="info-label">📍 지원 지역</div>
            <div class="info-value">{region}</div>

            <div class="info-label">📋 지원 형태</div>
            <div class="info-value">{support_type}</div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="info-label">💰 최대 지원한도</div>
            <div class="money-value">{format_money(row.get("최대금액"))}</div>

            <div class="info-label">📅 신청기간</div>
            <div class="info-value">{application_period}</div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
            <div class="info-label">📉 안내 금리</div>
            <div class="rate-value">{format_rate(row.get("금리"))}</div>

            <div class="info-label">🔎 심사 여부</div>
            <div class="info-value">기관 심사 후 결정</div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div class="description-box">
            <strong>정책 설명</strong><br>
            {description}
        </div>
        """,
        unsafe_allow_html=True,
    )

    button_col1, button_col2, empty_col = st.columns([1, 1, 2])

    with button_col1:
        if official_link:
            st.link_button(
                f"👉 {link_label}",
                official_link,
                use_container_width=True,
            )
        else:
            if "네이버폼주소" not in CONSULT_URL:
                st.link_button(
                    "📞 상담 신청",
                    CONSULT_URL,
                    use_container_width=True,
                )
            else:
                st.info("공식 링크 확인 필요")

    with button_col2:
        if "네이버폼주소" not in CONSULT_URL:
            st.link_button(
                "☎️ 무료 사전진단 신청",
                CONSULT_URL,
                use_container_width=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# 메인 화면
# =========================================================
st.markdown(
    '<div class="main-title">📊 정책자금 맞춤 조회</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="main-description">
        지역, 지원 대상, 업종 및 필요 자금을 선택하면 등록된 정책 중
        조건에 가까운 정책을 확인할 수 있습니다.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="notice-box">
        <strong>안내사항</strong><br>
        화면의 금액과 금리는 승인 확정값이 아닙니다.
        실제 지원 여부, 한도, 금리 및 접수 가능 여부는 공식 공고와
        기관 심사를 통해 최종 결정됩니다.
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 검색 조건
# =========================================================
st.sidebar.header("🔍 검색 조건")

region_options = get_policy_options(
    "지역",
    [
        "서울", "경기", "인천", "부산", "대구", "광주", "대전",
        "울산", "세종", "강원", "충북", "충남", "전북", "전남",
        "경북", "경남", "제주", "전국",
    ],
)

target_options = get_policy_options(
    "대상",
    [
        "소상공인",
        "중소기업",
        "창업기업",
        "청년",
        "재도전기업",
    ],
)

industry_options = get_policy_options(
    "업종",
    [
        "제조",
        "서비스",
        "도소매",
        "음식점",
        "건설",
        "운수",
        "정보통신",
        "숙박",
    ],
)

region = st.sidebar.selectbox(
    "지역",
    region_options,
)

target = st.sidebar.selectbox(
    "지원 대상",
    target_options,
)

industry = st.sidebar.selectbox(
    "업종",
    industry_options,
)

min_money = st.sidebar.number_input(
    "필요 자금",
    min_value=0,
    max_value=10_000_000_000,
    value=0,
    step=10_000_000,
    format="%d",
)

sort_option = st.sidebar.selectbox(
    "정렬 기준",
    [
        "기본순",
        "금리 낮은순",
        "지원한도 높은순",
        "정책명순",
    ],
)

exclude_dummy = st.sidebar.checkbox(
    "샘플 정책명 제외",
    value=True,
    help="정책자금_97과 같은 샘플 정책을 검색 결과에서 제외합니다.",
)

search_btn = st.sidebar.button(
    "🔎 정책 검색",
    use_container_width=True,
    type="primary",
)


# =========================================================
# 검색 결과 저장
# =========================================================
if "search_result" not in st.session_state:
    st.session_state.search_result = None

if search_btn:
    try:
        result_df = search_data(
            region,
            target,
            industry,
            int(min_money),
        )

        if exclude_dummy and not result_df.empty:
            result_df = result_df[
                ~result_df["name"].apply(is_dummy_policy_name)
            ]

        if sort_option == "금리 낮은순" and not result_df.empty:
            result_df = result_df.sort_values(
                by="금리",
                ascending=True,
                na_position="last",
            )

        elif sort_option == "지원한도 높은순" and not result_df.empty:
            result_df = result_df.sort_values(
                by="최대금액",
                ascending=False,
                na_position="last",
            )

        elif sort_option == "정책명순" and not result_df.empty:
            result_df = result_df.sort_values(
                by="name",
                ascending=True,
                na_position="last",
            )

        st.session_state.search_result = result_df

    except Exception as error:
        st.error(f"검색 중 오류가 발생했습니다: {error}")


# =========================================================
# 검색 결과 출력
# =========================================================
result_df = st.session_state.search_result

if result_df is not None:
    st.subheader(f"🔎 검색 결과 ({len(result_df):,}건)")

    if result_df.empty:
        st.warning(
            "조건에 맞는 실제 등록 정책이 없습니다. "
            "검색 조건을 완화하거나 상담 신청을 남겨주세요."
        )

    else:
        if len(result_df) > 20:
            st.info(
                "검색 결과가 많아 상위 20건만 표시합니다. "
                "지역·대상·업종 조건을 추가하면 더 정확하게 확인할 수 있습니다."
            )

        for _, policy_row in result_df.head(20).iterrows():
            render_policy_card(policy_row)


# =========================================================
# 상담 신청
# =========================================================
st.divider()
st.subheader("📞 정책자금 무료 사전진단 신청")

st.caption(
    "사업장 정보를 남겨주시면 업종, 업력, 매출, 신용상태 및 "
    "기존 대출을 기준으로 검토 가능한 방향을 안내드립니다."
)

with st.form(
    "consult_form",
    clear_on_submit=True,
):
    form_col1, form_col2 = st.columns(2)

    with form_col1:
        customer_name = st.text_input(
            "대표자명 *",
            placeholder="홍길동",
        )

        customer_phone = st.text_input(
            "연락처 *",
            placeholder="010-1234-5678",
        )

        customer_business = st.text_input(
            "사업자명 *",
            placeholder="홍길동식당",
        )

        customer_region = st.text_input(
            "사업장 지역",
            placeholder="대구",
        )

    with form_col2:
        customer_industry = st.text_input(
            "업종",
            placeholder="음식점업",
        )

        customer_amount = st.number_input(
            "희망 자금 *",
            min_value=0,
            max_value=10_000_000_000,
            value=0,
            step=10_000_000,
            format="%d",
        )

        selected_policy = st.text_input(
            "관심 정책",
            placeholder="검색 결과에서 확인한 정책명",
        )

        customer_message = st.text_area(
            "문의 내용",
            placeholder=(
                "업력, 연매출, 기존 대출, 연체·체납 여부 등을 "
                "간단히 작성해주세요."
            ),
        )

    privacy_agree = st.checkbox(
        "상담을 위한 개인정보 수집 및 이용에 동의합니다. *"
    )

    consult_submit = st.form_submit_button(
        "상담 신청하기",
        use_container_width=True,
        type="primary",
    )

    if consult_submit:
        customer_name = clean_text(customer_name)
        customer_phone = normalize_phone(customer_phone)
        customer_business = clean_text(customer_business)
        customer_region = clean_text(customer_region)
        customer_industry = clean_text(customer_industry)
        selected_policy = clean_text(selected_policy)
        customer_message = clean_text(customer_message)

        if not customer_name:
            st.warning("대표자명을 입력해주세요.")

        elif not is_valid_phone(customer_phone):
            st.warning("연락처를 정확하게 입력해주세요.")

        elif not customer_business:
            st.warning("사업자명을 입력해주세요.")

        elif customer_amount <= 0:
            st.warning("희망 자금을 입력해주세요.")

        elif not privacy_agree:
            st.warning("개인정보 수집 및 이용에 동의해주세요.")

        else:
            try:
                conn.execute(
                    """
                    INSERT INTO consult_requests (
                        name,
                        phone,
                        business,
                        region,
                        industry,
                        amount,
                        message,
                        selected_policy
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        customer_name,
                        customer_phone,
                        customer_business,
                        customer_region,
                        customer_industry,
                        int(customer_amount),
                        customer_message,
                        selected_policy,
                    ),
                )

                conn.commit()

                st.success(
                    "✅ 상담 신청이 접수되었습니다. 확인 후 연락드리겠습니다."
                )

            except sqlite3.Error as error:
                st.error(f"상담 신청 저장 중 오류가 발생했습니다: {error}")


# =========================================================
# 관리자 화면
# =========================================================
st.divider()

with st.expander("🧑‍💼 관리자 상담 신청 목록"):
    admin_password_input = st.text_input(
        "관리자 비밀번호",
        type="password",
        key="admin_password_input",
    )

    if admin_password_input:
        if check_admin_password(admin_password_input):
            st.success("관리자 인증 성공")

            try:
                consult_df = pd.read_sql(
                    """
                    SELECT
                        id,
                        name AS 대표자명,
                        phone AS 연락처,
                        business AS 사업자명,
                        region AS 지역,
                        industry AS 업종,
                        amount AS 희망자금,
                        selected_policy AS 관심정책,
                        message AS 문의내용,
                        created_at AS 신청일시
                    FROM consult_requests
                    ORDER BY created_at DESC
                    """,
                    conn,
                )

                if consult_df.empty:
                    st.info("📭 현재 상담 신청 데이터가 없습니다.")

                else:
                    display_df = consult_df.copy()

                    display_df["희망자금"] = display_df["희망자금"].apply(
                        lambda value: f"{int(clean_number(value)):,}원"
                    )

                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        hide_index=True,
                    )

                    output = BytesIO()

                    with pd.ExcelWriter(
                        output,
                        engine="openpyxl",
                    ) as writer:
                        consult_df.to_excel(
                            writer,
                            index=False,
                            sheet_name="상담신청목록",
                        )

                    st.download_button(
                        label="📥 상담 신청 목록 엑셀 다운로드",
                        data=output.getvalue(),
                        file_name="consult_requests.xlsx",
                        mime=(
                            "application/vnd.openxmlformats-officedocument."
                            "spreadsheetml.sheet"
                        ),
                        use_container_width=True,
                    )

            except Exception as error:
                st.error(f"관리자 DB 조회 중 오류가 발생했습니다: {error}")

        else:
            st.error("관리자 비밀번호가 일치하지 않습니다.")
