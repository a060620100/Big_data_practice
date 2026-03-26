import streamlit as st
from sqlalchemy import create_engine, Column, Integer, Float, String, Date, DateTime, Text, desc,text
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import requests

load_dotenv()

# 讀取 API URL 與資料庫設定
API_BASE = "http://8.229.26.9:8000"
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

# --- 1. 設定與連線 ---
st.set_page_config(page_title="經濟健康度儀表板", layout="wide")
Base = declarative_base()
API_BASE = f"{API_BASE}"  # FastAPI 位址
DATABASE_URL = f"mysql+pymysql://Lin_Po_Wei:rDAZFLHZmNGenr0a3Xzo@8.229.26.9:3306/mydb"
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle= 1800
)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT NOW();"))
        print("✅ 連線成功！資料庫時間：", result.fetchone())
except Exception as e:
    print("❌ 連線失敗：", e)


# --- 2. 定義資料獲取函式 ---

# # (保留) 從 API 獲取即時個股價格
# @st.cache_data(ttl=300)
# def fetch_stock_price(symbol):
#     try:
#         res = requests.get(f"{API_BASE}/stock_price", params={"symbol": symbol}, timeout=5)
#         return res.json() if res.status_code == 200 else None
#     except:
#         return None

class EconomicScore(Base):
    __tablename__ = "economic_score"
    id = Column(Integer, primary_key=True)
    score_date = Column(Date)
    total_score = Column(Float)
    signal_light = Column(String(10))
    # ... 其他欄位 cpi_score, ppi_score 等依此類推

class NewsArticle(Base):
    __tablename__ = "news_articles"
    id = Column(Integer, primary_key=True)
    title = Column(String(255))
    link = Column(String(500))
    source = Column(String(50))
    content = Column(Text)
    sentiment_score = Column(Float)
    importance_score = Column(Float)
    created_at = Column(DateTime)


def show_economic_dashboard():
    st.title("📊 經濟健康度 (直連 MySQL 版)")

    db = SessionLocal()
    try:
        # 取出所有日期供下拉選單使用
        dates = db.query(EconomicScore.score_date).distinct().order_by(EconomicScore.score_date.desc()).all()
        available_dates = [str(d.score_date) for d in dates]

        selected_date = st.sidebar.selectbox("請選擇查詢月份", options=available_dates)

        if selected_date:
            data = db.query(EconomicScore).filter(EconomicScore.score_date == selected_date).first()

            col1, col2 = st.columns(2)
            col1.metric("綜合評分", f"{data.total_score:.1f}")
            with col2:
                sig = data.signal_light.upper()
                if sig == "RED":
                    st.error("🔴 高風險紅燈")
                elif sig == "YELLOW":
                    st.warning("🟡 警示黃燈")
                else:
                    st.success("🟢 穩健綠燈")
    finally:
        db.close()


def show_news_dashboard():
    st.title("📰 美股精選新聞 (直連 MySQL 版)")

    days = st.sidebar.slider("幾天內新聞？", 1, 7, 3)
    limit = st.sidebar.number_input("顯示數量", 5, 50, 10)

    db = SessionLocal()
    try:
        time_threshold = datetime.now() - timedelta(days=days)
        top_news = db.query(NewsArticle) \
            .filter(NewsArticle.created_at >= time_threshold) \
            .order_by(desc(NewsArticle.importance_score)) \
            .limit(limit).all()

        if not top_news:
            st.warning("資料庫中尚無資料，請先執行爬蟲。")
        else:
            for news in top_news:
                with st.container():
                    col_s, col_c = st.columns([1, 6])
                    col_s.metric("重要性", f"{news.importance_score:.2f}")
                    with col_c:
                        st.subheader(f"[{news.title}]({news.link})")
                        st.caption(f"來源: {news.source} | 情緒: {news.sentiment_score:.2f}")
                        with st.expander("內容摘要"):
                            st.write(news.content)
                st.divider()
    finally:
        db.close()


# # --- 4. 導航設定 ---
st.set_page_config(page_title="金融監控中心", layout="wide")

pg = st.navigation([
    st.Page(show_economic_dashboard, title="經濟指標", icon="📈"),
    st.Page(show_news_dashboard, title="美股新聞", icon="📰"),
])
pg.run()