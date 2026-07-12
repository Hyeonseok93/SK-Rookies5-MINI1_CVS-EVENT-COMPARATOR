import streamlit as st
import pandas as pd
import os
from groq import Groq
from dotenv import load_dotenv

from utils.paths import categorized_path

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None


@st.cache_data(ttl=3600)
def load_chatbot_data():
    path = categorized_path()
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()


def show_chatbot():
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "🏪 **편의점 꿀팁봇 사용법**\n\n"
                           "1. **상품 검색**: 궁금한 상품명을 입력하세요.\n"
                           "2. **행사 확인**: 1+1, 2+1 등 행사 정보를 물어보세요.\n"
                           "3. **카테고리**: '과자', '도시락' 등으로 검색 가능합니다."
            }
        ]

    # Scope FAB styles to the chatbot popover only (sibling of #cvs-chatbot-anchor)
    st.markdown("""
    <div id="cvs-chatbot-anchor"></div>
    <style>
    div.element-container:has(#cvs-chatbot-anchor) + div.element-container div[data-testid="stPopover"] {
        position: fixed !important;
        bottom: 30px !important;
        right: 30px !important;
        width: 65px !important;
        height: 65px !important;
        z-index: 999999 !important;
    }
    div.element-container:has(#cvs-chatbot-anchor) + div.element-container div[data-testid="stPopover"] > button {
        width: 65px !important;
        height: 65px !important;
        border-radius: 50% !important;
        background-color: #007bff !important;
        color: white !important;
        border: none !important;
        font-size: 30px !important;
    }
    div.element-container:has(#cvs-chatbot-anchor) + div.element-container div[data-testid="stPopoverBody"] {
        position: fixed !important;
        bottom: 110px !important;
        right: 30px !important;
        width: 380px !important;
        height: 550px !important;
        background-color: #1c2128 !important;
        border: 1px solid #30363d !important;
        border-radius: 20px !important;
        padding: 10px !important;
        overflow: hidden !important;
    }
    .stChatFloatingInputContainer {
        background-color: transparent !important;
    }
    div[data-testid="stChatInput"] {
        background-color: #0d1117 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.popover("💬"):
        st.markdown("<h4 style='color:#58a6ff; margin-bottom:10px;'>🏪 편의점 꿀팁봇</h4>", unsafe_allow_html=True)

        chat_container = st.container(height=400)

        for msg in st.session_state.messages:
            with chat_container:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        prompt = st.chat_input("질문을 입력하세요...", key="chatbot_input_unique")

        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)

            if client:
                with chat_container:
                    with st.chat_message("assistant"):
                        placeholder = st.empty()
                        placeholder.markdown("…")

                        df = load_chatbot_data()
                        context = ""

                        if not df.empty:
                            keywords = prompt.split()
                            search_query = "|".join(keywords)
                            filtered_df = df[df['name'].str.contains(search_query, case=False, na=False) |
                                             df['category'].str.contains(search_query, case=False, na=False)]

                            if not filtered_df.empty:
                                target_df = filtered_df.head(20)
                            else:
                                target_df = df.sample(n=min(15, len(df)))

                            for _, row in target_df.iterrows():
                                context += f"[{row['brand']}] {row['name']} | {row['price']}원 | {row['event']} | {row['category']}\n"
                        else:
                            context = "조건에 맞는 행사 상품이 없습니다."

                        system_prompt = (
                            f"당신은 아주 약간의 센스를 기반으로 친절한 편의점 행사 도우미예요.\n"
                            f"사용자가 묻는 질문에 대해 아래 [검색된 데이터]를 참고해서 답변하세요.\n"
                            f"사용자가 포괄적인 단어(예: 음료, 간식 등)를 말하면, 데이터에 있는 구체적인 관련 상품들을 유추하여 최적의 답변을 제공해야 합니다.\n"
                            f"데이터에 '아메리카노'가 있고 사용자가 '커피'를 묻는다면 관련 상품으로 판단하고 답변하세요.\n"
                            f"답변은 자연스럽고 친근하게, 답변은 무조건 한국어만 사용하세요 이외의 언어는 사용하지마세요.\n"
                            f"상품명, 가격, 행사 정보를 한눈에 보기 좋게 정리하세요.\n"
                            f"[검색된 데이터]\n{context}"
                        )

                        full_response = ""
                        try:
                            response = client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    *st.session_state.messages[-5:]
                                ],
                                stream=True,
                                temperature=0.5,
                                top_p=0.9
                            )

                            for chunk in response:
                                if chunk.choices[0].delta.content:
                                    full_response += chunk.choices[0].delta.content
                                    placeholder.markdown(full_response + "▌")

                            placeholder.markdown(full_response)

                        except Exception as e:
                            full_response = f"오류 발생: {e}"
                            placeholder.markdown(full_response)

                        st.session_state.messages.append({"role": "assistant", "content": full_response})
