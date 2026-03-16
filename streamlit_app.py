import streamlit as st
import requests
import time

# -----------------------------
# CONFIG
# -----------------------------

API_BASE = "https://genai-knowledge-api-production.up.railway.app"

ASK_URL = f"{API_BASE}/ask"
UPLOAD_URL = f"{API_BASE}/upload"

st.set_page_config(
    page_title="Enterprise Knowledge Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# PREMIUM UI STYLE
# -----------------------------

st.markdown("""
<style>

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0f1117;
    color: #e6e6e6;
}

.stApp {
    background-color: #0f1117;
}

#MainMenu, footer, header {visibility: hidden;}

section[data-testid="stSidebar"] {
    background-color: #151821;
    border-right: 1px solid #262a36;
}

.sidebar-title {
    font-size: 22px;
    font-weight: 700;
    color: #ffffff;
}

.metric-box {
    background: #1c1f2a;
    border: 1px solid #2a2f3a;
    border-radius: 10px;
    padding: 12px;
    text-align: center;
}

.metric-num {
    font-size: 20px;
    font-weight: 700;
    color: #7c8cff;
}

.metric-label {
    font-size: 10px;
    color: #888;
    text-transform: uppercase;
}

.upload-card {
    background: #1c1f2a;
    border: 1px solid #2a2f3a;
    padding: 15px;
    border-radius: 12px;
}

.source-card {
    background:#1a1c25;
    border-left:3px solid #7c8cff;
    padding:10px;
    border-radius:6px;
    margin-bottom:6px;
    font-size:13px;
}

.response-badge {
    font-size:12px;
    color:#9aa0ff;
    margin-top:6px;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# SESSION STATE
# -----------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "total_questions" not in st.session_state:
    st.session_state.total_questions = 0

if "sources_found" not in st.session_state:
    st.session_state.sources_found = 0

if "total_time" not in st.session_state:
    st.session_state.total_time = 0

if "session_id" not in st.session_state:
    st.session_state.session_id = f"user_{int(time.time())}"

if "uploaded_docs" not in st.session_state:
    st.session_state.uploaded_docs = []

# -----------------------------
# SIDEBAR
# -----------------------------

with st.sidebar:

    st.markdown("<div class='sidebar-title'>🤖 GenAI Assistant</div>", unsafe_allow_html=True)
    st.caption("Enterprise Knowledge Base")

    st.divider()

    # Metrics
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div class="metric-box">
        <div class="metric-num">{st.session_state.total_questions}</div>
        <div class="metric-label">Questions</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-box">
        <div class="metric-num">{len(st.session_state.messages)//2}</div>
        <div class="metric-label">Chats</div>
        </div>
        """, unsafe_allow_html=True)

    if st.session_state.total_questions > 0:
        avg_time = st.session_state.total_time / st.session_state.total_questions

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"""
            <div class="metric-box">
            <div class="metric-num">{avg_time:.1f}s</div>
            <div class="metric-label">Avg Time</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-box">
            <div class="metric-num">{st.session_state.sources_found}</div>
            <div class="metric-label">Sources</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # -----------------------------
    # Upload Section
    # -----------------------------

    st.subheader("Upload Document")

    with st.container():

        uploaded_file = st.file_uploader(
            "Upload PDF or TXT",
            type=["pdf","txt"]
        )

        upload_button = st.button(
            "🚀 Index Document",
            use_container_width=True,
            disabled=uploaded_file is None
        )

        if upload_button:

            with st.spinner("Processing document..."):

                try:

                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type
                        )
                    }

                    response = requests.post(
                        UPLOAD_URL,
                        files=files,
                        timeout=120
                    )

                    if response.status_code == 200:

                        data = response.json()
                        chunks = data.get("total_chunks",0)

                        st.success(f"Indexed {chunks} chunks")

                        if uploaded_file.name not in st.session_state.uploaded_docs:
                            st.session_state.uploaded_docs.append(uploaded_file.name)

                    else:
                        st.error("Upload failed")

                except requests.exceptions.Timeout:
                    st.warning("Upload timeout. Large files take longer.")

                except Exception as e:
                    st.error(str(e))

    if st.session_state.uploaded_docs:

        st.markdown("**Indexed Documents**")

        for doc in st.session_state.uploaded_docs:
            st.write("✓", doc)

    st.caption("Large PDFs are processed page-by-page to stay within free tier limits.")

    st.divider()

    st.write("Session ID")
    st.code(st.session_state.session_id)

    if st.button("Clear Conversation"):

        st.session_state.messages=[]
        st.session_state.total_questions=0
        st.session_state.sources_found=0
        st.session_state.total_time=0
        st.rerun()

    st.divider()

    st.caption("Powered by")
    st.write("• Railway Backend")
    st.write("• Streamlit Cloud")
    st.write("• Pinecone Vector DB")
    st.write("• Gemini Flash")

# -----------------------------
# MAIN HEADER
# -----------------------------

st.title("Enterprise Knowledge Assistant")

st.caption("RAG Pipeline · Vector Search · Guardrails · Document Upload")

# -----------------------------
# CHAT DISPLAY
# -----------------------------

if not st.session_state.messages:

    st.info("Ask questions about company documents or upload new knowledge.")

else:

    for msg in st.session_state.messages:

        with st.chat_message(msg["role"]):

            st.markdown(msg["content"])

            if msg["role"]=="assistant":

                if msg.get("response_time"):

                    st.markdown(
                        f"<div class='response-badge'>⚡ {msg['response_time']:.2f}s · {msg['source_count']} sources</div>",
                        unsafe_allow_html=True
                    )

                if msg.get("sources"):

                    with st.expander("Sources"):

                        for src in msg["sources"]:
                            st.markdown(
                                f"<div class='source-card'>{src}</div>",
                                unsafe_allow_html=True
                            )

# -----------------------------
# CHAT INPUT
# -----------------------------

question = st.chat_input("Ask about documents...")

if question:

    st.session_state.total_questions +=1

    st.session_state.messages.append({
        "role":"user",
        "content":question
    })

    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):

        with st.spinner("Searching knowledge base..."):

            try:

                start=time.time()

                payload={
                    "question":question,
                    "session_id":st.session_state.session_id
                }

                response=requests.post(
                    ASK_URL,
                    json=payload,
                    timeout=30
                )

                elapsed=time.time()-start

                if response.status_code==200:

                    data=response.json()

                    answer=data.get("answer")
                    sources=data.get("sources",[])

                    st.session_state.total_time+=elapsed
                    st.session_state.sources_found+=len(sources)

                    st.write(answer)

                    st.markdown(
                        f"<div class='response-badge'>⚡ {elapsed:.2f}s · {len(sources)} sources</div>",
                        unsafe_allow_html=True
                    )

                    if sources:

                        with st.expander("Sources"):

                            for src in sources:
                                st.markdown(
                                    f"<div class='source-card'>{src}</div>",
                                    unsafe_allow_html=True
                                )

                    st.session_state.messages.append({
                        "role":"assistant",
                        "content":answer,
                        "sources":sources,
                        "response_time":elapsed,
                        "source_count":len(sources)
                    })

                else:

                    st.error("API error")

            except requests.exceptions.Timeout:
                st.warning("Backend timeout. Try again.")

            except Exception as e:
                st.error(str(e))