import streamlit as st


def _get_api_key() -> tuple[str, bool]:
    """
    Secrets에 키가 있으면 그걸 사용 (관리자 설정),
    없으면 사이드바 입력란을 표시해 사용자가 직접 입력하도록 함.
    반환값: (api_key, is_from_secrets)
    """
    secrets_key = st.secrets.get("GEMINI_API_KEY", "")
    if secrets_key:
        return secrets_key, True

    # Secrets에 없을 때만 입력란 표시
    user_key = st.sidebar.text_input(
        "Gemini API Key",
        type="password",
        placeholder="AIza...",
        help="Google AI Studio에서 발급받은 API 키를 입력하세요.",
    )
    return user_key, False


def show():
    st.title("🤖 Gemini AI 챗봇")

    with st.sidebar:
        st.subheader("🔑 API 설정")
        api_key, from_secrets = _get_api_key()

        if from_secrets:
            st.success("API 키가 설정되어 있습니다.", icon="✅")

        model_choice = st.selectbox(
            "모델 선택",
            ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
        )
        if st.button("대화 초기화", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    if not api_key:
        st.info("👈 왼쪽 사이드바에 Gemini API Key를 입력하면 챗봇이 활성화됩니다.")
        st.markdown(
            "API 키는 [Google AI Studio](https://aistudio.google.com/app/apikey)에서 무료로 발급받을 수 있습니다."
        )
        return

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        st.error("`google-genai` 패키지가 설치되어 있지 않습니다.")
        return

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("메시지를 입력하세요...")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("생각 중..."):
                try:
                    client = genai.Client(api_key=api_key)
                    history = [
                        types.Content(
                            role=m["role"] if m["role"] != "assistant" else "model",
                            parts=[types.Part(text=m["content"])]
                        )
                        for m in st.session_state.messages[:-1]
                    ]
                    history.append(types.Content(role="user", parts=[types.Part(text=prompt)]))
                    response = client.models.generate_content(
                        model=model_choice,
                        contents=history,
                    )
                    answer = response.text
                except Exception as e:
                    answer = f"오류가 발생했습니다: {e}"

            st.markdown(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})
