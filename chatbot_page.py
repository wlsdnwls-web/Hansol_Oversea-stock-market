import time
import re
import streamlit as st


def _get_api_key() -> tuple[str, bool]:
    secrets_key = st.secrets.get("OPENAI_API_KEY", "")
    if secrets_key:
        return secrets_key, True

    user_key = st.sidebar.text_input(
        "OpenAI API Key",
        type="password",
        placeholder="sk-...",
        help="OpenAI Platform에서 발급받은 API 키를 입력하세요.",
    )
    return user_key, False


def _call_openai(client, model: str, messages: list) -> str:
    MAX_RETRIES = 3
    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
            )
            return response.choices[0].message.content
        except Exception as e:
            err = str(e)
            is_rate_limit = "429" in err or "RateLimitError" in type(e).__name__
            is_last = attempt == MAX_RETRIES - 1

            if is_rate_limit and not is_last:
                delay = 20
                match = re.search(r"try again in ([\d.]+)s", err)
                if match:
                    delay = int(float(match.group(1))) + 1
                placeholder = st.empty()
                for remaining in range(delay, 0, -1):
                    placeholder.warning(
                        f"API 요청 한도 초과 — {remaining}초 후 자동 재시도합니다... "
                        f"({attempt + 1}/{MAX_RETRIES})"
                    )
                    time.sleep(1)
                placeholder.empty()
                continue

            if is_rate_limit:
                raise RateLimitError(err)
            raise e

    raise RuntimeError("최대 재시도 횟수 초과")


class RateLimitError(Exception):
    pass


def show():
    st.title("🤖 OpenAI 챗봇")

    with st.sidebar:
        st.subheader("🔑 API 설정")
        api_key, from_secrets = _get_api_key()

        if from_secrets:
            st.success("API 키가 설정되어 있습니다.", icon="✅")

        model_choice = st.selectbox(
            "모델 선택",
            ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
        )

        st.divider()
        system_prompt = st.text_area(
            "시스템 프롬프트 (선택)",
            value="You are a helpful assistant. Please respond in Korean.",
            height=80,
        )

        if st.button("대화 초기화", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    if not api_key:
        st.info("👈 왼쪽 사이드바에 OpenAI API Key를 입력하면 챗봇이 활성화됩니다.")
        st.markdown(
            "API 키는 [OpenAI Platform](https://platform.openai.com/api-keys)에서 발급받을 수 있습니다."
        )
        return

    try:
        from openai import OpenAI
    except ImportError:
        st.error("`openai` 패키지가 설치되어 있지 않습니다.")
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
                    client = OpenAI(api_key=api_key)
                    api_messages = [{"role": "system", "content": system_prompt}] + st.session_state.messages
                    answer = _call_openai(client, model_choice, api_messages)

                except RateLimitError:
                    answer = None
                    st.error(
                        "**API 요청 한도를 초과했습니다.**\n\n"
                        "**해결 방법:**\n"
                        "- 잠시 후 다시 시도하세요\n"
                        "- [OpenAI Platform](https://platform.openai.com/account/billing)에서 크레딧을 충전하세요\n"
                        "- 사이드바에서 더 저렴한 모델(gpt-4o-mini)로 바꿔보세요"
                    )
                except Exception as e:
                    answer = None
                    st.error(f"오류가 발생했습니다: {e}")

            if answer:
                st.markdown(answer)

        if answer:
            st.session_state.messages.append({"role": "assistant", "content": answer})
