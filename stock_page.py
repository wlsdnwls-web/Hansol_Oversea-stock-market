import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

STOCKS = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "NVIDIA": "NVDA",
    "Amazon": "AMZN",
    "Alphabet (Google)": "GOOGL",
    "Meta": "META",
    "Tesla": "TSLA",
    "Berkshire Hathaway": "BRK-B",
    "JPMorgan Chase": "JPM",
    "Eli Lilly": "LLY",
}


def show():
    st.title("📈 미국 주식 데이터 (Top 10)")
    st.caption("yfinance 기반 실시간 주식 정보")

    col1, col2 = st.columns([2, 1])
    with col1:
        period_map = {"1주": "5d", "1개월": "1mo", "3개월": "3mo", "6개월": "6mo", "1년": "1y"}
        period_label = st.selectbox("기간 선택", list(period_map.keys()), index=2)
        period = period_map[period_label]
    with col2:
        selected_stock_name = st.selectbox("차트 표시 종목", list(STOCKS.keys()))

    st.divider()

    with st.spinner("주식 데이터 불러오는 중..."):
        tickers = list(STOCKS.values())
        names = list(STOCKS.keys())

        summary_rows = []
        for name, ticker in STOCKS.items():
            try:
                info = yf.Ticker(ticker).fast_info
                summary_rows.append({
                    "종목명": name,
                    "티커": ticker,
                    "현재가 ($)": round(info.last_price, 2),
                    "전일대비 (%)": round((info.last_price - info.previous_close) / info.previous_close * 100, 2),
                    "52주 최고": round(info.fifty_two_week_high, 2),
                    "52주 최저": round(info.fifty_two_week_low, 2),
                    "시가총액 (B$)": round(info.market_cap / 1e9, 1) if info.market_cap else "N/A",
                })
            except Exception:
                summary_rows.append({"종목명": name, "티커": ticker, "현재가 ($)": "오류", "전일대비 (%)": "-", "52주 최고": "-", "52주 최저": "-", "시가총액 (B$)": "-"})

        df_summary = pd.DataFrame(summary_rows)

    def color_change(val):
        try:
            v = float(val)
            color = "color: #22c55e" if v > 0 else ("color: #ef4444" if v < 0 else "")
            return color
        except Exception:
            return ""

    styled = df_summary.style.applymap(color_change, subset=["전일대비 (%)"])
    st.dataframe(styled, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader(f"📊 {selected_stock_name} ({STOCKS[selected_stock_name]}) 차트 — {period_label}")

    hist = yf.Ticker(STOCKS[selected_stock_name]).history(period=period)
    if hist.empty:
        st.warning("데이터를 불러올 수 없습니다.")
        return

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.7, 0.3], vertical_spacing=0.04)

    fig.add_trace(go.Candlestick(
        x=hist.index, open=hist["Open"], high=hist["High"],
        low=hist["Low"], close=hist["Close"],
        name="캔들", increasing_line_color="#22c55e", decreasing_line_color="#ef4444"
    ), row=1, col=1)

    ma20 = hist["Close"].rolling(20).mean()
    fig.add_trace(go.Scatter(x=hist.index, y=ma20, name="MA20",
                             line=dict(color="#f59e0b", width=1.5)), row=1, col=1)

    fig.add_trace(go.Bar(
        x=hist.index, y=hist["Volume"],
        name="거래량",
        marker_color=["#22c55e" if c >= o else "#ef4444"
                      for c, o in zip(hist["Close"], hist["Open"])]
    ), row=2, col=1)

    fig.update_layout(
        height=520,
        xaxis_rangeslider_visible=False,
        showlegend=True,
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        font_color="#fafafa",
    )
    fig.update_xaxes(gridcolor="#1f2937")
    fig.update_yaxes(gridcolor="#1f2937")

    st.plotly_chart(fig, use_container_width=True)
