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
# Premium CSS — Deep Navy Editorial Theme
# ------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,400;0,9..144,600;1,9..144,300&family=Outfit:wght@300;400;500;600;700&display=swap');

/* ============ RESET & BASE ============ */
html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
    background-color: #05060f;
    color: #dde1f0;
}

.stApp {
    background: #05060f;
    background-image:
        radial-gradient(ellipse 80% 50% at 20% 0%, rgba(99,102,241,0.07) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 100%, rgba(16,185,129,0.05) 0%, transparent 50%);
    min-height: 100vh;
}

/* ============ HIDE DEFAULTS ============ */
#MainMenu, footer { visibility: hidden; }
header { visibility: hidden; }
.stDeployButton { display: none; }

/* ============ SIDEBAR TOGGLE — ALWAYS VISIBLE ============ */
[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    position: fixed !important;
    top: 0.6rem !important;
    left: 0.6rem !important;
    z-index: 999999 !important;
    background: #0d0e1f !important;
    border: 1px solid #1a1b35 !important;
    border-radius: 8px !important;
    padding: 0.3rem !important;
    color: #818cf8 !important;
}

/* ============ SIDEBAR ============ */
section[data-testid="stSidebar"] {
    background: #0a0b1a !important;
    border-right: 1px solid #131428 !important;
}

section[data-testid="stSidebar"] * {
    color: #dde1f0 !important;
}

section[data-testid="stSidebar"] .stFileUploader {
    background: #0d0e20 !important;
    border: 1px dashed #1e2040 !important;
    border-radius: 10px !important;
}

/* ============ SIDEBAR BRAND ============ */
.sidebar-brand {
    padding: 1.2rem 0 0.8rem 0;
}

.sidebar-brand-name {
    font-family: 'Fraunces', serif;
    font-weight: 600;
    font-size: 1.15rem;
    color: #e0e4ff;
    letter-spacing: -0.02em;
}

.sidebar-brand-tag {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    color: #2e3158;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-top: 0.25rem;
}

/* ============ METRIC CARDS ============ */
.metric-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.4rem;
    margin: 0.4rem 0;
}

.metric-card {
    background: #0d0e20;
    border: 1px solid #131428;
    border-radius: 10px;
    padding: 0.8rem 0.6rem;
    text-align: center;
}

.metric-card.full {
    grid-column: 1 / -1;
}

.metric-value {
    font-family: 'Fraunces', serif;
    font-weight: 600;
    font-size: 1.6rem;
    color: #818cf8;
    line-height: 1;
}

.metric-value.green { color: #10b981; }
.metric-value.blue  { color: #38bdf8; }

.metric-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.6rem;
    color: #2e3158;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.3rem;
}

/* ============ UPLOAD SECTION ============ */
.upload-section-title {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    color: #818cf8;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin: 0.8rem 0 0.4rem 0;
}

.upload-note {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    color: #1e2245;
    background: #0a0b1a;
    border: 1px solid #131428;
    border-left: 2px solid #1e2a5e;
    border-radius: 6px;
    padding: 0.6rem 0.8rem;
    margin-top: 0.5rem;
    line-height: 1.8;
}

.indexed-doc {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    color: #10b981;
    margin: 0.15rem 0;
}

/* ============ POWERED BY ============ */
.powered-by {
    font-family: 'DM Mono', monospace;
    font-size: 0.62rem;
    color: #1a1d3a;
    line-height: 2;
}

.powered-by span {
    color: #252850;
}

/* ============ SESSION ID ============ */
.session-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.62rem;
    color: #1e2245;
    line-height: 1.8;
}

.session-value {
    color: #2a2f5e;
    word-break: break-all;
}

/* ============ DIVIDER ============ */
.sidebar-divider {
    border: none;
    border-top: 1px solid #0f1025;
    margin: 0.8rem 0;
}

/* ============ MAIN HEADER ============ */
.app-header {
    padding: 2.5rem 0 2rem 0;
    border-bottom: 1px solid #0f1025;
    margin-bottom: 2rem;
    position: relative;
}

.app-header-eyebrow {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    color: #818cf8;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    margin-bottom: 0.6rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.app-title {
    font-family: 'Fraunces', serif;
    font-weight: 300;
    font-style: italic;
    font-size: 2.8rem;
    letter-spacing: -0.04em;
    color: #e8eaff;
    margin: 0;
    line-height: 1.05;
}

.app-title strong {
    font-weight: 600;
    font-style: normal;
    background: linear-gradient(135deg, #818cf8, #38bdf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.app-subtitle {
    font-family: 'Outfit', sans-serif;
    font-size: 0.85rem;
    color: #2e3158;
    margin-top: 0.8rem;
    font-weight: 300;
}

/* ============ STATUS DOT ============ */
.status-dot {
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #10b981;
    animation: blink 2.5s ease-in-out infinite;
}

@keyframes blink {
    0%, 100% { opacity: 1; box-shadow: 0 0 4px #10b981; }
    50% { opacity: 0.3; box-shadow: none; }
}

/* ============ EMPTY STATE ============ */
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 5rem 2rem;
    text-align: center;
}

.empty-state-glyph {
    font-family: 'Fraunces', serif;
    font-size: 3.5rem;
    color: #0f1025;
    margin-bottom: 1.5rem;
    line-height: 1;
}

.empty-state-title {
    font-family: 'Fraunces', serif;
    font-weight: 300;
    font-style: italic;
    font-size: 1.4rem;
    color: #1a1d3a;
    margin-bottom: 0.5rem;
}

.empty-state-hint {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    color: #131428;
    letter-spacing: 0.05em;
}

/* ============ CHAT MESSAGES ============ */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 0.3rem 0 !important;
}

/* ============ RESPONSE BADGE ============ */
.response-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.6rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    color: #1e2245;
    background: #0a0b1a;
    border: 1px solid #0f1025;
    border-radius: 20px;
    padding: 0.25rem 0.8rem;
    margin-top: 0.5rem;
}

.badge-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: #10b981;
    flex-shrink: 0;
}

/* ============ SOURCE CARD ============ */
.source-card {
    background: #080915;
    border: 1px solid #0f1025;
    border-left: 2px solid #818cf8;
    border-radius: 8px;
    padding: 0.9rem 1.1rem;
    margin: 0.5rem 0;
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    color: #2a2f5e;
    line-height: 1.7;
}

.source-card-label {
    font-size: 0.6rem;
    color: #818cf8;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.5rem;
    display: block;
}

.source-card-text {
    color: #3a4070;
}

/* ============ CHAT INPUT ============ */
[data-testid="stChatInput"] {
    background: #0a0b1a !important;
    border: 1px solid #131428 !important;
    border-radius: 14px !important;
}

[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: #dde1f0 !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.9rem !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: #1a1d3a !important;
}

/* ============ EXPANDER ============ */
.streamlit-expanderHeader {
    background: #0a0b1a !important;
    border: 1px solid #0f1025 !important;
    border-radius: 8px !important;
    color: #2e3158 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.7rem !important;
}

.streamlit-expanderContent {
    background: #080915 !important;
    border: 1px solid #0f1025 !important;
    border-top: none !important;
    border-radius: 0 0 8px 8px !important;
}

/* ============ BUTTONS ============ */
.stButton > button {
    background: #0d0e20 !important;
    border: 1px solid #131428 !important;
    color: #4a5080 !important;
    font-family: 'DM Mono', monospace !important;
    border-radius: 8px !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.03em !important;
    transition: all 0.2s ease !important;
    padding: 0.5rem 1rem !important;
}

.stButton > button:hover {
    border-color: #818cf8 !important;
    color: #818cf8 !important;
    background: #0d0e20 !important;
}

/* ============ FILE UPLOADER ============ */
[data-testid="stFileUploader"] {
    background: #0a0b1a !important;
}

[data-testid="stFileUploaderDropzone"] {
    background: #0a0b1a !important;
    border: 1px dashed #131428 !important;
    border-radius: 10px !important;
}

/* ============ SUCCESS / ERROR / WARNING ============ */
[data-testid="stAlert"] {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.75rem !important;
    border-radius: 8px !important;
}

/* ============ SPINNER ============ */
.stSpinner > div {
    border-top-color: #818cf8 !important;
}

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
    st.session_state.session_id = f"sess_{int(time.time())}"

if "uploaded_docs" not in st.session_state:
    st.session_state.uploaded_docs = []


# ------------------------------------------------
# Sidebar
# ------------------------------------------------

with st.sidebar:

    # Brand
    st.markdown("""
    <div class='sidebar-brand'>
        <div class='sidebar-brand-name'>⬡ GenAI Assistant</div>
        <div class='sidebar-brand-tag'>Enterprise Knowledge Base</div>
    </div>
    <hr class='sidebar-divider'>
    """, unsafe_allow_html=True)

    # Metrics — row 1
    st.markdown(f"""
    <div class='metric-row'>
        <div class='metric-card'>
            <div class='metric-value'>{st.session_state.total_questions}</div>
            <div class='metric-label'>Questions</div>
        </div>
        <div class='metric-card'>
            <div class='metric-value blue'>{len(st.session_state.messages) // 2}</div>
            <div class='metric-label'>Exchanges</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Metrics — row 2 (live after first question)
    if st.session_state.total_questions > 0:
        avg_time = st.session_state.total_time / st.session_state.total_questions
        st.markdown(f"""
        <div class='metric-row'>
            <div class='metric-card'>
                <div class='metric-value green'>{avg_time:.1f}s</div>
                <div class='metric-label'>Avg Time</div>
            </div>
            <div class='metric-card'>
                <div class='metric-value'>{st.session_state.sources_found}</div>
                <div class='metric-label'>Sources</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr class='sidebar-divider'>", unsafe_allow_html=True)

    # Upload section
    st.markdown("<div class='upload-section-title'>Upload Document</div>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload",
        type=["pdf", "txt"],
        label_visibility="collapsed"
    )

    if uploaded_file:
        if st.button("⬆  Index Document", use_container_width=True):
            with st.spinner("Indexing..."):
                try:
                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type
                        )
                    }
                    response = requests.post(UPLOAD_URL, files=files, timeout=120)

                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"✅ {data['total_chunks']} chunks indexed")
                        if uploaded_file.name not in st.session_state.uploaded_docs:
                            st.session_state.uploaded_docs.append(uploaded_file.name)
                    else:
                        st.error(f"Failed: {response.status_code}")

                except requests.exceptions.Timeout:
                    st.warning("⏱ Timeout — large docs take longer, try again.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    # Indexed docs this session
    if st.session_state.uploaded_docs:
        docs_html = "".join([
            f"<div class='indexed-doc'>✓ {d}</div>"
            for d in st.session_state.uploaded_docs
        ])
        st.markdown(f"""
        <div style='margin-top: 0.5rem;'>
            <div style='font-family: DM Mono, monospace; font-size: 0.6rem;
                        color: #1a1d3a; text-transform: uppercase;
                        letter-spacing: 0.1em; margin-bottom: 0.3rem;'>
                Indexed this session
            </div>
            {docs_html}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class='upload-note'>
        Large files processed page-by-page<br>
        to stay within free-tier memory limits.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr class='sidebar-divider'>", unsafe_allow_html=True)

    # Session ID
    st.markdown(f"""
    <div class='session-label'>
        SESSION ID<br>
        <span class='session-value'>{st.session_state.session_id}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("↺  Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.total_questions = 0
        st.session_state.total_time = 0.0
        st.session_state.sources_found = 0
        st.session_state.session_id = f"sess_{int(time.time())}"
        st.rerun()

    st.markdown("<hr class='sidebar-divider'>", unsafe_allow_html=True)

    # Powered by
    st.markdown("""
    <div class='powered-by'>
        POWERED BY<br>
        <span>Railway — Backend API</span><br>
        <span>Streamlit Cloud — Frontend</span><br>
        <span>Pinecone — Vector DB</span><br>
        <span>Gemini Embedding 001</span>
    </div>
    """, unsafe_allow_html=True)


# ------------------------------------------------
# Main Header
# ------------------------------------------------

st.markdown("""
<div class='app-header'>
    <div class='app-header-eyebrow'>
        <span class='status-dot'></span>
        Live · RAG Pipeline Active
    </div>
    <h1 class='app-title'>Enterprise <strong>Knowledge</strong></h1>
    <h1 class='app-title'>Assistant</h1>
    <div class='app-subtitle'>
        Vector Search · Guardrails · Conversational Memory · Document Upload
    </div>
</div>
""", unsafe_allow_html=True)


# ------------------------------------------------
# Chat Display
# ------------------------------------------------

if not st.session_state.messages:
    st.markdown("""
    <div class='empty-state'>
        <div class='empty-state-glyph'>◈</div>
        <div class='empty-state-title'>Nothing yet — ask something</div>
        <div class='empty-state-hint'>
            Query the knowledge base · Upload a document · Start a conversation
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message["role"] == "assistant":
                rt = message.get("response_time", 0)
                sc = message.get("source_count", 0)
                if rt:
                    st.markdown(f"""
                    <div class='response-badge'>
                        <span class='badge-dot'></span>
                        {rt:.2f}s &nbsp;·&nbsp; {sc} source{'s' if sc != 1 else ''}
                    </div>
                    """, unsafe_allow_html=True)

                if message.get("sources"):
                    with st.expander(f"📎 {len(message['sources'])} source(s)"):
                        for i, src in enumerate(message["sources"], 1):
                            st.markdown(f"""
                            <div class='source-card'>
                                <span class='source-card-label'>chunk · {i:02d}</span>
                                <div class='source-card-text'>{src}</div>
                            </div>
                            """, unsafe_allow_html=True)


# ------------------------------------------------
# Chat Input
# ------------------------------------------------

question = st.chat_input("Ask about policies, procedures, or uploaded documents...")

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
        with st.spinner(""):
            try:
                start_time = time.time()

                payload = {
                    "question": question,
                    "session_id": st.session_state.session_id
                }

                response = requests.post(
                    ASK_URL,
                    json=payload,
                    timeout=30
                )

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
                        <span class='badge-dot'></span>
                        {elapsed:.2f}s &nbsp;·&nbsp; {len(sources)} source{'s' if len(sources) != 1 else ''}
                    </div>
                    """, unsafe_allow_html=True)

                    if sources:
                        with st.expander(f"📎 {len(sources)} source(s)"):
                            for i, src in enumerate(sources, 1):
                                st.markdown(f"""
                                <div class='source-card'>
                                    <span class='source-card-label'>chunk · {i:02d}</span>
                                    <div class='source-card-text'>{src}</div>
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
                    msg = f"API returned {response.status_code}. Please try again."
                    st.error(msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": msg,
                        "sources": [],
                        "response_time": 0,
                        "source_count": 0
                    })

            except requests.exceptions.Timeout:
                msg = "⏱ Timed out. Backend may be waking up — please try again in a moment."
                st.warning(msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": msg,
                    "sources": [],
                    "response_time": 0,
                    "source_count": 0
                })

            except requests.exceptions.ConnectionError:
                msg = "🔌 Cannot reach the backend. Please check if the server is running."
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