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

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Fira+Code:wght@300;400;500&display=swap');

html, body {
    font-family: 'Inter', sans-serif !important;
}

.stApp {
    background-color: #07090f !important;
    font-family: 'Inter', sans-serif !important;
}

/* hide chrome */
#MainMenu, footer, header { visibility: hidden !important; }
.stDeployButton { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }

/* ---- all text elements ---- */
p, span, div, label, h1, h2, h3, li, td, th {
    font-family: 'Inter', sans-serif !important;
    color: #e1e4f0 !important;
}

/* ---- topnav ---- */
.tnav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 0 14px 0;
    border-bottom: 1px solid #111827;
    margin-bottom: 24px;
}

.tnav-left {
    display: flex;
    align-items: center;
    gap: 10px;
}

.tnav-logo {
    width: 32px;
    height: 32px;
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    border-radius: 8px;
    display: grid;
    place-items: center;
    font-weight: 800;
    font-size: 0.85rem;
    color: #fff;
    flex-shrink: 0;
}

.tnav-name {
    font-size: 0.95rem;
    font-weight: 700;
    color: #e1e4f0;
    letter-spacing: -0.02em;
}

.tnav-badge {
    display: flex;
    align-items: center;
    gap: 6px;
    background: #0d1117;
    border: 1px solid #1a2030;
    border-radius: 99px;
    padding: 4px 12px;
    font-size: 0.65rem;
    font-family: 'Fira Code', monospace !important;
    color: #10b981;
}

.ldot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #10b981;
    animation: lp 2s ease-in-out infinite;
}

@keyframes lp {
    0%,100% { opacity: 1; }
    50% { opacity: 0.3; }
}

/* ---- hero ---- */
.hero {
    margin-bottom: 24px;
}

.hero h1 {
    font-size: 2.2rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.04em !important;
    color: #e1e4f0 !important;
    line-height: 1.1 !important;
    margin: 0 0 8px 0 !important;
}

.hero h1 .hl {
    background: linear-gradient(90deg, #818cf8, #38bdf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-sub {
    font-size: 0.7rem;
    font-family: 'Fira Code', monospace !important;
    color: #2a3050 !important;
    letter-spacing: 0.06em;
    margin-bottom: 12px;
}

.tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}

.tag {
    font-size: 0.62rem;
    font-family: 'Fira Code', monospace !important;
    color: #374060 !important;
    background: #0d1117;
    border: 1px solid #111827;
    border-radius: 99px;
    padding: 3px 10px;
}

/* ---- metric grid ---- */
.mgrid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    margin-bottom: 24px;
}

.mcard {
    background: #0d1117;
    border: 1px solid #111827;
    border-radius: 12px;
    padding: 16px 12px;
    text-align: center;
}

.mnum {
    font-size: 1.9rem;
    font-weight: 800;
    color: #818cf8;
    line-height: 1;
    font-family: 'Inter', sans-serif !important;
}

.mnum.c1 { color: #818cf8; }
.mnum.c2 { color: #22d3ee; }
.mnum.c3 { color: #34d399; }
.mnum.c4 { color: #fbbf24; }

.mlbl {
    font-size: 0.58rem;
    font-family: 'Fira Code', monospace !important;
    color: #1e2540 !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-top: 5px;
}

/* ---- tabs ---- */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #111827 !important;
    gap: 0 !important;
    margin-bottom: 20px !important;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    color: #374060 !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 10px 20px !important;
}

.stTabs [aria-selected="true"] {
    color: #818cf8 !important;
    border-bottom: 2px solid #818cf8 !important;
    background: transparent !important;
}

.stTabs [data-baseweb="tab-highlight"] { display: none !important; }

/* ---- chat messages ---- */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 4px 0 !important;
}

/* ---- response badge ---- */
.rbadge {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    font-size: 0.63rem;
    font-family: 'Fira Code', monospace !important;
    color: #2a3050 !important;
    background: #0a0d15;
    border: 1px solid #111827;
    border-radius: 99px;
    padding: 3px 10px;
    margin-top: 6px;
}

.rdot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: #34d399;
    flex-shrink: 0;
}

/* ---- source card ---- */
.schunk {
    background: #080b12;
    border: 1px solid #111827;
    border-left: 3px solid #6366f1;
    border-radius: 8px;
    padding: 12px 14px;
    margin: 6px 0;
}

.slabel {
    font-size: 0.58rem;
    font-family: 'Fira Code', monospace !important;
    color: #6366f1 !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 6px;
}

.stext {
    font-size: 0.72rem;
    font-family: 'Fira Code', monospace !important;
    color: #2a3050 !important;
    line-height: 1.7;
}

/* ---- empty state ---- */
.empty {
    text-align: center;
    padding: 4rem 2rem;
}

.eicon {
    font-size: 2.5rem;
    opacity: 0.08;
    margin-bottom: 14px;
}

.etitle {
    font-size: 1rem;
    font-weight: 600;
    color: #1a2030 !important;
    margin-bottom: 6px;
}

.ehint {
    font-size: 0.65rem;
    font-family: 'Fira Code', monospace !important;
    color: #111827 !important;
}

/* ---- chat input ---- */
[data-testid="stChatInput"] {
    background: #0d1117 !important;
    border: 1px solid #1a2030 !important;
    border-radius: 12px !important;
}

[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: #e1e4f0 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: #1a2030 !important;
}

/* ---- expander ---- */
.streamlit-expanderHeader {
    background: #0d1117 !important;
    border: 1px solid #111827 !important;
    border-radius: 8px !important;
    font-family: 'Fira Code', monospace !important;
    font-size: 0.68rem !important;
    color: #374060 !important;
}

.streamlit-expanderContent {
    background: #080b12 !important;
    border: 1px solid #111827 !important;
    border-top: none !important;
}

/* ---- buttons ---- */
.stButton > button {
    background: #0d1117 !important;
    border: 1px solid #1a2030 !important;
    color: #4a5080 !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    font-size: 0.78rem !important;
    padding: 8px 16px !important;
    transition: all 0.15s !important;
}

.stButton > button:hover {
    border-color: #818cf8 !important;
    color: #818cf8 !important;
}

/* ---- file uploader ---- */
[data-testid="stFileUploaderDropzone"] {
    background: #0d1117 !important;
    border: 1px dashed #1a2030 !important;
    border-radius: 10px !important;
}

[data-testid="stFileUploaderDropzone"] p,
[data-testid="stFileUploaderDropzone"] span,
[data-testid="stFileUploaderDropzone"] small {
    color: #374060 !important;
    font-family: 'Fira Code', monospace !important;
    font-size: 0.72rem !important;
}

/* ---- alerts ---- */
[data-testid="stAlert"] {
    font-family: 'Fira Code', monospace !important;
    font-size: 0.72rem !important;
    border-radius: 8px !important;
}

/* ---- spinner ---- */
.stSpinner > div {
    border-top-color: #818cf8 !important;
}

/* ---- about cards ---- */
.acard {
    background: #0d1117;
    border: 1px solid #111827;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 10px;
}

.acard-title {
    font-size: 0.9rem;
    font-weight: 700;
    color: #e1e4f0 !important;
    margin-bottom: 14px;
}

.acard-body {
    font-size: 0.7rem;
    font-family: 'Fira Code', monospace !important;
    color: #2a3050 !important;
    line-height: 2.1;
}

.feat-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-top: 4px;
}

.feat-item {
    font-size: 0.65rem;
    font-family: 'Fira Code', monospace !important;
    color: #2a3050 !important;
    background: #080b12;
    border: 1px solid #111827;
    border-radius: 6px;
    padding: 8px 12px;
}

/* ---- upload note ---- */
.upnote {
    font-size: 0.63rem;
    font-family: 'Fira Code', monospace !important;
    color: #1e2540 !important;
    background: #080b12;
    border: 1px solid #111827;
    border-left: 2px solid #3730a3;
    border-radius: 6px;
    padding: 10px 12px;
    margin-top: 10px;
    line-height: 1.9;
}

/* ---- doc pill ---- */
.docpill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 0.62rem;
    font-family: 'Fira Code', monospace !important;
    color: #34d399 !important;
    background: #071410;
    border: 1px solid #0e2820;
    border-radius: 99px;
    padding: 3px 10px;
    margin: 3px 3px 0 0;
}

/* ---- session box ---- */
.sessbox {
    font-size: 0.6rem;
    font-family: 'Fira Code', monospace !important;
    color: #1a2030 !important;
    background: #080b12;
    border: 1px solid #0d1117;
    border-radius: 8px;
    padding: 8px 12px;
    margin-top: 10px;
    line-height: 1.9;
}

.sessbox .sv {
    color: #2a3050 !important;
    word-break: break-all;
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

st.markdown(f"""
<div class='tnav'>
    <div class='tnav-left'>
        <div class='tnav-logo'>G</div>
        <div class='tnav-name'>GenAI Knowledge Assistant</div>
    </div>
    <div class='tnav-badge'>
        <span class='ldot'></span>
        RAG Pipeline Active
    </div>
</div>
""", unsafe_allow_html=True)


# ------------------------------------------------
# Hero
# ------------------------------------------------

st.markdown("""
<div class='hero'>
    <h1>Enterprise <span class='hl'>Knowledge</span> Assistant</h1>
    <div class='hero-sub'>RAG &nbsp;·&nbsp; VECTOR SEARCH &nbsp;·&nbsp; GUARDRAILS &nbsp;·&nbsp; CONVERSATIONAL MEMORY</div>
    <div class='tags'>
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
<div class='mgrid'>
    <div class='mcard'>
        <div class='mnum c1'>{st.session_state.total_questions}</div>
        <div class='mlbl'>Questions</div>
    </div>
    <div class='mcard'>
        <div class='mnum c2'>{len(st.session_state.messages) // 2}</div>
        <div class='mlbl'>Exchanges</div>
    </div>
    <div class='mcard'>
        <div class='mnum c3'>{avg_time:.1f}s</div>
        <div class='mlbl'>Avg Response</div>
    </div>
    <div class='mcard'>
        <div class='mnum c4'>{st.session_state.sources_found}</div>
        <div class='mlbl'>Sources Found</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ------------------------------------------------
# Tabs
# ------------------------------------------------

tab1, tab2, tab3 = st.tabs(["Chat", "Upload Document", "About"])


# ================================================
# TAB 1 — CHAT
# ================================================

with tab1:

    if not st.session_state.messages:
        st.markdown("""
        <div class='empty'>
            <div class='eicon'>◈</div>
            <div class='etitle'>Ready to answer your questions</div>
            <div class='ehint'>
                Ask about company policies &nbsp;·&nbsp;
                Upload a document &nbsp;·&nbsp;
                Start a conversation
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
                        <div class='rbadge'>
                            <span class='rdot'></span>
                            {rt:.2f}s &nbsp;·&nbsp; {sc} source{'s' if sc != 1 else ''}
                        </div>
                        """, unsafe_allow_html=True)

                    srcs = msg.get("sources", [])
                    if srcs:
                        with st.expander(f"View {len(srcs)} source chunk(s)"):
                            for i, src in enumerate(srcs, 1):
                                st.markdown(f"""
                                <div class='schunk'>
                                    <div class='slabel'>CHUNK {i:02d}</div>
                                    <div class='stext'>{src}</div>
                                </div>
                                """, unsafe_allow_html=True)

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
                    t0 = time.time()
                    payload = {
                        "question": question,
                        "session_id": st.session_state.session_id
                    }
                    res = requests.post(ASK_URL, json=payload, timeout=30)
                    elapsed = time.time() - t0

                    if res.status_code == 200:
                        data = res.json()
                        answer = data.get("answer", "No answer returned.")
                        sources = data.get("sources", [])

                        st.session_state.total_time += elapsed
                        st.session_state.sources_found += len(sources)

                        st.markdown(answer)

                        st.markdown(f"""
                        <div class='rbadge'>
                            <span class='rdot'></span>
                            {elapsed:.2f}s &nbsp;·&nbsp; {len(sources)} source{'s' if len(sources) != 1 else ''}
                        </div>
                        """, unsafe_allow_html=True)

                        if sources:
                            with st.expander(f"View {len(sources)} source chunk(s)"):
                                for i, src in enumerate(sources, 1):
                                    st.markdown(f"""
                                    <div class='schunk'>
                                        <div class='slabel'>CHUNK {i:02d}</div>
                                        <div class='stext'>{src}</div>
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
                        err = f"API error {res.status_code}. Please try again."
                        st.error(err)
                        st.session_state.messages.append({
                            "role": "assistant", "content": err,
                            "sources": [], "response_time": 0, "source_count": 0
                        })

                except requests.exceptions.Timeout:
                    err = "Timed out. Backend may be waking up — please try again."
                    st.warning(err)
                    st.session_state.messages.append({
                        "role": "assistant", "content": err,
                        "sources": [], "response_time": 0, "source_count": 0
                    })

                except requests.exceptions.ConnectionError:
                    err = "Cannot reach backend. Please check if the server is running."
                    st.error(err)
                    st.session_state.messages.append({
                        "role": "assistant", "content": err,
                        "sources": [], "response_time": 0, "source_count": 0
                    })

                except Exception as e:
                    err = f"Unexpected error: {str(e)}"
                    st.error(err)
                    st.session_state.messages.append({
                        "role": "assistant", "content": err,
                        "sources": [], "response_time": 0, "source_count": 0
                    })

    col_a, col_b = st.columns([1, 5])
    with col_a:
        if st.button("Clear Conversation"):
            st.session_state.messages = []
            st.session_state.total_questions = 0
            st.session_state.total_time = 0.0
            st.session_state.sources_found = 0
            st.session_state.session_id = f"sess_{int(time.time())}"
            st.rerun()


# ================================================
# TAB 2 — UPLOAD
# ================================================

with tab2:

    st.markdown("""
    <div style='margin-bottom: 20px;'>
        <div style='font-size: 1.05rem; font-weight: 700; color: #e1e4f0; margin-bottom: 5px;'>
            Upload and Index Documents
        </div>
        <div style='font-size: 0.7rem; font-family: Fira Code, monospace; color: #2a3050;'>
            Supported: PDF, TXT &nbsp;·&nbsp; Max recommended size: 5MB &nbsp;·&nbsp; Processed page-by-page
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "Drop your file here (PDF or TXT, max 5MB recommended)",
            type=["pdf", "txt"],
            label_visibility="visible"
        )

        if uploaded_file:
            file_size_kb = len(uploaded_file.getvalue()) / 1024
            file_size_mb = file_size_kb / 1024

            # Warn if file is too large
            if file_size_mb > 5:
                st.warning(
                    f"File is {file_size_mb:.1f}MB. "
                    f"Large files may timeout on free-tier. "
                    f"Recommended: compress PDF or split into smaller parts."
                )

            st.markdown(f"""
            <div style='font-size: 0.72rem; font-family: Fira Code, monospace;
                        color: #818cf8; background: #0d1117; border: 1px solid #1a2030;
                        border-radius: 8px; padding: 10px 14px; margin: 10px 0;'>
                {uploaded_file.name} &nbsp;·&nbsp; {file_size_kb:.0f} KB
            </div>
            """, unsafe_allow_html=True)

            if st.button("Index This Document"):
                with st.spinner(f"Indexing {uploaded_file.name} — large files may take a minute..."):
                    try:
                        files = {
                            "file": (
                                uploaded_file.name,
                                uploaded_file.getvalue(),
                                uploaded_file.type
                            )
                        }
                        resp = requests.post(UPLOAD_URL, files=files, timeout=180)

                        if resp.status_code == 200:
                            data = resp.json()
                            st.success(
                                f"Successfully indexed {data['total_chunks']} chunks "
                                f"from {uploaded_file.name}"
                            )
                            if uploaded_file.name not in st.session_state.uploaded_docs:
                                st.session_state.uploaded_docs.append(uploaded_file.name)
                        elif resp.status_code == 500:
                            st.error(
                                "Server error (500) — file may be too large for free-tier memory (512MB). "
                                "Try a smaller file or compress the PDF."
                            )
                        else:
                            st.error(f"Upload failed with status {resp.status_code}")

                    except requests.exceptions.Timeout:
                        st.warning(
                            "Request timed out. The file may be too large. "
                            "Try compressing the PDF or splitting into chapters."
                        )
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

        st.markdown("""
        <div class='upnote'>
            Large PDFs are processed page-by-page to stay within<br>
            free-tier memory limits (512MB RAM on Railway).<br>
            For best results keep files under 5MB.
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style='background: #0d1117; border: 1px solid #111827;
                    border-radius: 12px; padding: 18px;'>
            <div style='font-size: 0.6rem; font-family: Fira Code, monospace;
                        color: #1e2540; text-transform: uppercase;
                        letter-spacing: 0.1em; margin-bottom: 12px;'>
                Indexed This Session
            </div>
        """, unsafe_allow_html=True)

        if st.session_state.uploaded_docs:
            for d in st.session_state.uploaded_docs:
                st.markdown(f"<div class='docpill'>&#10003; &nbsp;{d}</div>", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='font-size: 0.65rem; font-family: Fira Code, monospace; color: #111827;'>
                No documents yet
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(f"""
        <div class='sessbox'>
            SESSION<br>
            <span class='sv'>{st.session_state.session_id}</span>
        </div>
        """, unsafe_allow_html=True)


# ================================================
# TAB 3 — ABOUT
# ================================================

with tab3:

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class='acard'>
            <div class='acard-title'>RAG Pipeline</div>
            <div class='acard-body'>
                User Question<br>
                &nbsp;&nbsp;&darr;<br>
                Gemini Embedding (gemini-embedding-001)<br>
                &nbsp;&nbsp;&darr;<br>
                Pinecone Vector Search (top-k = 5)<br>
                &nbsp;&nbsp;&darr;<br>
                Guardrail Filter (score &gt; 0.55)<br>
                &nbsp;&nbsp;&darr;<br>
                Gemini 2.5 Flash LLM<br>
                &nbsp;&nbsp;&darr;<br>
                Answer + Source Citations
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class='acard'>
            <div class='acard-title'>Stack and Deployment</div>
            <div class='acard-body'>
                Backend &nbsp;&nbsp;&nbsp;&nbsp; Railway (FastAPI + Uvicorn)<br>
                Frontend &nbsp;&nbsp;&nbsp; Streamlit Cloud<br>
                Vector DB &nbsp;&nbsp; Pinecone (3072 dims, cosine)<br>
                Embedding &nbsp;&nbsp; gemini-embedding-001<br>
                LLM &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Gemini 2.5 Flash<br>
                Chunking &nbsp;&nbsp;&nbsp; RecursiveCharacterTextSplitter<br>
                Chunk Size &nbsp; 200 tokens, 50 overlap<br>
                Session &nbsp;&nbsp;&nbsp;&nbsp; {st.session_state.session_id}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class='acard'>
        <div class='acard-title'>Upcoming Features</div>
        <div class='feat-grid'>
            <div class='feat-item'>Multi-document Knowledge Base</div>
            <div class='feat-item'>RAG Evaluation with RAGAS</div>
            <div class='feat-item'>Hybrid Retrieval (BM25 + Vector)</div>
            <div class='feat-item'>Multi-Agent Workflow (LangGraph)</div>
            <div class='feat-item'>Streaming Responses</div>
            <div class='feat-item'>Observability and Tracing</div>
        </div>
    </div>
    """, unsafe_allow_html=True)