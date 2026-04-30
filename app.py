import streamlit as st
import pandas as pd
from io import BytesIO
import re

st.set_page_config(
    page_title="정책자금 DB 관리 시스템",
    page_icon="📊",
    layout="wide"
)

# -------------------------------
# 기본 함수
# -------------------------------

def clean_text(value):
    """빈값, 숫자, NaN 등을 안전하게 문자열로 정리"""
    if pd.isna(value):
        return ""
    return str(value).strip()


def clean_phone(콜):
    """전화번호에서 숫자만 추출"""
    phone = clean_text(콜)
    phone = re.sub(r"[^0-9]", "", phone)
    return phone


def is_valid_phone(콜):
    """휴대폰 번호 유효성 검사"""
    phone = clean_phone(콜)

    if not phone:
        return False

    # 010, 011 등 휴대폰 번호 기준
    if len(콜) not in [10, 11]:
        return False

    if not phone.startswith(("010", "011", "016", "017", "018", "019")):
        return False

    return True


def to_excel(df):
    """데이터프레임을 엑셀 파일로 변환"""
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="정책자금DB")

    return output.getvalue()


# -------------------------------
# 화면 제목
# -------------------------------

st.title("📊 정책자금 DB 관리 시스템")
st.write("엑셀 파일을 업로드하면 전화번호를 정리하고 유효한 고객 DB만 추출합니다.")

st.markdown("---")

# -------------------------------
# 파일 업로드
# -------------------------------

uploaded_file = st.file_uploader(
    "엑셀 파일을 업로드하세요",
    type=["xlsx", "xls", "csv"]
)

if uploaded_file is not None:

    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success("파일 업로드 성공")

        st.subheader("원본 데이터 미리보기")
        st.dataframe(df.head())

        st.markdown("---")

        # -------------------------------
        # 컬럼 선택
        # -------------------------------

        st.subheader("컬럼 선택")

        columns = df.columns.tolist()

        name_col = st.selectbox(
            "이름 컬럼을 선택하세요",
            columns
        )

        phone_col = st.selectbox(
            "전화번호 컬럼을 선택하세요",
            columns
        )

        memo_col = st.selectbox(
            "메모/업종/비고 컬럼을 선택하세요",
            ["없음"] + columns
        )

        st.markdown("---")

        # -------------------------------
        # DB 정리 실행
        # -------------------------------

        if st.button("DB 정리하기"):

            cleaned_rows = []
            invalid_rows = []

            for _, row in df.iterrows():

                name = clean_text(row[name_col])
                phone = clean_phone(row[phone_col])

                if memo_col != "없음":
                    memo = clean_text(row[memo_col])
                else:
                    memo = ""

                # 이름 없으면 제외
                if not name:
                    invalid_rows.append({
                        "이름": name,
                        "전화번호": phone,
                        "메모": memo,
                        "제외사유": "이름 없음"
                    })
                    continue

                # 전화번호 유효성 검사
                if not is_valid_phone(콜):
                    invalid_rows.append({
                        "이름": name,
                        "전화번호": phone,
                        "메모": memo,
                        "제외사유": "전화번호 오류"
                    })
                    continue

                cleaned_rows.append({
                    "이름": name,
                    "전화번호": phone,
                    "메모": memo
                })

            cleaned_df = pd.DataFrame(cleaned_rows)
            invalid_df = pd.DataFrame(invalid_rows)

            # -------------------------------
            # 결과 출력
            # -------------------------------

            st.success("DB 정리가 완료되었습니다.")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("전체 데이터", len(df))

            with col2:
                st.metric("정상 데이터", len(cleaned_df))

            with col3:
                st.metric("제외 데이터", len(invalid_df))

            st.markdown("---")

            st.subheader("정상 DB")
            st.dataframe(cleaned_df)

            if not invalid_df.empty:
                st.subheader("제외된 데이터")
                st.dataframe(invalid_df)

            # -------------------------------
            # 엑셀 다운로드
            # -------------------------------

            if not cleaned_df.empty:
                excel_data = to_excel(cleaned_df)

                st.download_button(
                    label="정리된 DB 엑셀 다운로드",
                    data=excel_data,
                    file_name="정책자금_DB_정리본.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    except Exception as e:
        st.error("오류가 발생했습니다.")
        st.exception(e)

else:
    st.info("엑셀 파일을 업로드하면 DB 정리를 시작할 수 있습니다.")
