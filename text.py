import streamlit as st
import pandas as pd
import requests
from sqlalchemy import create_engine ,text
import plotly.express as px
import plotly.graph_objects as go

# --- 1. 設定與連線 ---
st.set_page_config(page_title="經濟健康度儀表板", layout="wide")

BASE_URL = "http://127.0.0.1:8000"  # FastAPI 位址
DATABASE_URL = "mysql+pymysql://Lin_Po_Wei:1qaz2WSX@8.229.26.9:3306/mydb"
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT NOW();"))
        print("✅ 連線成功！資料庫時間：", result.fetchone())
except Exception as e:
    print("❌ 連線失敗：", e)


