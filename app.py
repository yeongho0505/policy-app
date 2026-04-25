import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import re

# -------------------------------
# 페이지 설정
# -------------------------------
st.set_page_config(page_title="정책자금 조회", layout="wide")

# -------------------------------
# DB 연결
# -------------------------------
conn = sqlite3.connect("policy_funds.db", check_same_thread=False)

# -------------------------------
# 보안 함수
# -------------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_admin_password(input_password):
    try:
        admin_password = st.secrets["ADMIN_PASSWORD"]
    except Exception:
        admin_password = "1234"

    return hash_password(input_password) == hash_password(admin_password)

def clean_text(value):
    if value is None:
        return ""
    return str(value).strip()

def is_valid_phone(콜):
    phone = phone.replace("-", "").replace(" ", "")
    return phone.isdigit() and len(콜) >= 10

# -------------------------------
# 테이블 생성
# -------------------------------
def create_table():
    conn.execute("""
    CREATE TABLE IF NOT EXISTS policy_funds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
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
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS consult_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        business TEXT,
        region TEXT,
        industry TEXT,
        amount INTEGER,
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()

create_table()

# -------------------------------
# 검색 함수
# -------------------------------
def search_data(region, target, industry, min_money):
    query = "SELECT * FROM policy_funds WHERE 최대금액 >= ?"
    params = [min_money]

    if region != "전체":
        query += " AND 지역 LIKE ?"
        params.append(f"%{region}%")

    if target != "전체":
        query += " AND 대상 LIKE ?"
        params.append(f"%{target}%")

    if industry != "전체":
        query += " AND 업종 LIKE ?"
        params.append(f"%{industry}%")

    return pd.read_sql(query, conn, params=params)

# -------------------------------
# UI 시작
# -------------------------------
st.title("📊 정책자금 조회 웹앱")

# -------------------------------
# 사이드바 검색 조건
# -------------------------------
st.sidebar.header("🔍 검색 조건")

region = st.sidebar.selectbox(
    "지역",
    ["전체", "서울", "경기", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]
)

target = st.sidebar.selectbox(
    "대상",
    ["전체", "청년", "소상공인", "중소기업"]
)

industry = st.sidebar.selectbox(
    "업종",
    ["전체", "제조", "서비스", "IT", "유통"]
)

min_money = st.sidebar.slider("최소 지원금", 0, 100000000, 0)

sort_option = st.sidebar.selectbox(
    "정렬 기준",
    ["없음", "금리 낮은순", "지원금 높은순"]
)

search_btn = st.sidebar.button("검색")

# -------------------------------
# 검색 결과
# -------------------------------
if search_btn:
    df = search_data(region, target, industry, min_money)

    if sort_option == "금리 낮은순":
        df = df.sort_values(by="금리")
    elif sort_option == "지원금 높은순":
        df = df.sort_values(by="최대금액", ascending=False)

    st.subheader(f"🔎 검색 결과 ({len(df)}건)")

    if len(df) > 0:
        for _, row in df.iterrows():
            with st.expander(f"📌 {row['name']}"):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"기관: {row['기관']}")
                    st.write(f"대상: {row['대상']}")
                    st.write(f"업종: {row['업종']}")
                    st.write(f"지역: {row['지역']}")

                with col2:
                    st.write(f"지원금: {row['최대금액']:,}원")
                    st.write(f"금리: {row['금리']}%")
                    st.write(f"형태: {row['지원형태']}")
                    st.write(f"기간: {row['신청기간']}")

                st.write("조건:", row["조건"])
                st.markdown(f"[👉 신청 바로가기]({row['링크']})")
    else:
        st.warning("조건에 맞는 정책이 없습니다.")

# -------------------------------
# 상담 신청
# -------------------------------
st.markdown("---")
st.subheader("📞 정책자금 상담 신청")

with st.form("consult_form"):
    name = st.text_input("이름")
    phone = st.text_input("연락처")
    business = st.text_input("사업자명")
    region_c = st.text_input("지역")
    industry_c = st.text_input("업종")
    amount = st.number_input("희망 자금", value=0, step=1000000)
    message = st.text_area("문의 내용")

    submit = st.form_submit_button("상담 신청하기")

    if submit:
        name = clean_text(name)
        phone = clean_text(콜)
        business = clean_text(business)
        region_c = clean_text(region_c)
        industry_c = clean_text(industry_c)
        message = clean_text(message)

        if not name:
            st.warning("이름을 입력해주세요.")
        elif not is_valid_phone(콜):
            st.warning("연락처를 정확히 입력해주세요.")
        elif not business:
            st.warning("사업자명을 입력해주세요.")
        elif amount <= 0:
            st.warning("희망 자금을 입력해주세요.")
        else:
            conn.execute("""
            INSERT INTO consult_requests
            (name, phone, business, region, industry, amount, message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, phone, business, region_c, industry_c, amount, message))

            conn.commit()
            st.success("✅ 상담 신청 완료!")

# -------------------------------
# 관리자 페이지
# -------------------------------
st.markdown("---")
st.subheader("🧑‍💼 관리자 상담 신청 목록")

admin_password = st.text_input("관리자 비밀번호", type="#n10090425")

if admin_password:
    if check_admin_password(admin_password):
        consult_df = pd.read_sql(
            "SELECT * FROM consult_requests ORDER BY created_at DESC",
            conn
        )

        st.success("관리자 인증 성공")

        if len(consult_df) > 0:
            st.dataframe(consult_df)
        else:
            st.info("아직 상담 신청 내역이 없습니다.")
    else:
        st.error("비밀번호가 틀렸습니다.")
