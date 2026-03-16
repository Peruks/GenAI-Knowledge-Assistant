import streamlit as st
import requests
import time

# ------------------------------------------------
# Configuration
# ------------------------------------------------

API_BASE = "https://genai-knowledge-api-production.up.railway.app"
ASK_URL = f"{API_BASE}/ask"
UPLOAD_URL = f"{API_BASE}/upload"

st.set_page_config(
    page_title="Enterprise GenAI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------
# Custom CSS
# ------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Syne:wght@400;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
    background-color: #0a0a0f;
    color: #e8e8f0;
}

.stApp { background: #0a0a0f; }

#MainMenu, footer { visibility: hidden; }
header { visibility: hidden; }

/* Always show sidebar toggle button */
button[kind="headerNominal"],
[data-testid="collapsedControl"] {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    color: #a78bfa !important;
}
.stDeployButton { display: none; }

section[data-testid="stSidebar"] {
    background: #0f0f1a !important;
    border-right: 1px solid #1e1e2e;
}

section[data-testid="stSidebar"] * {
    color: #e8e8f0 !important;
}

.app-header {
    padding: 2rem 0 1.5rem 0;
    border-bottom: 1px solid #1e1e2e;
    margin-bottom: 2rem;
}

.app-title {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 2rem;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, #ffffff 0%, #a78bfa 50%, #60a5fa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    line-height: 1.1;
}

.app-subtitle {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    color: #4a4a6a;
    margin-top: 0.4rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

.status-dot {
    display: inline-block;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #22c55e;
    margin-right: 6px;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

.metric-card {
    background: #13131f;
    border: 1px solid #1e1e2e;
    border-radius: 10px;
    padding: 1rem;
    margin: 0.5rem 0;
    text-align: center;
}

.metric-value {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 1.8rem;
    color: #a78bfa;
}

.metric-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: #4a4a6a;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.2rem;
}

.source-card {
    background: #0a0a0f;
    border: 1px solid #1e1e2e;
    border-left: 3px solid #6366f1;
    border-radius: 6px;
    padding: 0.8rem 1rem;
    margin: 0.5rem 0;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    color: #9090b0;
    line-height: 1.6;
}

.response-badge {
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    color: #4a4a6a;
    background: #0f0f1a;
    border: 1px solid #1e1e2e;
    border-radius: 20px;
    padding: 0.2rem 0.7rem;
    margin-top: 0.5rem;
}

.upload-info {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: #3a3a5a;
    background: #0f0f1a;
    border: 1px solid #1e1e2e;
    border-radius: 8px;
    padding: 0.8rem;
    margin-top: 0.5rem;
    line-height: 1.7;
}

.empty-state {
    text-align: center;
    padding: 4rem 2rem;
}

.empty-state-icon { font-size: 3rem; margin-bottom: 1rem; }

.empty-state-text {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem;
    color: #3a3a5a;
}

.empty-state-hint {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    color: #2a2a4a;
    margin-top: 0.5rem;
}

.stChatInput textarea {
    background: #13131f !important;
    color: #e8e8f0 !important;
    font-family: 'Syne', sans-serif !important;
    border: 1px solid #1e1e2e !important;
}

.streamlit-expanderHeader {
    background: #0f0f1a !important;
    border: 1px solid #1e1e2e !important;
    border-radius: 8px !important;
    color: #6366f1 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.75rem !important;
}

.streamlit-expanderContent {
    background: #0f0f1a !important;
    border: 1px solid #1e1e2e !important;
    border-top: none !important;
}

.stButton > button {
    background: #13131f !important;
    border: 1px solid #1e1e2e !important;
    color: #e8e8f0 !important;
    font-family: 'Syne', sans-serif !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
    transition: all 0.2s !important;
}

.stButton > button:hover {
    border-color: #6366f1 !important;
    color: #a78bfa !important;
}

.stSpinner > div { border-top-color: #6366f1 !important; }

</style>
""", unsafe_allow_html=True)


# ------------------------------------------------
# Session State Init
# ------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "total_questions" not in st.session_state:
    st.session_state.total_questions = 0

if "total_time" not in st.session_state:
    st.session_state.total_time = 0.0

if "sources_found" not in st.session_state:
    st.session_state.sources_found = 0

if "session_id" not in st.session_state:
    st.session_state.session_id = f"user_{int(time.time())}"

if "uploaded_docs" not in st.session_state:
    st.session_state.uploaded_docs = []


# ------------------------------------------------
# Sidebar
# ------------------------------------------------

with st.sidebar:

    st.markdown("""
    <div style='padding: 1rem 0 0.5rem 0;'>
        <div style='font-family: Syne, sans-serif; font-weight: 800; font-size: 1.1rem; color: #e8e8f0;'>
            ⬡ GenAI Assistant
        </div>
        <div style='font-family: IBM Plex Mono, monospace; font-size: 0.7rem; color: #4a4a6a;
                    text-transform: uppercase; letter-spacing: 0.08em; margin-top: 0.3rem;'>
            Enterprise Knowledge Base
        </div>
    </div>
    <hr style='border-color: #1e1e2e; margin: 0.8rem 0;'>
    """, unsafe_allow_html=True)

    # ---- Metrics ----
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-value'>{st.session_state.total_questions}</div>
        <div class='metric-label'>Questions Asked</div>
    </div>
    <div class='metric-card'>
        <div class='metric-value'>{len(st.session_state.messages) // 2}</div>
        <div class='metric-label'>Conversations</div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.total_questions > 0:
        avg_time = st.session_state.total_time / st.session_state.total_questions
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{avg_time:.1f}s</div>
            <div class='metric-label'>Avg Response Time</div>
        </div>
        <div class='metric-card'>
            <div class='metric-value'>{st.session_state.sources_found}</div>
            <div class='metric-label'>Sources Retrieved</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color: #1e1e2e; margin: 1rem 0;'>", unsafe_allow_html=True)

    # ---- Document Upload ----
    st.markdown("""
    <div style='font-family: IBM Plex Mono, monospace; font-size: 0.72rem;
                color: #6366f1; text-transform: uppercase; letter-spacing: 0.08em;
                margin-bottom: 0.5rem;'>
        Upload Document
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload PDF or TXT",
        type=["pdf", "txt"],
        label_visibility="collapsed"
    )

    if uploaded_file:
        if st.button("⬆  Index Document", use_container_width=True):
            with st.spinner("Indexing document..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(UPLOAD_URL, files=files, timeout=120)

                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"✅ Indexed {data['total_chunks']} chunks")
                        st.session_state.uploaded_docs.append(uploaded_file.name)
                    else:
                        st.error(f"Upload failed: {response.status_code}")

                except requests.exceptions.Timeout:
                    st.warning("⏱ Upload timed out. Large documents take longer — try again.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    # Show uploaded docs this session
    if st.session_state.uploaded_docs:
        st.markdown(f"""
        <div style='font-family: IBM Plex Mono, monospace; font-size: 0.68rem;
                    color: #3a3a5a; margin-top: 0.5rem;'>
            INDEXED THIS SESSION<br>
            {'<br>'.join([f"<span style='color:#4a4a6a;'>✓ {d}</span>" for d in st.session_state.uploaded_docs])}
        </div>
        """, unsafe_allow_html=True)

    # Upload info note
    st.markdown("""
    <div class='upload-info'>
        Large documents are processed<br>
        incrementally (page-by-page) to<br>
        stay stable within free-tier limits.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color: #1e1e2e; margin: 1rem 0;'>", unsafe_allow_html=True)

    # ---- Session ----
    st.markdown(f"""
    <div style='font-family: IBM Plex Mono, monospace; font-size: 0.7rem; color: #3a3a5a;'>
        SESSION<br>
        <span style='color: #4a4a6a;'>{st.session_state.session_id}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("↺  Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.total_questions = 0
        st.session_state.total_time = 0.0
        st.session_state.sources_found = 0
        st.session_state.session_id = f"user_{int(time.time())}"
        st.rerun()

    st.markdown("<hr style='border-color: #1e1e2e; margin: 1rem 0;'>", unsafe_allow_html=True)

    # ---- Powered by ----
    st.markdown("""
    <div style='font-family: IBM Plex Mono, monospace; font-size: 0.68rem; color: #2a2a4a; line-height: 1.8;'>
        POWERED BY<br>
        <span style='color: #3a3a6a;'>Render — Backend API</span><br>
        <span style='color: #3a3a6a;'>Streamlit Cloud — Frontend</span><br>
        <span style='color: #3a3a6a;'>Pinecone — Vector DB</span><br>
        <span style='color: #3a3a6a;'>Gemini Embedding 001</span>
    </div>
    """, unsafe_allow_html=True)


# ------------------------------------------------
# Main Header
# ------------------------------------------------

st.markdown("""
<div class='app-header'>
    <h1 class='app-title'>Enterprise Knowledge Assistant</h1>
    <div class='app-subtitle'>
        <span class='status-dot'></span>RAG Pipeline · Vector Search · Guardrails
    </div>
</div>
""", unsafe_allow_html=True)


# ------------------------------------------------
# Chat Display
# ------------------------------------------------

if not st.session_state.messages:
    st.markdown("""
    <div class='empty-state'>
        <div class='empty-state-icon'>◈</div>
        <div class='empty-state-text'>Ask anything about company policies</div>
        <div class='empty-state-hint'>
            Upload a document from the sidebar or ask about existing knowledge base
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message["role"] == "assistant" and message.get("response_time"):
                st.markdown(f"""
                <div class='response-badge'>
                    ⚡ {message['response_time']:.2f}s response
                    &nbsp;·&nbsp;
                    📎 {message.get('source_count', 0)} sources
                </div>
                """, unsafe_allow_html=True)

            if message["role"] == "assistant" and message.get("sources"):
                with st.expander(f"📎 {len(message['sources'])} source(s) retrieved"):
                    for i, src in enumerate(message["sources"], 1):
                        st.markdown(f"""
                        <div class='source-card'>
                            <span style='color: #6366f1; font-weight: 500;'>chunk_{i:02d}</span><br><br>
                            {src}
                        </div>
                        """, unsafe_allow_html=True)


# ------------------------------------------------
# Chat Input
# ------------------------------------------------

question = st.chat_input("Ask about company policies, procedures, or uploaded documents...")

if question:

    st.session_state.messages.append({
        "role": "user",
        "content": question,
        "sources": []
    })

    st.session_state.total_questions += 1

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching knowledge base..."):
            try:
                start_time = time.time()

                payload = {
                    "question": question,
                    "session_id": st.session_state.session_id
                }

                response = requests.post(ASK_URL, json=payload, timeout=30)

                elapsed = time.time() - start_time

                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "No answer returned.")
                    sources = data.get("sources", [])

                    st.session_state.total_time += elapsed
                    st.session_state.sources_found += len(sources)

                    st.markdown(answer)

                    st.markdown(f"""
                    <div class='response-badge'>
                        ⚡ {elapsed:.2f}s response
                        &nbsp;·&nbsp;
                        📎 {len(sources)} sources
                    </div>
                    """, unsafe_allow_html=True)

                    if sources:
                        with st.expander(f"📎 {len(sources)} source(s) retrieved"):
                            for i, src in enumerate(sources, 1):
                                st.markdown(f"""
                                <div class='source-card'>
                                    <span style='color: #6366f1; font-weight: 500;'>chunk_{i:02d}</span><br><br>
                                    {src}
                                </div>
                                """, unsafe_allow_html=True)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                        "response_time": elapsed,
                        "source_count": len(sources)
                    })

                else:
                    error_msg = f"API returned status {response.status_code}. Please try again."
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "sources": [],
                        "response_time": 0,
                        "source_count": 0
                    })

            except requests.exceptions.Timeout:
                msg = "⏱ Request timed out. The backend may be starting up — please try again."
                st.warning(msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": msg,
                    "sources": [],
                    "response_time": 0,
                    "source_count": 0
                })

            except requests.exceptions.ConnectionError:
                msg = "🔌 Could not connect to the backend API. Please check if the server is running."
                st.error(msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": msg,
                    "sources": [],
                    "response_time": 0,
                    "source_count": 0
                })

            except Exception as e:
                msg = f"Unexpected error: {str(e)}"
                st.error(msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": msg,
                    "sources": [],
                    "response_time": 0,
                    "source_count": 0
                })