import streamlit as st
import requests

API_URL = "https://genai-knowledge-assistant.onrender.com/ask"

st.set_page_config(
    page_title="Enterprise GenAI Assistant",
    page_icon="🤖",
    layout="wide"
)

st.title("Enterprise GenAI Assistant")
st.write("Ask questions about company policies.")

# session id
session_id = "streamlit_user"

# chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# user input
question = st.chat_input("Ask a question about company policies")

if question:

    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    payload = {
        "question": question,
        "session_id": session_id
    }

    response = requests.post(API_URL, json=payload)

    if response.status_code == 200:

        data = response.json()
        answer = data["answer"]

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

        with st.chat_message("assistant"):
            st.markdown(answer)

        # show sources
        with st.expander("Sources"):
            for src in data["sources"]:
                st.write(src)

    else:
        st.error("API error")