import streamlit as st
import requests

API_URL = "https://genai-knowledge-api.onrender.com/ask"

st.title("GenAI Knowledge Assistant")

session_id = st.text_input("Session ID", value="user_1")

question = st.text_input("Ask a question")

if st.button("Ask"):

    payload = {
        "question": question,
        "session_id": session_id
    }

    response = requests.post(API_URL, json=payload)

    data = response.json()

    st.subheader("Answer")
    st.write(data["answer"])

    st.subheader("Sources")
    for s in data["sources"]:
        st.write("-", s)
