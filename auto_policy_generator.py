import sqlite3
import random

conn = sqlite3.connect("policy_funds.db")
cursor = conn.cursor()

# 테이블 생성
cursor.execute("""
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

# 샘플 데이터
기관_list = ["중소벤처기업부", "소상공인시장진흥공단", "신용보증기금", "기술보증기금"]
대상_list = ["청년", "소상공인", "중소기업"]
업종_list = ["제조", "서비스", "IT", "유통"]
지역_list = ["서울", "경기", "부산", "대구"]
형태_list = ["대출", "보조금", "보증"]

def generate_policy(i):
    name = f"정책자금_{i}"
    기관 = random.choice(기관_list)
    대상 = random.choice(대상_list)
    업종 = random.choice(업종_list)
    지역 = random.choice(지역_list)
    금액 = random.randint(10000000, 100000000)
    금리 = round(random.uniform(1.0, 4.5), 2)
    형태 = random.choice(형태_list)
    조건 = f"{대상} 대상 지원 정책"
    기간 = "상시"
    링크 = "https://example.com"

    cursor.execute("""
    INSERT INTO policy_funds
    (name, 기관, 대상, 업종, 지역, 최대금액, 금리, 지원형태, 조건, 신청기간, 링크)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, 기관, 대상, 업종, 지역, 금액, 금리, 형태, 조건, 기간, 링크))

# 1000개 생성
for i in range(1000):
    generate_policy(i)

conn.commit()
conn.close()

print("✅ 1000개 정책자금 DB 생성 완료")
