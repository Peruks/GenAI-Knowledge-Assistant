import streamlit as st
import requests
import uuid
import time

# ------------------------------------------------
# Backend
# ------------------------------------------------

API_BASE   = "https://genai-knowledge-api-production.up.railway.app"
ASK_URL    = f"{API_BASE}/ask"
UPLOAD_URL = f"{API_BASE}/upload"

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

@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Space+Mono:ital,wght@0,400;0,700;1,400&display=swap');

:root {
    --bg:    #030508;
    --bg1:   #070b15;
    --bg2:   #0b1020;
    --bg3:   #0f1628;
    --b0:    #0c1120;
    --b1:    #131c35;
    --b2:    #1a2540;
    --b3:    #222e50;
    --txt:   #dde3ff;
    --txt2:  #6b75a0;
    --txt3:  #2e3560;
    --acc:   #4f6ef7;
    --acc2:  #7c3aed;
    --grn:   #0ea472;
    --cyn:   #0891b2;
    --amb:   #d97706;
    --user-bg: rgba(79,110,247,0.10);
    --user-br: rgba(79,110,247,0.25);
    --bot-bg:  #080d1a;
    --bot-br:  #131c35;
}

*, *::before, *::after { box-sizing: border-box; }

html, body, .stApp {
    font-family: 'Space Grotesk', sans-serif !important;
    background: var(--bg) !important;
    color: var(--txt) !important;
}

.stApp {
    background-image:
        radial-gradient(ellipse 70% 40% at 50% -8%,
            rgba(79,110,247,0.08) 0%, transparent 60%),
        linear-gradient(rgba(79,110,247,0.018) 1px, transparent 1px),
        linear-gradient(90deg, rgba(79,110,247,0.018) 1px, transparent 1px) !important;
    background-size: 100% 100%, 48px 48px, 48px 48px !important;
    background-attachment: fixed !important;
}

/* hide chrome */
#MainMenu, footer { visibility: hidden !important; }
header { visibility: hidden !important; }
.stDeployButton { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }

/* kill ALL streamlit chat avatars */
[data-testid="chatAvatarIcon-user"],
[data-testid="chatAvatarIcon-assistant"],
[data-testid="stChatMessageAvatarUser"],
[data-testid="stChatMessageAvatarAssistant"] {
    display: none !important;
}

[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    gap: 0 !important;
}

.block-container {
    padding-top: 1.8rem !important;
    max-width: 1060px !important;
}

/* ══════════════════════════════
   TOPBAR
══════════════════════════════ */
.topbar {
    display: flex; align-items: center;
    justify-content: space-between;
    padding-bottom: 18px;
    border-bottom: 1px solid var(--b1);
    margin-bottom: 28px;
    animation: slidedown .5s ease both;
}

.tb-left { display: flex; align-items: center; gap: 12px; }

.hex {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, var(--acc), var(--acc2));
    clip-path: polygon(50% 0%,100% 25%,100% 75%,50% 100%,0% 75%,0% 25%);
    display: grid; place-items: center;
    font-family: 'Space Mono', monospace !important;
    font-weight: 700; font-size: 0.7rem;
    color: #fff !important; flex-shrink: 0;
}

.brand-name {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700; font-size: 1rem;
    letter-spacing: 0.06em; color: var(--txt) !important;
}

.brand-sub {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.52rem; color: var(--txt3) !important;
    letter-spacing: 0.12em; text-transform: uppercase;
}

.online-chip {
    display: flex; align-items: center; gap: 7px;
    background: rgba(14,164,114,0.07);
    border: 1px solid rgba(14,164,114,0.18);
    border-radius: 99px; padding: 5px 14px;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.58rem; color: var(--grn) !important;
    letter-spacing: 0.1em; text-transform: uppercase;
}

.blink {
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--grn);
    animation: blinkbeat 2s ease-in-out infinite;
}

@keyframes blinkbeat {
    0%,100% { opacity:1; box-shadow:0 0 0 0 rgba(14,164,114,.5); }
    50%      { opacity:.5; box-shadow:0 0 0 6px rgba(14,164,114,0); }
}

/* ══════════════════════════════
   HERO
══════════════════════════════ */
.hero {
    text-align: center;
    padding: 22px 0 18px;
    animation: slideup .6s ease both;
}

.hero-eye {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.58rem; letter-spacing: 0.22em;
    text-transform: uppercase; color: var(--acc) !important;
    margin-bottom: 12px;
}

.hero-h1 {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700; font-size: 2.6rem;
    letter-spacing: -0.04em; line-height: 1.06;
    color: var(--txt) !important; margin-bottom: 12px;
}

.hero-h1 .hl {
    background: linear-gradient(90deg,#6080ff,#a78bfa 55%,#38bdf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    filter: drop-shadow(0 0 28px rgba(96,128,255,.28));
}

.hero-mono {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.62rem; letter-spacing: 0.08em;
    color: var(--txt3) !important; margin-bottom: 14px;
}

.pills {
    display: flex; justify-content: center;
    flex-wrap: wrap; gap: 6px;
}

.pill {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.56rem; color: var(--txt3) !important;
    background: var(--bg1); border: 1px solid var(--b1);
    border-radius: 4px; padding: 3px 10px;
    letter-spacing: 0.05em;
}

/* ══════════════════════════════
   METRICS
══════════════════════════════ */
.metrics {
    display: grid; grid-template-columns: repeat(4,1fr);
    gap: 10px; margin: 20px 0;
    animation: slideup .7s ease both;
}

.mc {
    background: var(--bg1); border: 1px solid var(--b1);
    border-radius: 10px; padding: 16px 12px;
    text-align: center; position: relative; overflow: hidden;
    transition: transform .2s, border-color .2s;
}

.mc:hover { transform: translateY(-3px); border-color: var(--b2); }

.mc::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, var(--c), transparent);
    opacity: .8;
}

.mc:nth-child(1) { --c: #4f6ef7; }
.mc:nth-child(2) { --c: #0891b2; }
.mc:nth-child(3) { --c: #0ea472; }
.mc:nth-child(4) { --c: #d97706; }

.mv {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700; font-size: 1.9rem; line-height: 1;
}

.mv.a { color: #4f6ef7 !important; }
.mv.b { color: #0891b2 !important; }
.mv.c { color: #0ea472 !important; }
.mv.d { color: #d97706 !important; }

.ml {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.52rem; color: var(--txt3) !important;
    text-transform: uppercase; letter-spacing: 0.12em; margin-top: 5px;
}

/* ══════════════════════════════
   TABS
══════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--b1) !important;
    gap: 0 !important; margin-bottom: 22px !important;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border: none !important;
    border-bottom: 1px solid transparent !important;
    color: var(--txt3) !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.65rem !important; font-weight: 400 !important;
    letter-spacing: 0.12em !important; text-transform: uppercase !important;
    padding: 10px 22px !important; transition: color .2s !important;
}

.stTabs [aria-selected="true"] {
    color: var(--acc) !important;
    border-bottom: 1px solid var(--acc) !important;
}

.stTabs [data-baseweb="tab-highlight"] { display: none !important; }

/* ══════════════════════════════
   CHAT AREA
══════════════════════════════ */
.chat-feed {
    display: flex; flex-direction: column;
    gap: 20px; padding: 8px 0 16px;
}

/* user message */
.msg-u-wrap {
    display: flex; justify-content: flex-end;
    animation: faderight .3s ease both;
}

.msg-u {
    max-width: 74%;
    background: var(--user-bg);
    border: 1px solid var(--user-br);
    border-radius: 16px 16px 4px 16px;
    padding: 13px 18px;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.92rem; line-height: 1.65;
    color: var(--txt) !important;
}

.msg-u-lbl {
    text-align: right;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.52rem; letter-spacing: 0.12em;
    color: var(--acc) !important; text-transform: uppercase;
    margin-bottom: 5px;
}

/* bot message */
.msg-b-wrap {
    display: flex; justify-content: flex-start;
    animation: fadeleft .3s ease both;
}

.msg-b-inner { max-width: 84%; }

.msg-b-lbl {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.52rem; letter-spacing: 0.12em;
    color: var(--grn) !important; text-transform: uppercase;
    margin-bottom: 6px;
    display: flex; align-items: center; gap: 6px;
}

.msg-b-lbl-dot {
    width: 5px; height: 5px; border-radius: 50%;
    background: var(--grn); flex-shrink: 0;
}

.msg-b {
    background: var(--bot-bg);
    border: 1px solid var(--bot-br);
    border-radius: 4px 16px 16px 16px;
    padding: 15px 20px;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.92rem; line-height: 1.78;
    color: var(--txt) !important;
}

.msg-meta {
    display: inline-flex; align-items: center; gap: 8px;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.56rem; color: var(--txt3) !important;
    background: var(--bg); border: 1px solid var(--b0);
    border-radius: 4px; padding: 3px 10px; margin-top: 8px;
    letter-spacing: 0.05em;
}

.msg-meta-dot {
    width: 4px; height: 4px; border-radius: 50%;
    background: var(--grn);
}

/* source chunks */
.schunk {
    background: var(--bg);
    border: 1px solid var(--b1);
    border-left: 2px solid var(--acc);
    border-radius: 6px; padding: 12px 16px; margin: 7px 0;
}

.schunk-lbl {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.5rem; color: var(--acc) !important;
    text-transform: uppercase; letter-spacing: 0.15em; margin-bottom: 7px;
}

.schunk-txt {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.67rem; color: var(--txt2) !important; line-height: 1.75;
}

/* empty state */
.empty {
    text-align: center; padding: 5rem 2rem;
    animation: slideup .5s ease both;
}

.empty-glyph {
    font-size: 2.5rem; color: var(--b2) !important;
    display: block; margin-bottom: 16px;
    animation: floatit 3s ease-in-out infinite;
}

.empty-t {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600; font-size: 1rem;
    color: var(--txt3) !important; margin-bottom: 8px;
}

.empty-s {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.6rem; color: var(--b2) !important;
    letter-spacing: 0.05em;
}

/* ══════════════════════════════
   CHAT INPUT
══════════════════════════════ */
[data-testid="stChatInput"] {
    background: var(--bg1) !important;
    border: 1px solid var(--b2) !important;
    border-radius: 10px !important;
    transition: border-color .2s, box-shadow .2s !important;
    margin-top: 16px !important;
}

[data-testid="stChatInput"]:focus-within {
    border-color: var(--acc) !important;
    box-shadow: 0 0 0 3px rgba(79,110,247,.08) !important;
}

[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: var(--txt) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.9rem !important;
    caret-color: var(--acc) !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: var(--txt3) !important;
}

/* ══════════════════════════════
   EXPANDER
══════════════════════════════ */
.streamlit-expanderHeader {
    background: var(--bg1) !important;
    border: 1px solid var(--b1) !important;
    border-radius: 6px !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.6rem !important; letter-spacing: 0.08em !important;
    color: var(--txt3) !important; text-transform: uppercase !important;
}

.streamlit-expanderContent {
    background: var(--bg) !important;
    border: 1px solid var(--b1) !important;
    border-top: none !important;
}

/* ══════════════════════════════
   BUTTONS
══════════════════════════════ */
.stButton > button {
    background: var(--bg1) !important;
    border: 1px solid var(--b2) !important;
    color: var(--txt2) !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.62rem !important; letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    border-radius: 6px !important; padding: 8px 20px !important;
    transition: all .15s ease !important;
}

.stButton > button:hover {
    border-color: var(--acc) !important;
    color: var(--acc) !important;
    background: rgba(79,110,247,.05) !important;
}

/* ══════════════════════════════
   FILE UPLOADER
══════════════════════════════ */
[data-testid="stFileUploaderDropzone"] {
    background: var(--bg1) !important;
    border: 1px dashed var(--b2) !important;
    border-radius: 10px !important;
    transition: border-color .2s !important;
}

[data-testid="stFileUploaderDropzone"]:hover {
    border-color: var(--acc) !important;
}

[data-testid="stFileUploaderDropzone"] p,
[data-testid="stFileUploaderDropzone"] span,
[data-testid="stFileUploaderDropzone"] small {
    font-family: 'Space Mono', monospace !important;
    color: var(--txt3) !important; font-size: 0.66rem !important;
}

/* ══════════════════════════════
   ABOUT CARDS
══════════════════════════════ */
.acard {
    background: var(--bg1); border: 1px solid var(--b1);
    border-radius: 10px; padding: 22px; margin-bottom: 12px;
    position: relative; overflow: hidden;
    transition: border-color .2s, transform .2s;
}

.acard:hover { border-color: var(--b2); transform: translateY(-2px); }

.acard::after {
    content: '';
    position: absolute; top: 0; right: 0;
    width: 80px; height: 80px;
    background: radial-gradient(circle, rgba(79,110,247,.05), transparent 70%);
    pointer-events: none;
}

.acard-t {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700; font-size: 0.85rem;
    color: var(--txt) !important; margin-bottom: 16px;
    display: flex; align-items: center; gap: 8px;
}

.acard-t::before {
    content: '';
    display: inline-block; width: 3px; height: 14px;
    background: var(--acc); border-radius: 2px;
}

.acard-b {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.64rem; color: var(--txt3) !important; line-height: 2.2;
}

.feat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }

.feat-item {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.58rem; color: var(--txt3) !important;
    background: var(--bg); border: 1px solid var(--b1);
    border-radius: 6px; padding: 9px 12px;
    display: flex; align-items: center; gap: 8px;
    transition: border-color .2s;
}

.feat-item:hover { border-color: var(--b2); }
.feat-dot { width:4px; height:4px; border-radius:50%; background:var(--acc); flex-shrink:0; }

/* ══════════════════════════════
   UPLOAD
══════════════════════════════ */
.up-note {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.58rem; color: var(--txt3) !important;
    background: var(--bg); border: 1px solid var(--b1);
    border-left: 2px solid rgba(79,110,247,.5);
    border-radius: 0 6px 6px 0;
    padding: 10px 14px; margin-top: 12px; line-height: 1.9;
}

.up-stats {
    background: var(--bg1); border: 1px solid var(--b1);
    border-radius: 10px; padding: 18px;
}

.up-stats-t {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.52rem; color: var(--txt3) !important;
    text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 12px;
}

.doc-row {
    display: flex; align-items: center; gap: 8px;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.6rem; color: var(--grn) !important;
    padding: 5px 0; border-bottom: 1px solid var(--b0);
}

.doc-row:last-child { border-bottom: none; }
.doc-dot { width:4px; height:4px; border-radius:50%; background:var(--grn); flex-shrink:0; }

.sess-box {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.56rem; color: var(--txt3) !important;
    margin-top: 14px; padding-top: 12px;
    border-top: 1px solid var(--b0); line-height: 1.9;
}

/* ══════════════════════════════
   ALERTS + SPINNER
══════════════════════════════ */
[data-testid="stAlert"] {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.68rem !important; border-radius: 6px !important;
}

.stSpinner > div { border-top-color: var(--acc) !important; }

/* ══════════════════════════════
   KEYFRAMES
══════════════════════════════ */
@keyframes slidedown {
    from { opacity:0; transform:translateY(-10px); }
    to   { opacity:1; transform:translateY(0); }
}

@keyframes slideup {
    from { opacity:0; transform:translateY(10px); }
    to   { opacity:1; transform:translateY(0); }
}

@keyframes faderight {
    from { opacity:0; transform:translateX(14px); }
    to   { opacity:1; transform:translateX(0); }
}

@keyframes fadeleft {
    from { opacity:0; transform:translateX(-14px); }
    to   { opacity:1; transform:translateX(0); }
}

@keyframes floatit {
    0%,100% { transform:translateY(0); }
    50%      { transform:translateY(-10px); }
}

</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# Session State
# ------------------------------------------------

if "messages"      not in st.session_state: st.session_state.messages      = []
if "session_id"    not in st.session_state: st.session_state.session_id    = f"nx_{str(uuid.uuid4())[:8]}"
if "questions"     not in st.session_state: st.session_state.questions     = 0
if "time_total"    not in st.session_state: st.session_state.time_total    = 0.0
if "src_total"     not in st.session_state: st.session_state.src_total     = 0
if "uploaded_docs" not in st.session_state: st.session_state.uploaded_docs = []

# ------------------------------------------------
# Helper — safe HTML escape for chat content
# ------------------------------------------------

def safe(text: str) -> str:
    """Escape < > & so raw HTML never renders inside chat bubbles."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>"))

# ------------------------------------------------
# Top Bar
# ------------------------------------------------

st.markdown(f"""
<div class="topbar">
    <div class="tb-left">
        <div class="hex">NX</div>
        <div>
            <div class="brand-name">NEXUS</div>
            <div class="brand-sub">Enterprise Knowledge OS &nbsp;·&nbsp; v2.0</div>
        </div>
    </div>
    <div class="online-chip">
        <span class="blink"></span>System Online
    </div>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------
# Hero
# ------------------------------------------------

st.markdown("""
<div class="hero">
    <div class="hero-eye">// RAG · Vector Search · Guardrails · Session Memory</div>
    <div class="hero-h1">Enterprise <span class="hl">Knowledge</span> OS</div>
    <div class="hero-mono">
        GEMINI-EMBEDDING-001 &nbsp;·&nbsp; PINECONE 3072-DIM &nbsp;·&nbsp; GEMINI 2.5 FLASH + GROQ FALLBACK
    </div>
    <div class="pills">
        <span class="pill">cosine similarity</span>
        <span class="pill">score threshold 0.30</span>
        <span class="pill">top-k retrieval</span>
        <span class="pill">chunk size 500</span>
        <span class="pill">guardrail filter</span>
        <span class="pill">document upload</span>
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
    <div class="mc"><div class="mv b">{len(st.session_state.messages) // 2}</div><div class="ml">Exchanges</div></div>
    <div class="mc"><div class="mv c">{avg:.1f}s</div><div class="ml">Avg Latency</div></div>
    <div class="mc"><div class="mv d">{st.session_state.src_total}</div><div class="ml">Chunks Retrieved</div></div>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------
# Tabs
# ------------------------------------------------

tab1, tab2, tab3 = st.tabs(["CHAT", "INGEST", "SYSTEM"])


# ════════════════════════════════════════════════
# TAB 1 — CHAT
# ════════════════════════════════════════════════

with tab1:

    # ── Build pure HTML chat (no st.chat_message, no avatar bugs) ──
    if st.session_state.messages:

        html = "<div class='chat-feed'>"

        for msg in st.session_state.messages:

            if msg["role"] == "user":
                html += f"""
                <div class="msg-u-wrap">
                    <div>
                        <div class="msg-u-lbl">You</div>
                        <div class="msg-u">{safe(msg['content'])}</div>
                    </div>
                </div>"""

            else:
                rt = msg.get("response_time", 0)
                sc = msg.get("source_count", 0)
                meta_html = ""
                if rt:
                    meta_html = f"""
                    <div class="msg-meta">
                        <span class="msg-meta-dot"></span>
                        {rt:.2f}s &nbsp;·&nbsp; {sc} chunk{'s' if sc != 1 else ''} retrieved
                    </div>"""

                html += f"""
                <div class="msg-b-wrap">
                    <div class="msg-b-inner">
                        <div class="msg-b-lbl">
                            <span class="msg-b-lbl-dot"></span>NEXUS
                        </div>
                        <div class="msg-b">{safe(msg['content'])}</div>
                        {meta_html}
                    </div>
                </div>"""

        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

        # Source expanders — Streamlit component (not inside HTML)
        for i, msg in enumerate(st.session_state.messages):
            if msg["role"] == "assistant" and msg.get("sources"):
                srcs = msg["sources"]
                idx  = (i // 2) + 1
                with st.expander(f"Sources — Response {idx} ({len(srcs)} chunks)"):
                    for j, src in enumerate(srcs, 1):
                        st.markdown(f"""
                        <div class="schunk">
                            <div class="schunk-lbl">Chunk {j:02d}</div>
                            <div class="schunk-txt">{safe(src)}</div>
                        </div>
                        """, unsafe_allow_html=True)

    else:
        st.markdown("""
        <div class="empty">
            <span class="empty-glyph">⬡</span>
            <div class="empty-t">Knowledge base is ready</div>
            <div class="empty-s">
                Send a query below &nbsp;·&nbsp;
                Upload docs in INGEST tab &nbsp;·&nbsp;
                Session memory is active
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Chat input — always at bottom ──
    question = st.chat_input("Enter query...")

    if question:
        st.session_state.questions += 1
        st.session_state.messages.append({
            "role": "user", "content": question, "sources": []
        })

        with st.spinner(""):
            try:
                t0  = time.time()
                res = requests.post(
                    ASK_URL,
                    json={"question": question,
                          "session_id": st.session_state.session_id},
                    timeout=30
                )
                elapsed = time.time() - t0

                if res.status_code == 200:
                    data    = res.json()
                    answer  = data.get("answer", "No answer returned.")
                    sources = data.get("sources", [])
                    st.session_state.time_total += elapsed
                    st.session_state.src_total  += len(sources)
                    st.session_state.messages.append({
                        "role":          "assistant",
                        "content":       answer,
                        "sources":       sources,
                        "response_time": elapsed,
                        "source_count":  len(sources)
                    })
                else:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"Backend error {res.status_code}. Please try again.",
                        "sources": [], "response_time": 0, "source_count": 0
                    })

            except requests.exceptions.Timeout:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Request timed out. Backend may be waking up — try again.",
                    "sources": [], "response_time": 0, "source_count": 0
                })
            except requests.exceptions.ConnectionError:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Cannot reach backend. Check server status.",
                    "sources": [], "response_time": 0, "source_count": 0
                })
            except Exception as e:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Error: {str(e)}",
                    "sources": [], "response_time": 0, "source_count": 0
                })

        st.rerun()

    # Clear button
    col_c, _ = st.columns([1, 8])
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
        <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;
                    font-size:0.95rem;color:#dde3ff;margin-bottom:5px;">
            Document Ingestion Pipeline
        </div>
        <div style="font-family:'Space Mono',monospace;font-size:0.6rem;color:#2e3560;">
            PDF &nbsp;·&nbsp; TXT &nbsp;·&nbsp; Max 5MB recommended &nbsp;·&nbsp;
            Chunked at 500 tokens &nbsp;·&nbsp; gemini-embedding-001
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])

    with col1:
        uploaded_file = st.file_uploader(
            "Drop document here",
            type=["pdf", "txt"],
            label_visibility="collapsed"
        )

        if uploaded_file:
            size_kb = len(uploaded_file.getvalue()) / 1024
            size_mb = size_kb / 1024

            if size_mb > 5:
                st.warning(
                    f"File is {size_mb:.1f}MB — may timeout on free-tier. "
                    f"Recommended: keep under 5MB."
                )

            st.markdown(f"""
            <div style="font-family:'Space Mono',monospace;font-size:0.65rem;
                        color:#4f6ef7;background:#070b15;
                        border:1px solid #1a2540;border-radius:6px;
                        padding:10px 14px;margin:10px 0;">
                &#9679;&nbsp; {uploaded_file.name} &nbsp;·&nbsp; {size_kb:.0f} KB
            </div>
            """, unsafe_allow_html=True)

            if st.button("Run Ingestion Pipeline"):
                with st.spinner("Ingesting document..."):
                    try:
                        files = {"file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type
                        )}
                        resp = requests.post(UPLOAD_URL, files=files, timeout=180)

                        if resp.status_code == 200:
                            data = resp.json()
                            st.success(
                                f"Ingestion complete — "
                                f"{data.get('total_chunks', 0)} chunks indexed"
                            )
                            if uploaded_file.name not in st.session_state.uploaded_docs:
                                st.session_state.uploaded_docs.append(uploaded_file.name)
                        elif resp.status_code == 413:
                            st.error("File too large. Maximum 10MB allowed.")
                        elif resp.status_code == 500:
                            st.error(
                                "Server error — file may exceed free-tier memory. "
                                "Try a smaller file."
                            )
                        else:
                            st.error(f"Upload failed: {resp.status_code}")

                    except requests.exceptions.Timeout:
                        st.warning("Timeout — large files take longer. Try again.")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

        st.markdown("""
        <div class="up-note">
            Files processed page-by-page via RecursiveCharacterTextSplitter<br>
            (chunk_size=500, overlap=100) — stays within 512MB free-tier RAM.<br>
            Vectors stored in Pinecone serverless (3072 dims, cosine metric).
        </div>
        """, unsafe_allow_html=True)

    with col2:
        indexed_html = ""
        if st.session_state.uploaded_docs:
            for d in st.session_state.uploaded_docs:
                indexed_html += f"""
                <div class="doc-row">
                    <span class="doc-dot"></span>{d}
                </div>"""
        else:
            indexed_html = """
            <div style="font-family:'Space Mono',monospace;
                        font-size:0.6rem;color:#131c35;">
                No documents this session
            </div>"""

        st.markdown(f"""
        <div class="up-stats">
            <div class="up-stats-t">Indexed This Session</div>
            {indexed_html}
            <div class="sess-box">
                SESSION ID<br>
                <span style="color:#2e3560;">
                    {st.session_state.session_id}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════
# TAB 3 — SYSTEM
# ════════════════════════════════════════════════

with tab3:

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="acard">
            <div class="acard-t">RAG Pipeline</div>
            <div class="acard-b">
                USER QUERY<br>
                &darr;&nbsp; embed via gemini-embedding-001<br>
                VECTOR SEARCH<br>
                &darr;&nbsp; pinecone top-k=5, cosine<br>
                GUARDRAIL FILTER<br>
                &darr;&nbsp; score threshold = 0.30<br>
                CONTEXT ASSEMBLY<br>
                &darr;&nbsp; join top chunks into prompt<br>
                LLM GENERATION<br>
                &darr;&nbsp; gemini-2.5-flash (groq fallback)<br>
                ANSWER + CITATIONS
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="acard">
            <div class="acard-t">Stack</div>
            <div class="acard-b">
                BACKEND &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; FastAPI + Uvicorn<br>
                HOST &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Railway (free tier)<br>
                FRONTEND &nbsp;&nbsp;&nbsp;&nbsp; Streamlit Cloud<br>
                VECTOR DB &nbsp;&nbsp;&nbsp; Pinecone serverless<br>
                DIMENSIONS &nbsp;&nbsp; 3072 cosine<br>
                EMBED MODEL &nbsp;&nbsp;gemini-embedding-001<br>
                LLM PRIMARY &nbsp;&nbsp;Gemini 2.5 Flash<br>
                LLM FALLBACK &nbsp;Groq llama-3.1-8b<br>
                SESSION &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {st.session_state.session_id}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="acard">
        <div class="acard-t">Roadmap</div>
        <div class="feat-grid">
            <div class="feat-item"><span class="feat-dot"></span>Multi-document Knowledge Base</div>
            <div class="feat-item"><span class="feat-dot"></span>RAG Evaluation with RAGAS</div>
            <div class="feat-item"><span class="feat-dot"></span>Hybrid Retrieval BM25 + Vector</div>
            <div class="feat-item"><span class="feat-dot"></span>Multi-Agent Workflow LangGraph</div>
            <div class="feat-item"><span class="feat-dot"></span>Streaming Token Responses</div>
            <div class="feat-item"><span class="feat-dot"></span>Observability and Tracing</div>
            <div class="feat-item"><span class="feat-dot"></span>Redis Conversation Memory</div>
            <div class="feat-item"><span class="feat-dot"></span>DOCX HTML CSV Ingestion</div>
        </div>
    </div>
    """, unsafe_allow_html=True)