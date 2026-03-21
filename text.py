import streamlit as st
import pandas as pd
import requests
from sqlalchemy import create_engine
import plotly.express as px
import plotly.graph_objects as go

# --- 1. 設定與連線 ---
st.set_page_config(page_title="經濟健康度儀表板", layout="wide")

BASE_URL = "http://127.0.0.1:8000"  # FastAPI 位址
DATABASE_URL = "mysql+pymysql://root:1qaz2WSX@8.229.26.9:3306/mydb"
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        result = conn.execute("SELECT NOW();")
        st.success(f"✅ MariaDB 連線成功！資料庫時間：{result.fetchone()[0]}")
except Exception as e:
    st.error(f"❌ MariaDB 連線失敗：{e}")