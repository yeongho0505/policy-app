import streamlit as st
import sqlite3
import pandas as pd

# -------------------------------
# DB 연결
# -------------------------------
conn = sqlite3.connect("policy_funds.db", check_same_thread=False)

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

create_table()

# -------------------------------
# 데이터 로드
# -------------------------------
def load_data():
    return pd.read_sql("SELECT * FROM policy_funds", conn)

# -------------------------------
# 검색 함수
# -------------------------------
def search_data(region, target, industry, min_money):
    query = f"""
    SELECT * FROM policy_funds
    WHERE 지역 LIKE '%{region}%'
    AND 대상 LIKE '%{target}%'
    AND 업종 LIKE '%{industry}%'
    AND 최대금액 >= {min_money}
    """
    return pd.read_sql(query, conn)

# -------------------------------
# UI 시작
# -------------------------------
st.set_page_config(page_title="정책자금 조회", layout="wide")

st.title("📊 정책자금 조회 웹앱")

# -------------------------------
# 사이드바 필터
# -------------------------------
st.sidebar.header("🔍 검색 조건")

region = st.sidebar.selectbox("지역", ["", "서울", "경기", "부산"])
target = st.sidebar.selectbox("대상", ["", "청년", "소상공인", "중소기업"])
industry = st.sidebar.selectbox("업종", ["", "제조", "서비스", "IT"])

min_money = st.sidebar.slider("최소 지원금", 0, 100000000, 0)

sort_option = st.sidebar.selectbox(
    "정렬 기준",
    ["없음", "금리 낮은순", "지원금 높은순"]
)

search_btn = st.sidebar.button("검색")

# -------------------------------
# 데이터 표시
# -------------------------------
if search_btn:
    df = search_data(region, target, industry, min_money)

    # 정렬
    if sort_option == "금리 낮은순":
        df = df.sort_values(by="금리")
    elif sort_option == "지원금 높은순":
        df = df.sort_values(by="최대금액", ascending=False)

    st.subheader(f"🔎 검색 결과 ({len(df)}건)")

    if len(df) > 0:
        for i, row in df.iterrows():
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

                st.write("조건:", row['조건'])
                st.markdown(f"[👉 신청 바로가기]({row['링크']})")

    else:
        st.warning("조건에 맞는 정책이 없습니다.")

# -------------------------------
# 엑셀 다운로드
# -------------------------------
st.sidebar.subheader("📥 데이터 다운로드")

if st.sidebar.button("엑셀 다운로드"):
    df = load_data()
    df.to_excel("policy_data.xlsx", index=False)

    with open("policy_data.xlsx", "rb") as file:
        st.download_button(
            label="다운로드",
            data=file,
            file_name="policy_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# -------------------------------
# 데이터 추가
# -------------------------------
st.sidebar.subheader("➕ 정책 추가")

with st.sidebar.form("add_form"):
    name = st.text_input("정책명")
    기관 = st.text_input("기관")
    대상 = st.text_input("대상")
    업종 = st.text_input("업종")
    지역 = st.text_input("지역")
    금액 = st.number_input("최대금액", value=0)
    금리 = st.number_input("금리", value=0.0)
    형태 = st.text_input("지원형태")
    조건 = st.text_area("조건")
    기간 = st.text_input("신청기간")
    링크 = st.text_input("링크")

    submitted = st.form_submit_button("저장")

    if submitted:
        conn.execute("""
        INSERT INTO policy_funds
        (name, 기관, 대상, 업종, 지역, 최대금액, 금리, 지원형태, 조건, 신청기간, 링크)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, 기관, 대상, 업종, 지역, 금액, 금리, 형태, 조건, 기간, 링크))
        
        conn.commit()
        st.success("저장 완료!")
        # -------------------------------
# 상담 신청 기능
# -------------------------------

conn.execute("""
CREATE TABLE IF NOT EXISTS consult_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone TEXT,
    business_name TEXT,
    region TEXT,
    industry TEXT,
    desired_amount INTEGER,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

st.markdown("---")
st.subheader("📞 정책자금 상담 신청")

with st.form("consult_form"):
    name = st.text_input("이름")
    phone = st.text_input("연락처")
    business_name = st.text_input("사업자명")
    consult_region = st.text_input("지역")
    consult_industry = st.text_input("업종")
    desired_amount = st.number_input("희망 자금", value=0, step=1000000)
    message = st.text_area("문의 내용")

    submitted = st.form_submit_button("상담 신청하기")

    if submitted:
        conn.execute("""
        INSERT INTO consult_requests
        (name, phone, business_name, region, industry, desired_amount, message)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            phone,
            business_name,
            consult_region,
            consult_industry,
            desired_amount,
            message
        ))
        conn.commit()
        st.success("상담 신청이 저장되었습니다.")
     # -------------------------------
# 관리자 페이지
# -------------------------------
st.markdown("---")
st.subheader("🧑‍💼 관리자 상담 신청 목록")

password = st.text_input("관리자 비밀번호", type="password")

if password:
    try:
        admin_pw = st.secrets["ADMIN_PASSWORD"]
    except:
        admin_pw = "1234"

    if password == admin_pw:
        st.success("관리자 인증 성공")

        try:
            df = pd.read_sql(
                "SELECT * FROM consult_requests ORDER BY created_at DESC",
                conn
            )

            if len(df) > 0:
                st.dataframe(df)

             from io import BytesIO

output = BytesIO()
df.to_excel(output, index=False, engine='openpyxl')
excel_data = output.getvalue()

st.download_button(
    label="📥 엑셀 다운로드",
    data=excel_data,
    file_name="consult_requests.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)   
            else:
                st.info("📭 상담 신청 데이터가 없습니다.")

        except Exception as e:
            st.error(f"DB 오류: {e}")

    else:
        st.error("비밀번호 틀림")
