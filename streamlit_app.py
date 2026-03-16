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
    initial_sidebar_state="collapsed"
)

# ------------------------------------------------
# CSS
# ------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

* {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    box-sizing: border-box;
}

html, body, [class*="css"], .stApp {
    background-color: #080b14 !important;
    color: #e2e5f0 !important;
}

/* Hide all Streamlit chrome */
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }
header { visibility: hidden !important; }
.stDeployButton { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }

/* ---- TOP NAV ---- */
.topnav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 18px 0 16px 0;
    border-bottom: 1px solid #151929;
    margin-bottom: 28px;
}

.topnav-brand {
    display: flex;
    align-items: center;
    gap: 10px;
}

.topnav-logo {
    width: 34px;
    height: 34px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    color: white;
    font-weight: 800;
    flex-shrink: 0;
}

.topnav-name {
    font-size: 1rem;
    font-weight: 700;
    color: #e2e5f0;
    letter-spacing: -0.02em;
}

.topnav-right {
    display: flex;
    align-items: center;
    gap: 8px;
}

.live-badge {
    display: flex;
    align-items: center;
    gap: 6px;
    background: #0e1420;
    border: 1px solid #151929;
    border-radius: 20px;
    padding: 5px 12px;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.65rem;
    color: #34d399;
}

.live-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #34d399;
    animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(52,211,153,0.5); }
    50% { opacity: 0.5; box-shadow: 0 0 0 5px rgba(52,211,153,0); }
}

/* ---- HERO ---- */
.hero {
    margin-bottom: 32px;
}

.hero-title {
    font-size: 2.4rem;
    font-weight: 800;
    color: #e2e5f0;
    letter-spacing: -0.04em;
    line-height: 1.1;
    margin: 0 0 10px 0;
}

.hero-title .g {
    background: linear-gradient(90deg, #818cf8 0%, #22d3ee 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-sub {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.72rem;
    color: #2a2f55;
    letter-spacing: 0.04em;
    margin-bottom: 14px;
}

.tag-row {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 8px;
}

.tag {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.62rem;
    color: #3a3f72;
    background: #0e1020;
    border: 1px solid #151929;
    border-radius: 20px;
    padding: 3px 10px;
}

/* ---- METRICS ROW ---- */
.metrics-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-bottom: 28px;
}

.m-card {
    background: #0e1020;
    border: 1px solid #151929;
    border-radius: 14px;
    padding: 16px;
    text-align: center;
}

.m-num {
    font-size: 1.8rem;
    font-weight: 800;
    line-height: 1;
    color: #818cf8;
}

.m-num.t { color: #22d3ee; }
.m-num.g { color: #34d399; }
.m-num.a { color: #fbbf24; }

.m-lbl {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.58rem;
    color: #2a2f55;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 5px;
}

/* ---- TABS ---- */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #151929 !important;
    gap: 0 !important;
    margin-bottom: 24px !important;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border: none !important;
    color: #2a2f55 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 10px 20px !important;
    border-bottom: 2px solid transparent !important;
    transition: all 0.2s !important;
}

.stTabs [aria-selected="true"] {
    color: #818cf8 !important;
    border-bottom: 2px solid #818cf8 !important;
    background: transparent !important;
}

.stTabs [data-baseweb="tab"]:hover {
    color: #818cf8 !important;
    background: transparent !important;
}

.stTabs [data-baseweb="tab-highlight"] {
    display: none !important;
}

/* ---- CHAT INPUT ---- */
[data-testid="stChatInput"] {
    background: #0e1020 !important;
    border: 1px solid #1e2240 !important;
    border-radius: 14px !important;
}

[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: #e2e5f0 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.92rem !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: #1e2240 !important;
}

/* ---- CHAT MESSAGES ---- */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
}

/* ---- RESPONSE BADGE ---- */
.rb {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.63rem;
    color: #2a2f55;
    background: #0a0d18;
    border: 1px solid #151929;
    border-radius: 20px;
    padding: 4px 12px;
    margin-top: 8px;
}

.rb-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: #34d399;
    flex-shrink: 0;
}

/* ---- SOURCE CARD ---- */
.src {
    background: #080b14;
    border: 1px solid #151929;
    border-left: 3px solid #6366f1;
    border-radius: 8px;
    padding: 12px 14px;
    margin: 6px 0;
}

.src-lbl {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.58rem;
    font-weight: 500;
    color: #6366f1;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 6px;
}

.src-txt {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.72rem;
    color: #3a3f72;
    line-height: 1.7;
}

/* ---- EMPTY STATE ---- */
.empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 5rem 2rem;
    text-align: center;
}

.empty-icon {
    font-size: 2.5rem;
    color: #0e1020;
    margin-bottom: 14px;
}

.empty-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #1e2240;
    margin-bottom: 6px;
}

.empty-hint {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.65rem;
    color: #151929;
}

/* ---- UPLOAD AREA ---- */
[data-testid="stFileUploaderDropzone"] {
    background: #0e1020 !important;
    border: 1px dashed #1e2240 !important;
    border-radius: 12px !important;
}

[data-testid="stFileUploaderDropzone"] p,
[data-testid="stFileUploaderDropzone"] span,
[data-testid="stFileUploaderDropzone"] small {
    color: #2a2f55 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.72rem !important;
}

/* ---- UPLOAD NOTE ---- */
.up-note {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.63rem;
    color: #1e2240;
    background: #0a0d18;
    border: 1px solid #151929;
    border-left: 2px solid #3730a3;
    border-radius: 6px;
    padding: 10px 12px;
    margin-top: 10px;
    line-height: 1.9;
}

/* ---- EXPANDER ---- */
.streamlit-expanderHeader {
    background: #0e1020 !important;
    border: 1px solid #151929 !important;
    border-radius: 8px !important;
    color: #3a3f72 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.68rem !important;
}

.streamlit-expanderContent {
    background: #080b14 !important;
    border: 1px solid #151929 !important;
    border-top: none !important;
}

/* ---- BUTTONS ---- */
.stButton > button {
    background: #0e1020 !important;
    border: 1px solid #1e2240 !important;
    color: #4a4f8a !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    font-size: 0.8rem !important;
    padding: 8px 18px !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
}

.stButton > button:hover {
    border-color: #818cf8 !important;
    color: #818cf8 !important;
    background: #0e1020 !important;
}

/* ---- ALERTS ---- */
[data-testid="stAlert"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.72rem !important;
    border-radius: 8px !important;
}

/* ---- SPINNER ---- */
.stSpinner > div {
    border-top-color: #818cf8 !important;
}

/* ---- INDEXED DOC ---- */
.doc-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.63rem;
    color: #34d399;
    background: #071410;
    border: 1px solid #0e2e22;
    border-radius: 20px;
    padding: 3px 10px;
    margin: 3px 3px 0 0;
}

/* ---- DIVIDER ---- */
.divider {
    border: none;
    border-top: 1px solid #151929;
    margin: 20px 0;
}

/* ---- POWERED ---- */
.powered-row {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 8px;
}

.p-pill {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.6rem;
    color: #1e2240;
    background: #0a0d18;
    border: 1px solid #151929;
    border-radius: 20px;
    padding: 3px 10px;
}

</style>
""", unsafe_allow_html=True)


# ------------------------------------------------
# Session State
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
# Top Nav
# ------------------------------------------------

st.markdown("""
<div class='topnav'>
    <div class='topnav-brand'>
        <div class='topnav-logo'>G</div>
        <div class='topnav-name'>GenAI Assistant</div>
    </div>
    <div class='topnav-right'>
        <div class='live-badge'>
            <span class='live-dot'></span>
            RAG Pipeline Active
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ------------------------------------------------
# Hero
# ------------------------------------------------

st.markdown("""
<div class='hero'>
    <h1 class='hero-title'>Enterprise <span class='g'>Knowledge</span> Assistant</h1>
    <div class='hero-sub'>RAG · VECTOR SEARCH · GUARDRAILS · CONVERSATIONAL MEMORY</div>
    <div class='tag-row'>
        <span class='tag'>Gemini LLM</span>
        <span class='tag'>Pinecone Vector DB</span>
        <span class='tag'>Document Upload</span>
        <span class='tag'>Source Citations</span>
        <span class='tag'>Session Memory</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ------------------------------------------------
# Metrics
# ------------------------------------------------

avg_time = (
    st.session_state.total_time / st.session_state.total_questions
    if st.session_state.total_questions > 0 else 0.0
)

st.markdown(f"""
<div class='metrics-row'>
    <div class='m-card'>
        <div class='m-num'>{st.session_state.total_questions}</div>
        <div class='m-lbl'>Questions</div>
    </div>
    <div class='m-card'>
        <div class='m-num t'>{len(st.session_state.messages) // 2}</div>
        <div class='m-lbl'>Exchanges</div>
    </div>
    <div class='m-card'>
        <div class='m-num g'>{avg_time:.1f}s</div>
        <div class='m-lbl'>Avg Response</div>
    </div>
    <div class='m-card'>
        <div class='m-num a'>{st.session_state.sources_found}</div>
        <div class='m-lbl'>Sources Found</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ------------------------------------------------
# Tabs
# ------------------------------------------------

tab1, tab2, tab3 = st.tabs(["💬  Chat", "📄  Upload Document", "ℹ️  About"])


# ================================================
# TAB 1 — CHAT
# ================================================

with tab1:

    # Chat history
    if not st.session_state.messages:
        st.markdown("""
        <div class='empty'>
            <div class='empty-icon'>◈</div>
            <div class='empty-title'>Ready to answer your questions</div>
            <div class='empty-hint'>
                Ask about company policies · Upload a document · Start a conversation
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
                        <div class='rb'>
                            <span class='rb-dot'></span>
                            {rt:.2f}s &nbsp;·&nbsp; {sc} source{'s' if sc != 1 else ''}
                        </div>
                        """, unsafe_allow_html=True)

                    if msg.get("sources"):
                        with st.expander(f"📎 {len(msg['sources'])} source(s) retrieved"):
                            for i, src in enumerate(msg["sources"], 1):
                                st.markdown(f"""
                                <div class='src'>
                                    <div class='src-lbl'>chunk · {i:02d}</div>
                                    <div class='src-txt'>{src}</div>
                                </div>
                                """, unsafe_allow_html=True)

    # Chat input
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
                        <div class='rb'>
                            <span class='rb-dot'></span>
                            {elapsed:.2f}s &nbsp;·&nbsp; {len(sources)} source{'s' if len(sources) != 1 else ''}
                        </div>
                        """, unsafe_allow_html=True)

                        if sources:
                            with st.expander(f"📎 {len(sources)} source(s) retrieved"):
                                for i, src in enumerate(sources, 1):
                                    st.markdown(f"""
                                    <div class='src'>
                                        <div class='src-lbl'>chunk · {i:02d}</div>
                                        <div class='src-txt'>{src}</div>
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
                        msg_err = f"API returned {response.status_code}. Please try again."
                        st.error(msg_err)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": msg_err,
                            "sources": [],
                            "response_time": 0,
                            "source_count": 0
                        })

                except requests.exceptions.Timeout:
                    msg_err = "⏱ Timed out. Backend may be waking up — please try again."
                    st.warning(msg_err)
                    st.session_state.messages.append({
                        "role": "assistant", "content": msg_err,
                        "sources": [], "response_time": 0, "source_count": 0
                    })

                except requests.exceptions.ConnectionError:
                    msg_err = "🔌 Cannot reach the backend. Please check if the server is running."
                    st.error(msg_err)
                    st.session_state.messages.append({
                        "role": "assistant", "content": msg_err,
                        "sources": [], "response_time": 0, "source_count": 0
                    })

                except Exception as e:
                    msg_err = f"Unexpected error: {str(e)}"
                    st.error(msg_err)
                    st.session_state.messages.append({
                        "role": "assistant", "content": msg_err,
                        "sources": [], "response_time": 0, "source_count": 0
                    })

    # Clear button
    st.markdown("<div style='margin-top: 12px;'>", unsafe_allow_html=True)
    if st.button("↺  Clear Conversation"):
        st.session_state.messages = []
        st.session_state.total_questions = 0
        st.session_state.total_time = 0.0
        st.session_state.sources_found = 0
        st.session_state.session_id = f"sess_{int(time.time())}"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# ================================================
# TAB 2 — UPLOAD
# ================================================

with tab2:

    st.markdown("""
    <div style='margin-bottom: 20px;'>
        <div style='font-size: 1.1rem; font-weight: 700; color: #e2e5f0;
                    margin-bottom: 6px;'>
            Upload & Index Documents
        </div>
        <div style='font-family: JetBrains Mono, monospace; font-size: 0.7rem;
                    color: #2a2f55;'>
            Supported formats: PDF, TXT · Processed page-by-page for memory safety
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "Drop your document here",
            type=["pdf", "txt"],
            label_visibility="visible"
        )

        if uploaded_file:
            st.markdown(f"""
            <div style='font-family: JetBrains Mono, monospace; font-size: 0.7rem;
                        color: #818cf8; background: #0e1020; border: 1px solid #1e2240;
                        border-radius: 8px; padding: 10px 14px; margin: 10px 0;'>
                📄 &nbsp; {uploaded_file.name} &nbsp;·&nbsp;
                {round(len(uploaded_file.getvalue()) / 1024, 1)} KB
            </div>
            """, unsafe_allow_html=True)

            if st.button("⬆  Index This Document"):
                with st.spinner("Indexing document — this may take a moment for large files..."):
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
                            st.success(
                                f"✅ Successfully indexed **{data['total_chunks']}** chunks "
                                f"from **{uploaded_file.name}**"
                            )
                            if uploaded_file.name not in st.session_state.uploaded_docs:
                                st.session_state.uploaded_docs.append(uploaded_file.name)
                        else:
                            st.error(f"Upload failed with status {resp.status_code}")

                    except requests.exceptions.Timeout:
                        st.warning("⏱ Upload timed out. Large documents take longer — try again.")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

        st.markdown("""
        <div class='up-note'>
            ℹ️ &nbsp; Large PDFs are processed page-by-page to stay within<br>
            free-tier memory limits (512MB). This ensures stability<br>
            on Render and Railway free tiers.
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style='background: #0e1020; border: 1px solid #151929;
                    border-radius: 14px; padding: 20px;'>
            <div style='font-family: JetBrains Mono, monospace; font-size: 0.6rem;
                        color: #2a2f55; text-transform: uppercase;
                        letter-spacing: 0.1em; margin-bottom: 12px;'>
                Indexed This Session
            </div>
        """, unsafe_allow_html=True)

        if st.session_state.uploaded_docs:
            docs_html = "".join([
                f"<div class='doc-pill'>✓ &nbsp;{d}</div>"
                for d in st.session_state.uploaded_docs
            ])
            st.markdown(docs_html, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                        color: #151929;'>
                No documents yet
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)


# ================================================
# TAB 3 — ABOUT
# ================================================

with tab3:

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style='background: #0e1020; border: 1px solid #151929;
                    border-radius: 14px; padding: 24px; margin-bottom: 12px;'>
            <div style='font-size: 0.95rem; font-weight: 700; color: #e2e5f0;
                        margin-bottom: 14px;'>
                RAG Pipeline
            </div>
            <div style='font-family: JetBrains Mono, monospace; font-size: 0.7rem;
                        color: #2a2f55; line-height: 2.2;'>
                User Question<br>
                &nbsp;&nbsp;↓<br>
                Gemini Embedding (gemini-embedding-001)<br>
                &nbsp;&nbsp;↓<br>
                Pinecone Vector Search (top-k=5)<br>
                &nbsp;&nbsp;↓<br>
                Guardrail Filter (score > 0.55)<br>
                &nbsp;&nbsp;↓<br>
                Gemini 2.5 Flash LLM<br>
                &nbsp;&nbsp;↓<br>
                Answer + Sources
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style='background: #0e1020; border: 1px solid #151929;
                    border-radius: 14px; padding: 24px; margin-bottom: 12px;'>
            <div style='font-size: 0.95rem; font-weight: 700; color: #e2e5f0;
                        margin-bottom: 14px;'>
                Stack & Deployment
            </div>
            <div style='font-family: JetBrains Mono, monospace; font-size: 0.7rem;
                        color: #2a2f55; line-height: 2.2;'>
                Backend &nbsp;&nbsp;&nbsp; Railway (FastAPI)<br>
                Frontend &nbsp;&nbsp; Streamlit Cloud<br>
                Vector DB &nbsp; Pinecone (3072 dims)<br>
                Embedding &nbsp; gemini-embedding-001<br>
                LLM &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Gemini 2.5 Flash<br>
                Chunking &nbsp;&nbsp; RecursiveCharacterTextSplitter<br>
                Session &nbsp;&nbsp;&nbsp; {st.session_state.session_id}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style='background: #0e1020; border: 1px solid #151929;
                border-radius: 14px; padding: 24px;'>
        <div style='font-size: 0.95rem; font-weight: 700; color: #e2e5f0;
                    margin-bottom: 14px;'>
            Upcoming Features
        </div>
        <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 8px;'>
            <div style='font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                        color: #2a2f55; background: #080b14; border: 1px solid #151929;
                        border-radius: 8px; padding: 8px 12px;'>
                🔄 &nbsp;Multi-document KB
            </div>
            <div style='font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                        color: #2a2f55; background: #080b14; border: 1px solid #151929;
                        border-radius: 8px; padding: 8px 12px;'>
                📊 &nbsp;RAG Evaluation (RAGAS)
            </div>
            <div style='font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                        color: #2a2f55; background: #080b14; border: 1px solid #151929;
                        border-radius: 8px; padding: 8px 12px;'>
                🔍 &nbsp;Hybrid Retrieval (BM25)
            </div>
            <div style='font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                        color: #2a2f55; background: #080b14; border: 1px solid #151929;
                        border-radius: 8px; padding: 8px 12px;'>
                🤖 &nbsp;Multi-Agent Workflow
            </div>
            <div style='font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                        color: #2a2f55; background: #080b14; border: 1px solid #151929;
                        border-radius: 8px; padding: 8px 12px;'>
                ⚡ &nbsp;Streaming Responses
            </div>
            <div style='font-family: JetBrains Mono, monospace; font-size: 0.65rem;
                        color: #2a2f55; background: #080b14; border: 1px solid #151929;
                        border-radius: 8px; padding: 8px 12px;'>
                📡 &nbsp;Observability & Tracing
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)