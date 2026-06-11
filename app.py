import streamlit as st

st.set_page_config(
    page_title="Stock & AI Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.title("📊 메뉴")
page = st.sidebar.radio("페이지 선택", ["📈 미국 주식 데이터", "🤖 Gemini 챗봇"])

if page == "📈 미국 주식 데이터":
    import stock_page
    stock_page.show()
else:
    import chatbot_page
    chatbot_page.show()
