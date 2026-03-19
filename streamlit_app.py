import streamlit as st
import requests
import uuid
import time
import json

# ------------------------------------------------
# Backend
# ------------------------------------------------

API_BASE     = "https://genai-knowledge-api-production.up.railway.app"
ASK_URL      = f"{API_BASE}/ask"
STREAM_URL   = f"{API_BASE}/ask-stream"
UPLOAD_URL   = f"{API_BASE}/upload"
EVALUATE_URL = f"{API_BASE}/evaluate"

# ------------------------------------------------
# Page Config
# ------------------------------------------------

st.set_page_config(
    page_title="NEXUS — Enterprise Knowledge",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ------------------------------------------------
# CSS
# ------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

:root {
    --bg:   #030508;
    --bg1:  #08091a;
    --bg2:  #0c102a;
    --b0:   #0f1428;
    --b1:   #161d40;
    --b2:   #1e2850;
    --b3:   #263060;
    --txt:  #f0f2ff;
    --txt2: #9ba3cc;
    --txt3: #4a5280;
    --acc:  #5b7fff;
    --acc2: #8b50f0;
    --grn:  #10c880;
    --cyn:  #0ea5d0;
    --amb:  #f0a020;
    --red:  #f05050;
}

*, *::before, *::after { box-sizing: border-box; }

html, body, .stApp {
    font-family: 'Space Grotesk', sans-serif !important;
    background: var(--bg) !important;
    color: var(--txt) !important;
}

.stApp {
    background-image:
        radial-gradient(ellipse 70% 40% at 50% -8%, rgba(91,127,255,0.09) 0%, transparent 60%),
        linear-gradient(rgba(91,127,255,0.022) 1px, transparent 1px),
        linear-gradient(90deg,rgba(91,127,255,0.022) 1px,transparent 1px) !important;
    background-size: 100% 100%, 48px 48px, 48px 48px !important;
    background-attachment: fixed !important;
}

#MainMenu, footer { visibility: hidden !important; }
header { visibility: hidden !important; }
.stDeployButton { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
[data-testid="chatAvatarIcon-user"],
[data-testid="chatAvatarIcon-assistant"],
[data-testid="stChatMessageAvatarUser"],
[data-testid="stChatMessageAvatarAssistant"] { display: none !important; }
[data-testid="stChatMessage"] { background: transparent !important; border: none !important; padding: 0 !important; gap: 0 !important; }

.block-container { padding-top: 1.8rem !important; max-width: 1060px !important; }

.topbar { display:flex; align-items:center; justify-content:space-between; padding-bottom:18px; border-bottom:1px solid var(--b1); margin-bottom:28px; animation:slidedown .5s ease both; }
.tb-left { display:flex; align-items:center; gap:12px; }
.hex { width:36px; height:36px; background:linear-gradient(135deg,var(--acc),var(--acc2)); clip-path:polygon(50% 0%,100% 25%,100% 75%,50% 100%,0% 75%,0% 25%); display:grid; place-items:center; font-family:'Space Mono',monospace !important; font-weight:700; font-size:0.7rem; color:#fff !important; flex-shrink:0; }
.brand-name { font-family:'Space Grotesk',sans-serif !important; font-weight:700; font-size:1rem; letter-spacing:0.06em; color:var(--txt) !important; }
.brand-sub { font-family:'Space Mono',monospace !important; font-size:0.52rem; color:var(--txt3) !important; letter-spacing:0.12em; text-transform:uppercase; }
.online-chip { display:flex; align-items:center; gap:7px; background:rgba(16,200,128,0.08); border:1px solid rgba(16,200,128,0.2); border-radius:99px; padding:5px 14px; font-family:'Space Mono',monospace !important; font-size:0.58rem; color:var(--grn) !important; letter-spacing:0.1em; text-transform:uppercase; }
.blink { width:6px; height:6px; border-radius:50%; background:var(--grn); animation:blinkbeat 2s ease-in-out infinite; }
@keyframes blinkbeat { 0%,100%{opacity:1;box-shadow:0 0 0 0 rgba(16,200,128,.6)} 50%{opacity:.5;box-shadow:0 0 0 6px rgba(16,200,128,0)} }

.hero { text-align:center; padding:22px 0 18px; animation:slideup .6s ease both; }
.hero-eye { font-family:'Space Mono',monospace !important; font-size:0.6rem; letter-spacing:0.2em; text-transform:uppercase; color:var(--acc) !important; margin-bottom:12px; }
.hero-h1 { font-family:'Space Grotesk',sans-serif !important; font-weight:700; font-size:2.6rem; letter-spacing:-0.04em; line-height:1.06; color:var(--txt) !important; margin-bottom:12px; }
.hl { background:linear-gradient(90deg,#7090ff,#b080ff 55%,#50d0ff); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; filter:drop-shadow(0 0 28px rgba(112,144,255,.3)); }
.hero-mono { font-family:'Space Mono',monospace !important; font-size:0.64rem; letter-spacing:0.08em; color:var(--txt2) !important; margin-bottom:14px; }
.pills { display:flex; justify-content:center; flex-wrap:wrap; gap:6px; }
.pill { font-family:'Space Mono',monospace !important; font-size:0.58rem; color:var(--txt2) !important; background:var(--bg1); border:1px solid var(--b1); border-radius:4px; padding:3px 10px; letter-spacing:0.05em; }

.metrics { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin:20px 0; animation:slideup .7s ease both; }
.mc { background:var(--bg1); border:1px solid var(--b1); border-radius:10px; padding:16px 12px; text-align:center; position:relative; overflow:hidden; transition:transform .2s,border-color .2s; }
.mc:hover { transform:translateY(-3px); border-color:var(--b2); }
.mc::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; background:linear-gradient(90deg,transparent,var(--c),transparent); opacity:.9; }
.mc:nth-child(1){--c:#5b7fff;} .mc:nth-child(2){--c:#0ea5d0;} .mc:nth-child(3){--c:#10c880;} .mc:nth-child(4){--c:#f0a020;}
.mv { font-family:'Space Grotesk',sans-serif !important; font-weight:700; font-size:2rem; line-height:1; }
.mv.a{color:#7090ff !important;} .mv.b{color:#20c0f0 !important;} .mv.c{color:#20e090 !important;} .mv.d{color:#f0b030 !important;}
.ml { font-family:'Space Mono',monospace !important; font-size:0.54rem; color:var(--txt2) !important; text-transform:uppercase; letter-spacing:0.12em; margin-top:5px; }

.stTabs [data-baseweb="tab-list"] { background:transparent !important; border-bottom:1px solid var(--b1) !important; gap:0 !important; margin-bottom:22px !important; }
.stTabs [data-baseweb="tab"] { background:transparent !important; border:none !important; border-bottom:1px solid transparent !important; color:var(--txt3) !important; font-family:'Space Mono',monospace !important; font-size:0.67rem !important; font-weight:400 !important; letter-spacing:0.12em !important; text-transform:uppercase !important; padding:10px 22px !important; transition:color .2s !important; }
.stTabs [aria-selected="true"] { color:var(--acc) !important; border-bottom:1px solid var(--acc) !important; }
.stTabs [data-baseweb="tab-highlight"] { display:none !important; }

.msg-u-wrap { display:flex; justify-content:flex-end; margin:8px 0; animation:faderight .3s ease both; }
.msg-u-box { max-width:72%; }
.msg-u-lbl { text-align:right; font-family:'Space Mono',monospace !important; font-size:0.54rem; letter-spacing:0.14em; color:var(--acc) !important; text-transform:uppercase; margin-bottom:5px; }
.msg-u { background:rgba(91,127,255,0.12); border:1px solid rgba(91,127,255,0.28); border-radius:16px 16px 4px 16px; padding:13px 18px; font-family:'Space Grotesk',sans-serif !important; font-size:0.95rem; line-height:1.65; color:var(--txt) !important; }
.msg-b-lbl { font-family:'Space Mono',monospace !important; font-size:0.54rem; letter-spacing:0.14em; color:var(--grn) !important; text-transform:uppercase; margin:8px 0 5px; display:flex; align-items:center; gap:6px; animation:fadeleft .3s ease both; }
.msg-b-lbl-dot { width:5px; height:5px; border-radius:50%; background:var(--grn); flex-shrink:0; }
.msg-b-wrap { max-width:84%; margin:0 0 4px 0; animation:fadeleft .3s ease both; }
.msg-b { background:var(--bg1); border:1px solid var(--b1); border-radius:4px 16px 16px 16px; padding:15px 20px; font-family:'Space Grotesk',sans-serif !important; font-size:0.95rem; line-height:1.78; color:var(--txt) !important; }
.cursor { display:inline-block; width:2px; height:1em; background:var(--acc); margin-left:2px; vertical-align:text-bottom; animation:cursorblink 0.8s ease-in-out infinite; }
@keyframes cursorblink { 0%,100%{opacity:1} 50%{opacity:0} }
.msg-meta-wrap { margin:6px 0 14px 0; animation:fadeleft .3s ease both; }
.msg-meta { display:inline-flex; align-items:center; gap:8px; font-family:'Space Mono',monospace !important; font-size:0.58rem; color:var(--txt2) !important; background:var(--bg); border:1px solid var(--b0); border-radius:4px; padding:4px 12px; letter-spacing:0.05em; }
.msg-meta-dot { width:4px; height:4px; border-radius:50%; background:var(--grn); }

.schunk { background:var(--bg); border:1px solid var(--b1); border-left:2px solid var(--acc); border-radius:6px; padding:12px 16px; margin:7px 0; }
.schunk-lbl { font-family:'Space Mono',monospace !important; font-size:0.52rem; color:var(--acc) !important; text-transform:uppercase; letter-spacing:0.15em; margin-bottom:4px; }
.schunk-src { font-family:'Space Mono',monospace !important; font-size:0.5rem; color:var(--txt3) !important; margin-bottom:7px; }
.schunk-txt { font-family:'Space Mono',monospace !important; font-size:0.7rem; color:var(--txt2) !important; line-height:1.75; }

.empty { text-align:center; padding:5rem 2rem; animation:slideup .5s ease both; }
.empty-glyph { font-size:2.5rem; color:var(--b2) !important; display:block; margin-bottom:16px; animation:floatit 3s ease-in-out infinite; }
.empty-t { font-family:'Space Grotesk',sans-serif !important; font-weight:600; font-size:1rem; color:var(--txt3) !important; margin-bottom:8px; }
.empty-s { font-family:'Space Mono',monospace !important; font-size:0.62rem; color:var(--b2) !important; letter-spacing:0.05em; }

[data-testid="stChatInput"] { background:var(--bg1) !important; border:1px solid var(--b2) !important; border-radius:10px !important; transition:border-color .2s,box-shadow .2s !important; margin-top:16px !important; }
[data-testid="stChatInput"]:focus-within { border-color:var(--acc) !important; box-shadow:0 0 0 3px rgba(91,127,255,.1) !important; }
[data-testid="stChatInput"] textarea { background:transparent !important; color:var(--txt) !important; font-family:'Space Grotesk',sans-serif !important; font-size:0.9rem !important; caret-color:var(--acc) !important; }
[data-testid="stChatInput"] textarea::placeholder { color:var(--txt3) !important; }

.streamlit-expanderHeader { background:var(--bg1) !important; border:1px solid var(--b1) !important; border-radius:6px !important; font-family:'Space Mono',monospace !important; font-size:0.62rem !important; letter-spacing:0.08em !important; color:var(--txt2) !important; text-transform:uppercase !important; }
.streamlit-expanderContent { background:var(--bg) !important; border:1px solid var(--b1) !important; border-top:none !important; }

.stButton > button { background:var(--bg1) !important; border:1px solid var(--b2) !important; color:var(--txt2) !important; font-family:'Space Mono',monospace !important; font-size:0.64rem !important; letter-spacing:0.08em !important; text-transform:uppercase !important; border-radius:6px !important; padding:8px 20px !important; transition:all .15s ease !important; }
.stButton > button:hover { border-color:var(--acc) !important; color:var(--acc) !important; background:rgba(91,127,255,.06) !important; }

[data-testid="stFileUploaderDropzone"] { background:var(--bg1) !important; border:1px dashed var(--b2) !important; border-radius:10px !important; transition:border-color .2s !important; }
[data-testid="stFileUploaderDropzone"]:hover { border-color:var(--acc) !important; }
[data-testid="stFileUploaderDropzone"] p,[data-testid="stFileUploaderDropzone"] span,[data-testid="stFileUploaderDropzone"] small { font-family:'Space Mono',monospace !important; color:var(--txt2) !important; font-size:0.68rem !important; }

.acard { background:var(--bg1); border:1px solid var(--b1); border-radius:10px; padding:22px; margin-bottom:12px; position:relative; overflow:hidden; transition:border-color .2s,transform .2s; }
.acard:hover { border-color:var(--b2); transform:translateY(-2px); }
.acard::after { content:''; position:absolute; top:0; right:0; width:80px; height:80px; background:radial-gradient(circle,rgba(91,127,255,.06),transparent 70%); pointer-events:none; }
.acard-t { font-family:'Space Grotesk',sans-serif !important; font-weight:700; font-size:0.88rem; color:var(--txt) !important; margin-bottom:16px; display:flex; align-items:center; gap:8px; }
.acard-t::before { content:''; display:inline-block; width:3px; height:14px; background:var(--acc); border-radius:2px; }
.acard-b { font-family:'Space Mono',monospace !important; font-size:0.66rem; color:var(--txt2) !important; line-height:2.2; }
.feat-grid { display:grid; grid-template-columns:1fr 1fr; gap:8px; }
.feat-item { font-family:'Space Mono',monospace !important; font-size:0.6rem; color:var(--txt2) !important; background:var(--bg); border:1px solid var(--b1); border-radius:6px; padding:9px 12px; display:flex; align-items:center; gap:8px; transition:border-color .2s; }
.feat-item:hover { border-color:var(--b2); }
.feat-dot { width:4px; height:4px; border-radius:50%; background:var(--acc); flex-shrink:0; }
.feat-item.done { border-color:rgba(16,200,128,0.3); }
.feat-item.done .feat-dot { background:var(--grn); }

/* ── EVAL TAB ── */
.eval-header { font-family:'Space Grotesk',sans-serif !important; font-weight:700; font-size:0.95rem; color:var(--txt); margin-bottom:5px; }
.eval-sub { font-family:'Space Mono',monospace !important; font-size:0.62rem; color:var(--txt2); margin-bottom:20px; }

.eval-tool-label { font-family:'Space Mono',monospace !important; font-size:0.58rem; color:var(--acc); text-transform:uppercase; letter-spacing:0.14em; margin-bottom:10px; display:flex; align-items:center; gap:8px; }
.eval-tool-label::before { content:''; display:inline-block; width:3px; height:12px; background:var(--acc); border-radius:2px; }
.eval-tool-label.tru::before { background:var(--amb); }
.eval-tool-label.tru { color:var(--amb) !important; }

.score-card { background:var(--bg1); border:1px solid var(--b1); border-radius:10px; padding:16px; margin-bottom:8px; }
.score-row { display:flex; align-items:center; justify-content:space-between; margin-bottom:10px; }
.score-name { font-family:'Space Mono',monospace !important; font-size:0.62rem; color:var(--txt2); text-transform:uppercase; letter-spacing:0.08em; }
.score-val { font-family:'Space Grotesk',sans-serif !important; font-weight:700; font-size:1rem; }
.score-bar-bg { background:var(--b1); border-radius:4px; height:6px; flex:1; margin:0 12px; overflow:hidden; }
.score-bar-fill { height:6px; border-radius:4px; transition:width 0.8s ease; }

.overall-card { background:var(--bg2); border:1px solid var(--b2); border-radius:10px; padding:18px; text-align:center; margin-top:10px; }
.overall-num { font-family:'Space Grotesk',sans-serif !important; font-weight:800; font-size:2.4rem; line-height:1; }
.overall-lbl { font-family:'Space Mono',monospace !important; font-size:0.58rem; color:var(--txt3); text-transform:uppercase; letter-spacing:0.12em; margin-top:5px; }

.q-card { background:var(--bg); border:1px solid var(--b1); border-radius:8px; padding:12px 16px; margin:6px 0; }
.q-text { font-family:'Space Grotesk',sans-serif !important; font-size:0.82rem; color:var(--txt); margin-bottom:8px; }
.q-scores { display:flex; flex-wrap:wrap; gap:6px; }
.q-badge { font-family:'Space Mono',monospace !important; font-size:0.6rem; border-radius:4px; padding:2px 8px; }

[data-testid="stAlert"] { font-family:'Space Mono',monospace !important; font-size:0.7rem !important; border-radius:6px !important; }
.stSpinner > div { border-top-color:var(--acc) !important; }

@keyframes slidedown { from{opacity:0;transform:translateY(-10px)} to{opacity:1;transform:translateY(0)} }
@keyframes slideup   { from{opacity:0;transform:translateY(10px)}  to{opacity:1;transform:translateY(0)} }
@keyframes faderight { from{opacity:0;transform:translateX(14px)}  to{opacity:1;transform:translateX(0)} }
@keyframes fadeleft  { from{opacity:0;transform:translateX(-14px)} to{opacity:1;transform:translateX(0)} }
@keyframes floatit   { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-10px)} }
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------
# Session State
# ------------------------------------------------

if "messages"        not in st.session_state: st.session_state.messages        = []
if "session_id"      not in st.session_state: st.session_state.session_id      = f"nx_{str(uuid.uuid4())[:8]}"
if "questions"       not in st.session_state: st.session_state.questions       = 0
if "time_total"      not in st.session_state: st.session_state.time_total      = 0.0
if "src_total"       not in st.session_state: st.session_state.src_total       = 0
if "uploaded_docs"   not in st.session_state: st.session_state.uploaded_docs   = []
if "use_stream"      not in st.session_state: st.session_state.use_stream      = True
if "eval_results"    not in st.session_state: st.session_state.eval_results    = None
if "eval_running"    not in st.session_state: st.session_state.eval_running    = False


# ------------------------------------------------
# Helpers
# ------------------------------------------------

def extract_src_text(src) -> str:
    if isinstance(src, dict):
        return str(src.get("text", src.get("content", str(src))))
    return str(src)

def extract_src_meta(src) -> str:
    if isinstance(src, dict):
        source = src.get("source", "")
        page   = src.get("page", "")
        if source and page:
            return f"{source} · page {page}"
        elif source:
            return source
    return ""

def score_color(score: float) -> str:
    if score >= 0.8:  return "#10c880"
    if score >= 0.6:  return "#f0a020"
    return "#f05050"

def score_label(score: float) -> str:
    if score >= 0.8:  return "GOOD"
    if score >= 0.6:  return "FAIR"
    return "POOR"

def render_score_row(name: str, score: float):
    color = score_color(score)
    pct   = int(score * 100)
    st.markdown(f"""
    <div class="score-row">
        <div class="score-name">{name}</div>
        <div class="score-bar-bg">
            <div class="score-bar-fill" style="width:{pct}%;background:{color};"></div>
        </div>
        <div class="score-val" style="color:{color};">{score:.3f}</div>
    </div>
    """, unsafe_allow_html=True)


# ------------------------------------------------
# Top Bar
# ------------------------------------------------

st.markdown("""
<div class="topbar">
    <div class="tb-left">
        <div class="hex">NX</div>
        <div>
            <div class="brand-name">NEXUS</div>
            <div class="brand-sub">Enterprise Knowledge OS &nbsp;·&nbsp; v4.1</div>
        </div>
    </div>
    <div class="online-chip"><span class="blink"></span>System Online</div>
</div>
""", unsafe_allow_html=True)


# ------------------------------------------------
# Hero
# ------------------------------------------------

st.markdown("""
<div class="hero">
    <div class="hero-eye">// Hybrid RAG · Streaming · BM25 + Vector · RAGAS · TruLens</div>
    <div class="hero-h1">Enterprise <span class="hl">Knowledge</span> OS</div>
    <div class="hero-mono">
        GEMINI-EMBEDDING-001 &nbsp;·&nbsp; PINECONE 3072-DIM &nbsp;·&nbsp;
        GEMINI 2.5 FLASH + GROQ FALLBACK
    </div>
    <div class="pills">
        <span class="pill">hybrid retrieval</span>
        <span class="pill">BM25 + vector</span>
        <span class="pill">RRF fusion</span>
        <span class="pill">streaming tokens</span>
        <span class="pill">RAGAS eval</span>
        <span class="pill">TruLens tracing</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ------------------------------------------------
# Metrics
# ------------------------------------------------

avg = st.session_state.time_total / st.session_state.questions if st.session_state.questions > 0 else 0.0

st.markdown(f"""
<div class="metrics">
    <div class="mc"><div class="mv a">{st.session_state.questions}</div><div class="ml">Queries</div></div>
    <div class="mc"><div class="mv b">{len(st.session_state.messages)//2}</div><div class="ml">Exchanges</div></div>
    <div class="mc"><div class="mv c">{avg:.1f}s</div><div class="ml">Avg Latency</div></div>
    <div class="mc"><div class="mv d">{st.session_state.src_total}</div><div class="ml">Chunks Retrieved</div></div>
</div>
""", unsafe_allow_html=True)


# ------------------------------------------------
# Tabs
# ------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs(["CHAT", "INGEST", "EVAL", "SYSTEM"])


# ════════════════════════════════════════════════
# TAB 1 — CHAT
# ════════════════════════════════════════════════

with tab1:

    col_tog, _ = st.columns([2, 8])
    with col_tog:
        st.session_state.use_stream = st.toggle(
            "Streaming", value=st.session_state.use_stream,
            help="Stream tokens in real-time vs wait for full response"
        )

    if not st.session_state.messages:
        st.markdown("""
        <div class="empty">
            <span class="empty-glyph">&#11041;</span>
            <div class="empty-t">Knowledge base is ready</div>
            <div class="empty-s">Send a query · Upload docs in INGEST · Check EVAL for quality scores</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="msg-u-wrap"><div class="msg-u-box">
                    <div class="msg-u-lbl">You</div>
                    <div class="msg-u">{msg['content']}</div>
                </div></div>
                """, unsafe_allow_html=True)
            else:
                st.markdown('<div class="msg-b-lbl"><span class="msg-b-lbl-dot"></span>NEXUS</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="msg-b-wrap"><div class="msg-b">{msg["content"]}</div></div>', unsafe_allow_html=True)
                rt = msg.get("response_time", 0)
                sc = msg.get("source_count", 0)
                if rt:
                    st.markdown(f"""
                    <div class="msg-meta-wrap"><div class="msg-meta">
                        <span class="msg-meta-dot"></span>
                        {rt:.2f}s &nbsp;&#183;&nbsp; {sc} chunk{'s' if sc != 1 else ''} &nbsp;&#183;&nbsp; hybrid
                    </div></div>
                    """, unsafe_allow_html=True)
                srcs = msg.get("sources", [])
                if srcs:
                    with st.expander(f"Sources ({len(srcs)} chunks)"):
                        for j, src in enumerate(srcs, 1):
                            text = extract_src_text(src)
                            meta = extract_src_meta(src)
                            st.markdown(f"""
                            <div class="schunk">
                                <div class="schunk-lbl">Chunk {j:02d}</div>
                                {f'<div class="schunk-src">{meta}</div>' if meta else ''}
                                <div class="schunk-txt">{text}</div>
                            </div>
                            """, unsafe_allow_html=True)

    question = st.chat_input("Enter query...")

    if question:
        st.session_state.questions += 1
        st.session_state.messages.append({"role": "user", "content": question, "sources": []})

        st.markdown(f"""
        <div class="msg-u-wrap"><div class="msg-u-box">
            <div class="msg-u-lbl">You</div>
            <div class="msg-u">{question}</div>
        </div></div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="msg-b-lbl"><span class="msg-b-lbl-dot"></span>NEXUS</div>', unsafe_allow_html=True)

        t0 = time.time()
        full_answer = ""
        sources     = []
        streamed_ok = False

        if st.session_state.use_stream:
            placeholder = st.empty()
            try:
                with requests.post(STREAM_URL,
                                   json={"question": question, "session_id": st.session_state.session_id},
                                   stream=True, timeout=60) as res:
                    if res.status_code == 200:
                        streamed_ok = True
                        for raw_line in res.iter_lines():
                            if raw_line:
                                line = raw_line.decode("utf-8")
                                if line.startswith("data: "):
                                    try:
                                        data = json.loads(line[6:])
                                    except Exception:
                                        continue
                                    if not data.get("done"):
                                        full_answer += data.get("token", "")
                                        placeholder.markdown(f'<div class="msg-b-wrap"><div class="msg-b">{full_answer}<span class="cursor"></span></div></div>', unsafe_allow_html=True)
                                    else:
                                        sources = data.get("sources", [])
                                        placeholder.markdown(f'<div class="msg-b-wrap"><div class="msg-b">{full_answer}</div></div>', unsafe_allow_html=True)
            except Exception as e:
                streamed_ok = False

        if not st.session_state.use_stream or not streamed_ok:
            with st.spinner(""):
                try:
                    res = requests.post(ASK_URL,
                                        json={"question": question, "session_id": st.session_state.session_id},
                                        timeout=30)
                    if res.status_code == 200:
                        data        = res.json()
                        full_answer = data.get("answer", "No answer returned.")
                        sources     = data.get("sources", [])
                    else:
                        full_answer = f"Backend error {res.status_code}."
                except requests.exceptions.Timeout:
                    full_answer = "Request timed out. Try again."
                except Exception as e:
                    full_answer = f"Error: {str(e)}"
            st.markdown(f'<div class="msg-b-wrap"><div class="msg-b">{full_answer}</div></div>', unsafe_allow_html=True)

        elapsed = time.time() - t0
        st.session_state.time_total += elapsed
        st.session_state.src_total  += len(sources)

        st.markdown(f"""
        <div class="msg-meta-wrap"><div class="msg-meta">
            <span class="msg-meta-dot"></span>
            {elapsed:.2f}s &nbsp;&#183;&nbsp; {len(sources)} chunk{'s' if len(sources) != 1 else ''} &nbsp;&#183;&nbsp; hybrid retrieval
        </div></div>
        """, unsafe_allow_html=True)

        if sources:
            with st.expander(f"Sources ({len(sources)} chunks)"):
                for j, src in enumerate(sources, 1):
                    text = extract_src_text(src)
                    meta = extract_src_meta(src)
                    st.markdown(f"""
                    <div class="schunk">
                        <div class="schunk-lbl">Chunk {j:02d}</div>
                        {f'<div class="schunk-src">{meta}</div>' if meta else ''}
                        <div class="schunk-txt">{text}</div>
                    </div>
                    """, unsafe_allow_html=True)

        st.session_state.messages.append({
            "role": "assistant", "content": full_answer, "sources": sources,
            "response_time": elapsed, "source_count": len(sources), "streamed": streamed_ok
        })
        st.rerun()

    col_c, _ = st.columns([1, 9])
    with col_c:
        if st.button("Clear Session"):
            st.session_state.messages   = []
            st.session_state.questions  = 0
            st.session_state.time_total = 0.0
            st.session_state.src_total  = 0
            st.session_state.session_id = f"nx_{str(uuid.uuid4())[:8]}"
            st.rerun()


# ════════════════════════════════════════════════
# TAB 2 — INGEST
# ════════════════════════════════════════════════

with tab2:
    st.markdown("""
    <div style="margin-bottom:20px;">
        <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:0.95rem;color:#f0f2ff;margin-bottom:5px;">Document Ingestion Pipeline</div>
        <div style="font-family:'Space Mono',monospace;font-size:0.62rem;color:#9ba3cc;">PDF &nbsp;&#183;&nbsp; TXT &nbsp;&#183;&nbsp; Max 5MB &nbsp;&#183;&nbsp; Chunked at 500 tokens &nbsp;&#183;&nbsp; Indexed in Pinecone + BM25</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])
    with col1:
        uploaded_file = st.file_uploader("Drop document here", type=["pdf", "txt"], label_visibility="collapsed")
        if uploaded_file:
            size_kb = len(uploaded_file.getvalue()) / 1024
            size_mb = size_kb / 1024
            if size_mb > 5:
                st.warning(f"File is {size_mb:.1f}MB — may timeout on free-tier.")
            st.markdown(f"""
            <div style="font-family:'Space Mono',monospace;font-size:0.65rem;color:#5b7fff;background:#08091a;border:1px solid #1e2850;border-radius:6px;padding:10px 14px;margin:10px 0;">
                &#9679;&nbsp; {uploaded_file.name} &nbsp;&#183;&nbsp; {size_kb:.0f} KB
            </div>
            """, unsafe_allow_html=True)
            if st.button("Run Ingestion Pipeline"):
                with st.spinner("Ingesting document..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        resp  = requests.post(UPLOAD_URL, files=files, timeout=180)
                        if resp.status_code == 200:
                            data = resp.json()
                            st.success(f"Ingestion complete — {data.get('total_chunks',0)} chunks indexed · BM25: {data.get('bm25_corpus',0)} chunks")
                            if uploaded_file.name not in st.session_state.uploaded_docs:
                                st.session_state.uploaded_docs.append(uploaded_file.name)
                        elif resp.status_code == 413:
                            st.error("File too large. Max 10MB.")
                        else:
                            st.error(f"Upload failed: {resp.status_code}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

        st.markdown("""
        <div style="font-family:'Space Mono',monospace;font-size:0.6rem;color:#9ba3cc;background:#030508;border:1px solid #161d40;border-left:2px solid rgba(91,127,255,0.5);border-radius:0 6px 6px 0;padding:10px 14px;margin-top:12px;line-height:1.9;">
            Chunked via RecursiveCharacterTextSplitter (chunk=500, overlap=100).<br>
            Each chunk indexed in Pinecone (vector) AND BM25 (keyword) simultaneously.<br>
            Hybrid retrieval merges both using Reciprocal Rank Fusion.
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""<div style="background:#08091a;border:1px solid #161d40;border-radius:10px;padding:18px;"><div style="font-family:'Space Mono',monospace;font-size:0.54rem;color:#9ba3cc;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:14px;">Indexed This Session</div></div>""", unsafe_allow_html=True)
        if st.session_state.uploaded_docs:
            for d in st.session_state.uploaded_docs:
                st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;font-family:'Space Mono',monospace;font-size:0.62rem;color:#10c880;padding:5px 0;border-bottom:1px solid #0f1428;"><span style="width:5px;height:5px;border-radius:50%;background:#10c880;flex-shrink:0;display:inline-block;"></span>{d}</div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div style="font-family:'Space Mono',monospace;font-size:0.62rem;color:#4a5280;padding:4px 0;">No documents this session</div>""", unsafe_allow_html=True)
        st.markdown(f"""<div style="font-family:'Space Mono',monospace;font-size:0.58rem;color:#4a5280;margin-top:14px;padding-top:12px;border-top:1px solid #0f1428;line-height:2;">SESSION ID<br><span style="color:#9ba3cc;">{st.session_state.session_id}</span></div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════
# TAB 3 — EVAL
# ════════════════════════════════════════════════

with tab3:

    st.markdown("""
    <div class="eval-header">RAG Quality Evaluation</div>
    <div class="eval-sub">
        RAGAS measures retrieval + answer quality · TruLens measures grounding + relevance ·
        5 ground truth questions from company_policy.txt · Scored by Groq LLM judge
    </div>
    """, unsafe_allow_html=True)

    # Run button
    col_btn, col_note = st.columns([2, 5])
    with col_btn:
        run_eval = st.button("Run Evaluation — 5 Questions", use_container_width=True)
    with col_note:
        st.markdown("""
        <div style="font-family:'Space Mono',monospace;font-size:0.6rem;color:#4a5280;padding-top:10px;">
            Takes ~60s · Uses Groq as LLM judge · Consumes ~20 API calls
        </div>
        """, unsafe_allow_html=True)

    if run_eval:
        with st.spinner("Running RAGAS + TruLens evaluation on 5 questions..."):
            try:
                resp = requests.post(EVALUATE_URL, timeout=180)
                if resp.status_code == 200:
                    st.session_state.eval_results = resp.json()
                    st.success("Evaluation complete!")
                else:
                    st.error(f"Evaluation failed: {resp.status_code}")
            except requests.exceptions.Timeout:
                st.warning("Evaluation timed out — free-tier server is slow. Try again.")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # ── Display results ──
    if st.session_state.eval_results:
        results = st.session_state.eval_results
        ragas   = results.get("ragas",   {})
        trulens = results.get("trulens", {})

        ragas_scores   = ragas.get("scores",   {})
        trulens_scores = trulens.get("scores", {})

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Two column layout ──
        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="eval-tool-label">RAGAS Metrics</div>', unsafe_allow_html=True)
            st.markdown('<div class="score-card">', unsafe_allow_html=True)

            ragas_map = {
                "faithfulness":      "Faithfulness",
                "answer_relevancy":  "Answer Relevancy",
                "context_precision": "Context Precision",
                "context_recall":    "Context Recall"
            }
            for key, label in ragas_map.items():
                score = ragas_scores.get(key, 0)
                render_score_row(label, score)

            st.markdown('</div>', unsafe_allow_html=True)

            overall_r = ragas_scores.get("overall", 0)
            color_r   = score_color(overall_r)
            st.markdown(f"""
            <div class="overall-card">
                <div class="overall-num" style="color:{color_r};">{overall_r:.3f}</div>
                <div class="overall-lbl">RAGAS Overall &nbsp;·&nbsp; {score_label(overall_r)}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="eval-tool-label tru">TruLens Metrics</div>', unsafe_allow_html=True)
            st.markdown('<div class="score-card">', unsafe_allow_html=True)

            trulens_map = {
                "groundedness":      "Groundedness",
                "answer_relevance":  "Answer Relevance",
                "context_relevance": "Context Relevance"
            }
            for key, label in trulens_map.items():
                score = trulens_scores.get(key, 0)
                render_score_row(label, score)

            st.markdown('</div>', unsafe_allow_html=True)

            overall_t = trulens_scores.get("overall", 0)
            color_t   = score_color(overall_t)
            st.markdown(f"""
            <div class="overall-card">
                <div class="overall-num" style="color:{color_t};">{overall_t:.3f}</div>
                <div class="overall-lbl">TruLens Overall &nbsp;·&nbsp; {score_label(overall_t)}</div>
            </div>
            """, unsafe_allow_html=True)

        # ── Per-question breakdown ──
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("Per-question RAGAS breakdown"):
            for item in ragas.get("per_question", []):
                f  = item.get("faithfulness",      0)
                ar = item.get("answer_relevancy",  0)
                cp = item.get("context_precision", 0)
                cr = item.get("context_recall",    0)
                st.markdown(f"""
                <div class="q-card">
                    <div class="q-text">{item['question']}</div>
                    <div class="q-scores">
                        <span class="q-badge" style="background:rgba(91,127,255,0.1);color:#5b7fff;">Faith {f:.2f}</span>
                        <span class="q-badge" style="background:rgba(16,200,128,0.1);color:#10c880;">Ans Rel {ar:.2f}</span>
                        <span class="q-badge" style="background:rgba(14,165,208,0.1);color:#0ea5d0;">Ctx Pre {cp:.2f}</span>
                        <span class="q-badge" style="background:rgba(240,160,32,0.1);color:#f0a020;">Ctx Rec {cr:.2f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with st.expander("Per-question TruLens breakdown"):
            for item in trulens.get("per_question", []):
                gs = item.get("groundedness",      0)
                ar = item.get("answer_relevance",  0)
                cr = item.get("context_relevance", 0)
                st.markdown(f"""
                <div class="q-card">
                    <div class="q-text">{item['question']}</div>
                    <div style="font-family:'Space Mono',monospace;font-size:0.65rem;color:#4a5280;margin:4px 0 8px;">{item.get('answer','')[:120]}...</div>
                    <div class="q-scores">
                        <span class="q-badge" style="background:rgba(240,160,32,0.1);color:#f0a020;">Ground {gs:.2f}</span>
                        <span class="q-badge" style="background:rgba(16,200,128,0.1);color:#10c880;">Ans Rel {ar:.2f}</span>
                        <span class="q-badge" style="background:rgba(14,165,208,0.1);color:#0ea5d0;">Ctx Rel {cr:.2f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    else:
        st.markdown("""
        <div style="text-align:center;padding:3rem 2rem;">
            <div style="font-size:2rem;opacity:0.15;margin-bottom:14px;">◈</div>
            <div style="font-family:'Space Grotesk',sans-serif;font-weight:600;font-size:0.95rem;color:#2e3560;">
                No evaluation results yet
            </div>
            <div style="font-family:'Space Mono',monospace;font-size:0.62rem;color:#161d40;margin-top:6px;">
                Click "Run Evaluation" above to score the RAG pipeline
            </div>
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════
# TAB 4 — SYSTEM
# ════════════════════════════════════════════════

with tab4:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="acard">
            <div class="acard-t">Hybrid RAG Pipeline</div>
            <div class="acard-b">
                USER QUERY<br>
                &darr;&nbsp; multi-query rewriting (Groq)<br>
                HYBRID RETRIEVAL<br>
                &darr;&nbsp; vector search (Pinecone)<br>
                &darr;&nbsp; BM25 keyword search (in-memory)<br>
                RRF FUSION<br>
                &darr;&nbsp; Reciprocal Rank Fusion merge<br>
                GUARDRAIL FILTER &darr;&nbsp; score 0.30<br>
                LLM GENERATION<br>
                &darr;&nbsp; gemini-2.5-flash (groq fallback)<br>
                STREAMING ANSWER + CITATIONS
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="acard">
            <div class="acard-t">Stack</div>
            <div class="acard-b">
                BACKEND &nbsp;&nbsp;&nbsp;&nbsp; FastAPI + Uvicorn · Railway<br>
                FRONTEND &nbsp;&nbsp;&nbsp; Streamlit Cloud<br>
                VECTOR DB &nbsp;&nbsp; Pinecone 3072 cosine<br>
                KEYWORD &nbsp;&nbsp;&nbsp;&nbsp; BM25 (rank-bm25)<br>
                FUSION &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Reciprocal Rank Fusion<br>
                EMBED &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; gemini-embedding-001<br>
                LLM PRIMARY &nbsp;Gemini 2.5 Flash<br>
                LLM FALLBACK Groq llama-3.1-8b<br>
                EVAL &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; RAGAS + TruLens<br>
                SESSION &nbsp;&nbsp;&nbsp;&nbsp; {st.session_state.session_id}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="acard">
        <div class="acard-t">Roadmap</div>
        <div class="feat-grid">
            <div class="feat-item done"><span class="feat-dot"></span>Streaming Token Responses</div>
            <div class="feat-item done"><span class="feat-dot"></span>Hybrid Retrieval BM25 + Vector</div>
            <div class="feat-item done"><span class="feat-dot"></span>RAGAS Evaluation Pipeline</div>
            <div class="feat-item done"><span class="feat-dot"></span>TruLens Quality Tracing</div>
            <div class="feat-item"><span class="feat-dot"></span>Redis Conversation Memory</div>
            <div class="feat-item"><span class="feat-dot"></span>Multi-Agent LangGraph</div>
            <div class="feat-item"><span class="feat-dot"></span>Cross-encoder Re-ranking</div>
            <div class="feat-item"><span class="feat-dot"></span>DOCX HTML CSV Ingestion</div>
        </div>
    </div>
    """, unsafe_allow_html=True)