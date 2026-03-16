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
# CSS — Rich Dark Slate Theme, High Contrast
# ------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap');

/* ======== BASE ======== */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background-color: #0c0e1a !important;
    color: #c8cde8 !important;
}

.stApp {
    background: #0c0e1a !important;
    background-image:
        radial-gradient(ellipse 70% 40% at 0% 0%, rgba(139,92,246,0.08) 0%, transparent 55%),
        radial-gradient(ellipse 50% 35% at 100% 100%, rgba(34,211,238,0.06) 0%, transparent 50%);
}

/* ======== HEADER — make toggle visible ======== */
header {
    background: transparent !important;
}

header * {
    visibility: hidden !important;
}

/* Only show the sidebar collapse button */
header [data-testid="collapsedControl"],
header [data-testid="collapsedControl"] * {
    visibility: visible !important;
}

[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    z-index: 999999 !important;
    background: #161828 !important;
    border: 1px solid #2a2d4a !important;
    border-radius: 10px !important;
    color: #a78bfa !important;
}

[data-testid="collapsedControl"] svg {
    color: #a78bfa !important;
    fill: #a78bfa !important;
}

#MainMenu, footer { visibility: hidden !important; }
.stDeployButton { display: none !important; }

/* ======== SIDEBAR ======== */
section[data-testid="stSidebar"] {
    background: #10121f !important;
    border-right: 1px solid #1e2038 !important;
    padding-top: 1rem !important;
}

section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] label {
    color: #c8cde8 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

/* ======== METRIC CARDS ======== */
.metric-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin: 8px 0;
}

.metric-box {
    background: #161828;
    border: 1px solid #1e2038;
    border-radius: 12px;
    padding: 14px 10px;
    text-align: center;
}

.metric-num {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 800;
    font-size: 1.7rem;
    line-height: 1;
    color: #a78bfa;
}

.metric-num.teal  { color: #22d3ee; }
.metric-num.green { color: #34d399; }
.metric-num.amber { color: #fbbf24; }

.metric-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.58rem;
    font-weight: 400;
    color: #4a4f7a;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 5px;
}

/* ======== SIDEBAR SECTION LABEL ======== */
.sb-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    font-weight: 500;
    color: #a78bfa;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin: 16px 0 6px 0;
}

.sb-divider {
    border: none;
    border-top: 1px solid #1a1c30;
    margin: 14px 0;
}

/* ======== UPLOAD NOTE ======== */
.upload-note {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    color: #3a4070;
    background: #0e1020;
    border: 1px solid #1a1c30;
    border-left: 2px solid #4338ca;
    border-radius: 6px;
    padding: 8px 10px;
    margin-top: 8px;
    line-height: 1.9;
}

/* ======== INDEXED DOCS ======== */
.doc-item {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: #34d399;
    padding: 2px 0;
}

/* ======== SESSION ======== */
.session-box {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    color: #2e3358;
    line-height: 1.9;
    background: #0e1020;
    border: 1px solid #1a1c30;
    border-radius: 8px;
    padding: 8px 10px;
}

.session-box .val {
    color: #3d4275;
    word-break: break-all;
}

/* ======== POWERED BY ======== */
.powered {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    line-height: 2;
    color: #252840;
}

.powered .pill {
    display: inline-block;
    background: #161828;
    border: 1px solid #1e2038;
    border-radius: 20px;
    padding: 1px 8px;
    color: #3a3f6a;
    margin: 1px 0;
}

/* ======== MAIN HEADER ======== */
.main-header {
    padding: 2rem 0 1.8rem 0;
    border-bottom: 1px solid #1a1c30;
    margin-bottom: 2rem;
}

.header-eyebrow {
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    font-weight: 400;
    color: #6366f1;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    margin-bottom: 12px;
}

.live-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #34d399;
    display: inline-block;
    animation: livepulse 2s ease-in-out infinite;
}

@keyframes livepulse {
    0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(52,211,153,0.4); }
    50% { opacity: 0.6; box-shadow: 0 0 0 4px rgba(52,211,153,0); }
}

.main-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 800;
    font-size: 2.6rem;
    letter-spacing: -0.04em;
    color: #e8eaff;
    line-height: 1.1;
    margin: 0;
}

.main-title .accent {
    background: linear-gradient(90deg, #a78bfa 0%, #22d3ee 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.header-tags {
    margin-top: 10px;
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}

.header-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.62rem;
    color: #3a3f6a;
    background: #161828;
    border: 1px solid #1e2038;
    border-radius: 20px;
    padding: 3px 10px;
}

/* ======== EMPTY STATE ======== */
.empty-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 5rem 2rem;
    text-align: center;
}

.empty-icon {
    font-size: 2.5rem;
    margin-bottom: 1.2rem;
    opacity: 0.15;
}

.empty-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 700;
    font-size: 1.2rem;
    color: #2e3358;
    margin-bottom: 6px;
}

.empty-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: #1e2245;
    letter-spacing: 0.04em;
}

/* ======== RESPONSE BADGE ======== */
.resp-badge {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: #3a4070;
    background: #0e1020;
    border: 1px solid #1a1c30;
    border-radius: 20px;
    padding: 4px 12px;
    margin-top: 8px;
}

.resp-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: #34d399;
    flex-shrink: 0;
}

/* ======== SOURCE CARD ======== */
.src-card {
    background: #0c0e1a;
    border: 1px solid #1a1c30;
    border-left: 3px solid #6366f1;
    border-radius: 8px;
    padding: 12px 14px;
    margin: 6px 0;
}

.src-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.58rem;
    font-weight: 500;
    color: #6366f1;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 6px;
}

.src-text {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: #4a4f7a;
    line-height: 1.7;
}

/* ======== CHAT INPUT ======== */
[data-testid="stChatInput"] {
    background: #161828 !important;
    border: 1px solid #2a2d4a !important;
    border-radius: 14px !important;
}

[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: #c8cde8 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.92rem !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: #2a2d4a !important;
}

/* ======== EXPANDER ======== */
.streamlit-expanderHeader {
    background: #10121f !important;
    border: 1px solid #1e2038 !important;
    border-radius: 8px !important;
    color: #4a4f7a !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.68rem !important;
}

.streamlit-expanderContent {
    background: #0e1020 !important;
    border: 1px solid #1e2038 !important;
    border-top: none !important;
}

/* ======== BUTTONS ======== */
.stButton > button {
    background: #161828 !important;
    border: 1px solid #2a2d4a !important;
    color: #6b7280 !important;
    font-family: 'JetBrains Mono', monospace !important;
    border-radius: 10px !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.03em !important;
    padding: 8px 16px !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    border-color: #a78bfa !important;
    color: #a78bfa !important;
    background: #1a1c30 !important;
}

/* ======== FILE UPLOADER ======== */
[data-testid="stFileUploaderDropzone"] {
    background: #10121f !important;
    border: 1px dashed #2a2d4a !important;
    border-radius: 10px !important;
    color: #4a4f7a !important;
}

[data-testid="stFileUploaderDropzone"] * {
    color: #4a4f7a !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.72rem !important;
}

/* ======== ALERTS ======== */
[data-testid="stAlert"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.72rem !important;
    border-radius: 8px !important;
}

/* ======== SPINNER ======== */
.stSpinner > div {
    border-top-color: #a78bfa !important;
}

/* ======== CHAT MESSAGES ======== */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
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
    <div style='padding: 0.5rem 0 0.2rem 0;'>
        <div style='font-family: Plus Jakarta Sans, sans-serif; font-weight: 800;
                    font-size: 1.05rem; color: #e8eaff; letter-spacing: -0.02em;'>
            ⬡ &nbsp;GenAI Assistant
        </div>
        <div style='font-family: JetBrains Mono, monospace; font-size: 0.6rem;
                    color: #2e3358; text-transform: uppercase;
                    letter-spacing: 0.12em; margin-top: 4px;'>
            Enterprise Knowledge Base
        </div>
    </div>
    <hr class='sb-divider'>
    """, unsafe_allow_html=True)

    # Metrics row 1
    st.markdown(f"""
    <div class='metric-grid'>
        <div class='metric-box'>
            <div class='metric-num'>{st.session_state.total_questions}</div>
            <div class='metric-tag'>Questions</div>
        </div>
        <div class='metric-box'>
            <div class='metric-num teal'>{len(st.session_state.messages) // 2}</div>
            <div class='metric-tag'>Exchanges</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Metrics row 2 — live after first question
    if st.session_state.total_questions > 0:
        avg = st.session_state.total_time / st.session_state.total_questions
        st.markdown(f"""
        <div class='metric-grid'>
            <div class='metric-box'>
                <div class='metric-num green'>{avg:.1f}s</div>
                <div class='metric-tag'>Avg Time</div>
            </div>
            <div class='metric-box'>
                <div class='metric-num amber'>{st.session_state.sources_found}</div>
                <div class='metric-tag'>Sources</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr class='sb-divider'>", unsafe_allow_html=True)

    # Upload section
    st.markdown("<div class='sb-label'>Upload Document</div>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Drop PDF or TXT",
        type=["pdf", "txt"],
        label_visibility="collapsed"
    )

    if uploaded_file:
        if st.button("⬆  Index Document", use_container_width=True):
            with st.spinner("Indexing document..."):
                try:
                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type
                        )
                    }
                    resp = requests.post(UPLOAD_URL, files=files, timeout=120)

                    if resp.status_code == 200:
                        data = resp.json()
                        st.success(f"✅ {data['total_chunks']} chunks indexed")
                        if uploaded_file.name not in st.session_state.uploaded_docs:
                            st.session_state.uploaded_docs.append(uploaded_file.name)
                    else:
                        st.error(f"Failed: {resp.status_code}")

                except requests.exceptions.Timeout:
                    st.warning("⏱ Timed out — large docs take longer. Try again.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    # Indexed docs
    if st.session_state.uploaded_docs:
        docs_html = "".join([
            f"<div class='doc-item'>✓ &nbsp;{d}</div>"
            for d in st.session_state.uploaded_docs
        ])
        st.markdown(f"""
        <div style='margin-top: 8px;'>
            <div style='font-family: JetBrains Mono, monospace; font-size: 0.58rem;
                        color: #1e2245; text-transform: uppercase;
                        letter-spacing: 0.1em; margin-bottom: 4px;'>
                Indexed this session
            </div>
            {docs_html}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class='upload-note'>
        Large files are processed page-by-page<br>
        to stay within free-tier memory limits.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr class='sb-divider'>", unsafe_allow_html=True)

    # Session
    st.markdown(f"""
    <div class='session-box'>
        SESSION ID<br>
        <span class='val'>{st.session_state.session_id}</span>
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

    st.markdown("<hr class='sb-divider'>", unsafe_allow_html=True)

    # Powered by
    st.markdown("""
    <div class='powered'>
        POWERED BY<br>
        <span class='pill'>Railway — Backend</span><br>
        <span class='pill'>Streamlit Cloud — Frontend</span><br>
        <span class='pill'>Pinecone — Vector DB</span><br>
        <span class='pill'>Gemini Embedding 001</span>
    </div>
    """, unsafe_allow_html=True)


# ------------------------------------------------
# Main Header
# ------------------------------------------------

st.markdown("""
<div class='main-header'>
    <div class='header-eyebrow'>
        <span class='live-dot'></span>
        Live &nbsp;·&nbsp; RAG Pipeline Active
    </div>
    <div class='main-title'>
        Enterprise <span class='accent'>Knowledge</span> Assistant
    </div>
    <div class='header-tags'>
        <span class='header-tag'>Vector Search</span>
        <span class='header-tag'>Guardrails</span>
        <span class='header-tag'>Conversational Memory</span>
        <span class='header-tag'>Document Upload</span>
        <span class='header-tag'>Gemini LLM</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ------------------------------------------------
# Chat Display
# ------------------------------------------------

if not st.session_state.messages:
    st.markdown("""
    <div class='empty-wrap'>
        <div class='empty-icon'>◈</div>
        <div class='empty-title'>Ready to answer your questions</div>
        <div class='empty-sub'>
            Query the knowledge base &nbsp;·&nbsp; Upload a document &nbsp;·&nbsp; Start a conversation
        </div>
    </div>
    """, unsafe_allow_html=True)

else:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

            if msg["role"] == "assistant":
                rt = msg.get("response_time", 0)
                sc = msg.get("source_count", 0)
                if rt:
                    st.markdown(f"""
                    <div class='resp-badge'>
                        <span class='resp-dot'></span>
                        {rt:.2f}s &nbsp;·&nbsp; {sc} source{'s' if sc != 1 else ''}
                    </div>
                    """, unsafe_allow_html=True)

                if msg.get("sources"):
                    with st.expander(f"📎 {len(msg['sources'])} source(s) retrieved"):
                        for i, src in enumerate(msg["sources"], 1):
                            st.markdown(f"""
                            <div class='src-card'>
                                <div class='src-label'>chunk · {i:02d}</div>
                                <div class='src-text'>{src}</div>
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
                    <div class='resp-badge'>
                        <span class='resp-dot'></span>
                        {elapsed:.2f}s &nbsp;·&nbsp; {len(sources)} source{'s' if len(sources) != 1 else ''}
                    </div>
                    """, unsafe_allow_html=True)

                    if sources:
                        with st.expander(f"📎 {len(sources)} source(s) retrieved"):
                            for i, src in enumerate(sources, 1):
                                st.markdown(f"""
                                <div class='src-card'>
                                    <div class='src-label'>chunk · {i:02d}</div>
                                    <div class='src-text'>{src}</div>
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
                msg = "⏱ Timed out. Backend may be waking up — please try again."
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