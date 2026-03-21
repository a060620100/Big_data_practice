import streamlit as st
import pandas as pd
import requests
from sqlalchemy import create_engine
import plotly.express as px
import plotly.graph_objects as go

# --- 1. 設定與連線 ---
st.set_page_config(page_title="經濟健康度儀表板", layout="wide")

BASE_URL = "http://127.0.0.1:8000"  # FastAPI 位址
DATABASE_URL = "mysql+pymysql://root:yarrow1016@127.0.0.1:3306/macro_monitor_1"
engine = create_engine(DATABASE_URL)

# --- 2. 定義資料獲取函式 ---

# (保留) 從 API 獲取即時個股價格
@st.cache_data(ttl=300)
def fetch_stock_price(symbol):
    try:
        res = requests.get(f"{BASE_URL}/stock_price", params={"symbol": symbol}, timeout=5)
        return res.json() if res.status_code == 200 else None
    except:
        return None

# (新增) 直接從資料庫獲取評分歷史數據
@st.cache_data(ttl=600)
def get_historical_scores():
    query = "SELECT * FROM economic_score ORDER BY score_date ASC"
    df = pd.read_sql(query, engine)
    df['score_date'] = pd.to_datetime(df['score_date'])
    return df

# --- 3. 頁面標題 ---
st.title("📊 經濟健康度與股市監控儀表板")

# --- 4. 頂部區塊：即時個股報價 (來自 FastAPI) ---
st.subheader("🔥 熱門標的即時監控 (API 來源)")
target_stocks = ["NVDA", "TSLA", "COST", "BA"] 
stock_cols = st.columns(len(target_stocks))

for i, symbol in enumerate(target_stocks):
    with stock_cols[i]:
        s_data = fetch_stock_price(symbol)
        if s_data and "current_price" in s_data:
            st.metric(
                label=s_data["symbol"], 
                value=f"${s_data['current_price']}", 
                delta=f"{s_data['change']}"
            )
        else:
            st.info(f"等待 {symbol}...")

st.divider()

# --- 5. 中間區塊：評分系統圖表 (來自 MySQL) ---
try:
    df_history = get_historical_scores()
    
    col_l, col_r = st.columns([1, 3]) # 左窄右寬

    with col_l:
        st.subheader("🔍 評分查詢")
        symbols = df_history['symbol'].unique()
        selected_symbol = st.selectbox("選擇監控標的", symbols)
        
        # 篩選特定標的資料
        plot_df = df_history[df_history['symbol'] == selected_symbol].copy()
        latest = plot_df.iloc[-1]
        
        # 顯示最新狀態卡片
        st.write(f"**最新觀測：{latest['score_date'].date()}**")
        score = latest['total_score']
        if score >= 80:
            st.success(f"當前燈號：🟢 GREEN ({int(score)}分)")
        else:
            st.warning(f"當前燈號：🟡 YELLOW ({int(score)}分)")
        
        st.metric("收盤價", f"${latest['adj_close']:.2f}")

    with col_r:
        st.subheader(f"{selected_symbol} 歷史趨勢圖")
        # 製作分數走勢圖
        fig = px.area(plot_df, x='score_date', y='total_score', 
                      title="歷史綜合評分變化",
                      color_discrete_sequence=['#3366CC'])
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    # --- 6. 底部區塊：詳細數據與均線對照 ---
    with st.expander("查看技術面與原始數據詳情"):
        # 計算 200MA
        plot_df['ma200'] = plot_df['adj_close'].rolling(window=200).mean()
        
        fig_price = go.Figure()
        fig_price.add_trace(go.Scatter(x=plot_df['score_date'], y=plot_df['adj_close'], name='收盤價'))
        fig_price.add_trace(go.Scatter(x=plot_df['score_date'], y=plot_df['ma200'], name='200日均線', line=dict(dash='dash', color='orange')))
        fig_price.update_layout(title="價格與 200MA 對照 (技術面判斷依據)")
        st.plotly_chart(fig_price, use_container_width=True)
        
        st.dataframe(plot_df.sort_values('score_date', ascending=False), use_container_width=True)

except Exception as e:
    st.error(f"資料庫讀取失敗：{e}")

