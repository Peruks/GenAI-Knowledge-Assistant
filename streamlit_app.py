import streamlit as st
import requests
import uuid
import time

# ------------------------------------------------
# Backend Configuration
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
# Ultra Premium CSS
# ------------------------------------------------

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Geist+Mono:wght@300;400;500;600;700&family=Geist:wght@300;400;500;600;700;800;900&display=swap');

/* ═══════════════════════════════════════
   CSS VARIABLES
═══════════════════════════════════════ */
:root {
  --bg:        #03040a;
  --bg1:       #070a14;
  --bg2:       #0b0f1e;
  --bg3:       #0f1428;
  --border:    #111830;
  --border2:   #1a2040;
  --text:      #e4e8ff;
  --text2:     #7b82a8;
  --text3:     #3a4060;
  --accent:    #4f6ef7;
  --accent2:   #7c3aed;
  --green:     #10b981;
  --cyan:      #06b6d4;
  --amber:     #f59e0b;
  --red:       #ef4444;
  --glow:      rgba(79,110,247,0.15);
}

/* ═══════════════════════════════════════
   BASE
═══════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }

html, body {
    font-family: 'Geist', sans-serif !important;
    background: var(--bg) !important;
    color: var(--text) !important;
}

.stApp {
    background: var(--bg) !important;
    background-image:
        radial-gradient(ellipse 60% 40% at 50% -10%, rgba(79,110,247,0.06) 0%, transparent 60%),
        radial-gradient(ellipse 40% 30% at 100% 100%, rgba(124,58,237,0.04) 0%, transparent 50%),
        repeating-linear-gradient(
            0deg,
            transparent,
            transparent 39px,
            rgba(255,255,255,0.012) 39px,
            rgba(255,255,255,0.012) 40px
        ),
        repeating-linear-gradient(
            90deg,
            transparent,
            transparent 39px,
            rgba(255,255,255,0.012) 39px,
            rgba(255,255,255,0.012) 40px
        );
    background-attachment: fixed !important;
}

/* ═══════════════════════════════════════
   HIDE STREAMLIT CHROME
═══════════════════════════════════════ */
#MainMenu, footer { visibility: hidden !important; }
header { visibility: hidden !important; }
.stDeployButton { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }

.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    max-width: 1100px !important;
}

/* ═══════════════════════════════════════
   TYPOGRAPHY OVERRIDES
═══════════════════════════════════════ */
p, span, div, label, li {
    font-family: 'Geist', sans-serif !important;
    color: var(--text) !important;
}

code, pre, .mono {
    font-family: 'Geist Mono', monospace !important;
}

/* ═══════════════════════════════════════
   TOP BAR
═══════════════════════════════════════ */
.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 0 20px 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 32px;
    animation: fadedown 0.5s ease;
}

.topbar-left {
    display: flex;
    align-items: center;
    gap: 12px;
}

.logo-hex {
    width: 38px;
    height: 38px;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
    display: grid;
    place-items: center;
    font-family: 'Geist Mono', monospace !important;
    font-weight: 700;
    font-size: 0.8rem;
    color: #fff !important;
    flex-shrink: 0;
}

.brand-name {
    font-family: 'Geist', sans-serif !important;
    font-weight: 800;
    font-size: 1.05rem;
    letter-spacing: 0.06em;
    color: var(--text) !important;
}

.brand-ver {
    font-family: 'Geist Mono', monospace !important;
    font-size: 0.58rem;
    color: var(--text3) !important;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-top: 2px;
}

.topbar-right {
    display: flex;
    align-items: center;
    gap: 10px;
}

.status-pill {
    display: flex;
    align-items: center;
    gap: 7px;
    background: rgba(16,185,129,0.06);
    border: 1px solid rgba(16,185,129,0.15);
    border-radius: 99px;
    padding: 5px 14px;
    font-family: 'Geist Mono', monospace !important;
    font-size: 0.62rem;
    color: var(--green) !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.pulse {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--green);
    animation: pulsebeat 2s ease-in-out infinite;
}

@keyframes pulsebeat {
    0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(16,185,129,0.6); }
    50% { opacity: 0.6; box-shadow: 0 0 0 5px rgba(16,185,129,0); }
}

/* ═══════════════════════════════════════
   HERO
═══════════════════════════════════════ */
.hero {
    text-align: center;
    padding: 20px 0 28px 0;
    animation: fadeup 0.6s ease;
}

.hero-eyebrow {
    font-family: 'Geist Mono', monospace !important;
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--accent) !important;
    margin-bottom: 14px;
}

.hero-title {
    font-family: 'Geist', sans-serif !important;
    font-weight: 900;
    font-size: 3rem;
    letter-spacing: -0.05em;
    line-height: 1.0;
    color: var(--text) !important;
    margin: 0 0 6px 0;
}

.hero-title .glow-word {
    background: linear-gradient(90deg, #6080ff 0%, #a78bfa 50%, #38bdf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    filter: drop-shadow(0 0 20px rgba(96,128,255,0.3));
}

.hero-desc {
    font-family: 'Geist Mono', monospace !important;
    font-size: 0.72rem;
    color: var(--text3) !important;
    letter-spacing: 0.06em;
    margin: 10px 0 16px 0;
}

.hero-tags {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 6px;
}

.htag {
    font-family: 'Geist Mono', monospace !important;
    font-size: 0.6rem;
    color: var(--text3) !important;
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 3px 10px;
    letter-spacing: 0.06em;
}

/* ═══════════════════════════════════════
   METRIC CARDS
═══════════════════════════════════════ */
.metrics {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin: 24px 0;
    animation: fadeup 0.7s ease;
}

.mcard {
    background: var(--bg1);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px 14px;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s, transform 0.2s;
}

.mcard::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent-color, var(--accent)), transparent);
    opacity: 0.6;
}

.mcard:nth-child(1) { --accent-color: var(--accent); }
.mcard:nth-child(2) { --accent-color: var(--cyan); }
.mcard:nth-child(3) { --accent-color: var(--green); }
.mcard:nth-child(4) { --accent-color: var(--amber); }

.mcard:hover {
    border-color: var(--border2);
    transform: translateY(-2px);
}

.mval {
    font-family: 'Geist', sans-serif !important;
    font-weight: 800;
    font-size: 2rem;
    line-height: 1;
    margin-bottom: 5px;
}

.mval.v1 { color: var(--accent) !important; }
.mval.v2 { color: var(--cyan) !important; }
.mval.v3 { color: var(--green) !important; }
.mval.v4 { color: var(--amber) !important; }

.mlbl {
    font-family: 'Geist Mono', monospace !important;
    font-size: 0.58rem;
    color: var(--text3) !important;
    text-transform: uppercase;
    letter-spacing: 0.12em;
}

/* ═══════════════════════════════════════
   TABS
═══════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--border) !important;
    gap: 0 !important;
    margin-bottom: 24px !important;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border: none !important;
    border-bottom: 1px solid transparent !important;
    color: var(--text3) !important;
    font-family: 'Geist Mono', monospace !important;
    font-size: 0.72rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 10px 22px !important;
    transition: all 0.2s !important;
}

.stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom: 1px solid var(--accent) !important;
    background: transparent !important;
}

.stTabs [data-baseweb="tab"]:hover {
    color: var(--text) !important;
}

.stTabs [data-baseweb="tab-highlight"] { display: none !important; }

/* ═══════════════════════════════════════
   CHAT MESSAGES
═══════════════════════════════════════ */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 2px 0 !important;
}

.umsg {
    background: linear-gradient(135deg, rgba(79,110,247,0.12), rgba(124,58,237,0.08));
    border: 1px solid rgba(79,110,247,0.2);
    border-radius: 12px 12px 4px 12px;
    padding: 14px 18px;
    margin: 8px 0;
    font-size: 0.9rem;
    line-height: 1.6;
    color: var(--text) !important;
    animation: fadeup 0.25s ease;
    max-width: 85%;
    margin-left: auto;
}

.amsg {
    background: var(--bg1);
    border: 1px solid var(--border);
    border-radius: 12px 12px 12px 4px;
    padding: 16px 18px;
    margin: 8px 0;
    font-size: 0.9rem;
    line-height: 1.7;
    color: var(--text) !important;
    animation: fadeup 0.25s ease;
    max-width: 90%;
    position: relative;
}

.amsg::before {
    content: '⬡';
    position: absolute;
    top: 12px;
    left: -24px;
    font-size: 0.7rem;
    color: var(--accent) !important;
    opacity: 0.5;
}

/* ═══════════════════════════════════════
   RESPONSE META
═══════════════════════════════════════ */
.rmeta {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-family: 'Geist Mono', monospace !important;
    font-size: 0.6rem;
    color: var(--text3) !important;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 3px 10px;
    margin-top: 8px;
    letter-spacing: 0.05em;
}

.rdot {
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background: var(--green);
}

/* ═══════════════════════════════════════
   SOURCE CHUNKS
═══════════════════════════════════════ */
.schunk {
    background: var(--bg);
    border: 1px solid var(--border);
    border-left: 2px solid var(--accent);
    border-radius: 6px;
    padding: 12px 16px;
    margin: 6px 0;
}

.schunk-label {
    font-family: 'Geist Mono', monospace !important;
    font-size: 0.55rem;
    color: var(--accent) !important;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    margin-bottom: 6px;
}

.schunk-text {
    font-family: 'Geist Mono', monospace !important;
    font-size: 0.7rem;
    color: var(--text3) !important;
    line-height: 1.7;
}

/* ═══════════════════════════════════════
   EMPTY STATE
═══════════════════════════════════════ */
.empty-state {
    text-align: center;
    padding: 5rem 2rem;
    animation: fadeup 0.5s ease;
}

.empty-glyph {
    font-family: 'Geist Mono', monospace !important;
    font-size: 3rem;
    color: var(--border2) !important;
    margin-bottom: 16px;
    display: block;
    animation: floatglyph 3s ease-in-out infinite;
}

@keyframes floatglyph {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-8px); }
}

.empty-title {
    font-family: 'Geist', sans-serif !important;
    font-weight: 700;
    font-size: 1.1rem;
    color: var(--text3) !important;
    margin-bottom: 8px;
}

.empty-hint {
    font-family: 'Geist Mono', monospace !important;
    font-size: 0.65rem;
    color: var(--border2) !important;
    letter-spacing: 0.05em;
}

/* ═══════════════════════════════════════
   CHAT INPUT
═══════════════════════════════════════ */
[data-testid="stChatInput"] {
    background: var(--bg1) !important;
    border: 1px solid var(--border2) !important;
    border-radius: 10px !important;
    transition: border-color 0.2s !important;
}

[data-testid="stChatInput"]:focus-within {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(79,110,247,0.08) !important;
}

[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: var(--text) !important;
    font-family: 'Geist', sans-serif !important;
    font-size: 0.9rem !important;
    caret-color: var(--accent) !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: var(--text3) !important;
}

/* ═══════════════════════════════════════
   EXPANDER
═══════════════════════════════════════ */
.streamlit-expanderHeader {
    background: var(--bg1) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    font-family: 'Geist Mono', monospace !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.08em !important;
    color: var(--text3) !important;
    text-transform: uppercase !important;
}

.streamlit-expanderContent {
    background: var(--bg) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
}

/* ═══════════════════════════════════════
   BUTTONS
═══════════════════════════════════════ */
.stButton > button {
    background: var(--bg1) !important;
    border: 1px solid var(--border2) !important;
    color: var(--text2) !important;
    font-family: 'Geist Mono', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    border-radius: 6px !important;
    padding: 8px 18px !important;
    transition: all 0.15s ease !important;
}

.stButton > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    background: rgba(79,110,247,0.05) !important;
}

/* ═══════════════════════════════════════
   FILE UPLOADER
═══════════════════════════════════════ */
[data-testid="stFileUploaderDropzone"] {
    background: var(--bg1) !important;
    border: 1px dashed var(--border2) !important;
    border-radius: 10px !important;
    transition: border-color 0.2s !important;
}

[data-testid="stFileUploaderDropzone"]:hover {
    border-color: var(--accent) !important;
}

[data-testid="stFileUploaderDropzone"] p,
[data-testid="stFileUploaderDropzone"] span,
[data-testid="stFileUploaderDropzone"] small {
    font-family: 'Geist Mono', monospace !important;
    color: var(--text3) !important;
    font-size: 0.7rem !important;
}

/* ═══════════════════════════════════════
   ALERTS
═══════════════════════════════════════ */
[data-testid="stAlert"] {
    font-family: 'Geist Mono', monospace !important;
    font-size: 0.72rem !important;
    border-radius: 6px !important;
}

/* ═══════════════════════════════════════
   SPINNER
═══════════════════════════════════════ */
.stSpinner > div {
    border-top-color: var(--accent) !important;
}

/* ═══════════════════════════════════════
   ABOUT CARDS
═══════════════════════════════════════ */
.acard {
    background: var(--bg1);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 22px;
    margin-bottom: 12px;
    position: relative;
    overflow: hidden;
}

.acard::after {
    content: '';
    position: absolute;
    top: 0; right: 0;
    width: 60px; height: 60px;
    background: radial-gradient(circle, rgba(79,110,247,0.06), transparent 70%);
    pointer-events: none;
}

.acard-title {
    font-family: 'Geist', sans-serif !important;
    font-weight: 700;
    font-size: 0.85rem;
    color: var(--text) !important;
    letter-spacing: -0.01em;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.acard-title::before {
    content: '';
    display: inline-block;
    width: 3px;
    height: 14px;
    background: var(--accent);
    border-radius: 2px;
    flex-shrink: 0;
}

.acard-body {
    font-family: 'Geist Mono', monospace !important;
    font-size: 0.68rem;
    color: var(--text3) !important;
    line-height: 2.2;
}

.feat-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
}

.feat-item {
    font-family: 'Geist Mono', monospace !important;
    font-size: 0.62rem;
    color: var(--text3) !important;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 9px 12px;
    display: flex;
    align-items: center;
    gap: 8px;
    transition: border-color 0.2s;
}

.feat-item:hover { border-color: var(--border2); }

.feat-dot {
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background: var(--accent);
    flex-shrink: 0;
}

/* ═══════════════════════════════════════
   UPLOAD SECTION
═══════════════════════════════════════ */
.up-header {
    margin-bottom: 20px;
}

.up-title {
    font-family: 'Geist', sans-serif !important;
    font-weight: 700;
    font-size: 0.95rem;
    color: var(--text) !important;
    margin-bottom: 4px;
}

.up-sub {
    font-family: 'Geist Mono', monospace !important;
    font-size: 0.65rem;
    color: var(--text3) !important;
    letter-spacing: 0.04em;
}

.up-note {
    font-family: 'Geist Mono', monospace !important;
    font-size: 0.62rem;
    color: var(--text3) !important;
    background: var(--bg);
    border: 1px solid var(--border);
    border-left: 2px solid rgba(79,110,247,0.5);
    border-radius: 0 6px 6px 0;
    padding: 10px 14px;
    margin-top: 12px;
    line-height: 1.9;
}

.up-stats {
    background: var(--bg1);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px;
}

.up-stats-title {
    font-family: 'Geist Mono', monospace !important;
    font-size: 0.58rem;
    color: var(--text3) !important;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 12px;
}

.doc-entry {
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: 'Geist Mono', monospace !important;
    font-size: 0.65rem;
    color: var(--green) !important;
    padding: 5px 0;
    border-bottom: 1px solid var(--border);
}

.doc-entry:last-child { border-bottom: none; }

.doc-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: var(--green);
    flex-shrink: 0;
}

.session-info {
    font-family: 'Geist Mono', monospace !important;
    font-size: 0.58rem;
    color: var(--text3) !important;
    margin-top: 14px;
    padding-top: 12px;
    border-top: 1px solid var(--border);
    line-height: 1.9;
}

/* ═══════════════════════════════════════
   ANIMATIONS
═══════════════════════════════════════ */
@keyframes fadeup {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}

@keyframes fadedown {
    from { opacity: 0; transform: translateY(-8px); }
    to   { opacity: 1; transform: translateY(0); }
}

</style>
""", unsafe_allow_html=True)


# ------------------------------------------------
# Session State
# ------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = f"nx_{str(uuid.uuid4())[:8]}"
if "questions" not in st.session_state:
    st.session_state.questions = 0
if "time_total" not in st.session_state:
    st.session_state.time_total = 0.0
if "sources_total" not in st.session_state:
    st.session_state.sources_total = 0
if "uploaded_docs" not in st.session_state:
    st.session_state.uploaded_docs = []


# ------------------------------------------------
# Top Bar
# ------------------------------------------------

st.markdown(f"""
<div class="topbar">
    <div class="topbar-left">
        <div class="logo-hex">NX</div>
        <div>
            <div class="brand-name">NEXUS</div>
            <div class="brand-ver">Enterprise Knowledge v2.0</div>
        </div>
    </div>
    <div class="topbar-right">
        <div class="status-pill">
            <span class="pulse"></span>
            System Online
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ------------------------------------------------
# Hero
# ------------------------------------------------

st.markdown("""
<div class="hero">
    <div class="hero-eyebrow">// RAG · VECTOR SEARCH · GUARDRAILS</div>
    <h1 class="hero-title">
        Enterprise <span class="glow-word">Knowledge</span> OS
    </h1>
    <div class="hero-desc">
        GEMINI EMBEDDINGS &nbsp;·&nbsp; PINECONE VECTOR DB &nbsp;·&nbsp; REAL-TIME RAG PIPELINE
    </div>
    <div class="hero-tags">
        <span class="htag">gemini-embedding-001</span>
        <span class="htag">3072-dim vectors</span>
        <span class="htag">cosine similarity</span>
        <span class="htag">guardrail filter</span>
        <span class="htag">session memory</span>
        <span class="htag">document upload</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ------------------------------------------------
# Metrics
# ------------------------------------------------

avg = st.session_state.time_total / st.session_state.questions if st.session_state.questions > 0 else 0.0

st.markdown(f"""
<div class="metrics">
    <div class="mcard">
        <div class="mval v1">{st.session_state.questions}</div>
        <div class="mlbl">Queries</div>
    </div>
    <div class="mcard">
        <div class="mval v2">{len(st.session_state.messages) // 2}</div>
        <div class="mlbl">Exchanges</div>
    </div>
    <div class="mcard">
        <div class="mval v3">{avg:.1f}s</div>
        <div class="mlbl">Avg Latency</div>
    </div>
    <div class="mcard">
        <div class="mval v4">{st.session_state.sources_total}</div>
        <div class="mlbl">Chunks Retrieved</div>
    </div>
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

    # Message history
    if not st.session_state.messages:
        st.markdown("""
        <div class="empty-state">
            <span class="empty-glyph">⬡</span>
            <div class="empty-title">Knowledge base is ready</div>
            <div class="empty-hint">
                Send a query to begin &nbsp;·&nbsp;
                Upload documents in INGEST tab &nbsp;·&nbsp;
                Session memory active
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                if msg["role"] == "user":
                    st.markdown(
                        f"<div class='umsg'>{msg['content']}</div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"<div class='amsg'>{msg['content']}</div>",
                        unsafe_allow_html=True
                    )
                    rt = msg.get("response_time", 0)
                    sc = msg.get("source_count", 0)
                    if rt:
                        st.markdown(f"""
                        <div class="rmeta">
                            <span class="rdot"></span>
                            {rt:.2f}s latency &nbsp;·&nbsp; {sc} chunk{'s' if sc != 1 else ''} retrieved
                        </div>
                        """, unsafe_allow_html=True)

                    srcs = msg.get("sources", [])
                    if srcs:
                        with st.expander(f"View {len(srcs)} retrieved chunk(s)"):
                            for i, src in enumerate(srcs, 1):
                                st.markdown(f"""
                                <div class="schunk">
                                    <div class="schunk-label">Chunk {i:02d}</div>
                                    <div class="schunk-text">{src}</div>
                                </div>
                                """, unsafe_allow_html=True)

    # Chat input
    question = st.chat_input("Enter query...")

    if question:
        st.session_state.questions += 1
        st.session_state.messages.append({
            "role": "user",
            "content": question,
            "sources": []
        })

        with st.chat_message("user"):
            st.markdown(
                f"<div class='umsg'>{question}</div>",
                unsafe_allow_html=True
            )

        with st.chat_message("assistant"):
            with st.spinner(""):
                try:
                    t0 = time.time()
                    payload = {
                        "question": question,
                        "session_id": st.session_state.session_id
                    }
                    res = requests.post(ASK_URL, json=payload, timeout=30)
                    elapsed = time.time() - t0

                    if res.status_code == 200:
                        data    = res.json()
                        answer  = data.get("answer", "No answer returned.")
                        sources = data.get("sources", [])

                        st.session_state.time_total    += elapsed
                        st.session_state.sources_total += len(sources)

                        st.markdown(
                            f"<div class='amsg'>{answer}</div>",
                            unsafe_allow_html=True
                        )

                        st.markdown(f"""
                        <div class="rmeta">
                            <span class="rdot"></span>
                            {elapsed:.2f}s latency &nbsp;·&nbsp; {len(sources)} chunk{'s' if len(sources) != 1 else ''} retrieved
                        </div>
                        """, unsafe_allow_html=True)

                        if sources:
                            with st.expander(f"View {len(sources)} retrieved chunk(s)"):
                                for i, src in enumerate(sources, 1):
                                    st.markdown(f"""
                                    <div class="schunk">
                                        <div class="schunk-label">Chunk {i:02d}</div>
                                        <div class="schunk-text">{src}</div>
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
                        err = f"Backend returned {res.status_code}"
                        st.error(err)
                        st.session_state.messages.append({
                            "role": "assistant", "content": err,
                            "sources": [], "response_time": 0, "source_count": 0
                        })

                except requests.exceptions.Timeout:
                    err = "Request timed out — backend may be waking up. Try again."
                    st.warning(err)
                    st.session_state.messages.append({
                        "role": "assistant", "content": err,
                        "sources": [], "response_time": 0, "source_count": 0
                    })

                except requests.exceptions.ConnectionError:
                    err = "Cannot reach backend. Check server status."
                    st.error(err)
                    st.session_state.messages.append({
                        "role": "assistant", "content": err,
                        "sources": [], "response_time": 0, "source_count": 0
                    })

                except Exception as e:
                    err = f"Error: {str(e)}"
                    st.error(err)
                    st.session_state.messages.append({
                        "role": "assistant", "content": err,
                        "sources": [], "response_time": 0, "source_count": 0
                    })

    # Clear button
    col_btn, _ = st.columns([1, 6])
    with col_btn:
        if st.button("Clear Session"):
            st.session_state.messages     = []
            st.session_state.questions    = 0
            st.session_state.time_total   = 0.0
            st.session_state.sources_total = 0
            st.session_state.session_id   = f"nx_{str(uuid.uuid4())[:8]}"
            st.rerun()


# ════════════════════════════════════════════════
# TAB 2 — INGEST
# ════════════════════════════════════════════════

with tab2:

    st.markdown("""
    <div class="up-header">
        <div class="up-title">Document Ingestion Pipeline</div>
        <div class="up-sub">
            PDF · TXT &nbsp;·&nbsp; Max 5MB recommended &nbsp;·&nbsp;
            Page-by-page processing &nbsp;·&nbsp; Auto-chunked at 500 tokens
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])

    with col1:
        uploaded_file = st.file_uploader(
            "Drop document",
            type=["pdf", "txt"],
            label_visibility="collapsed"
        )

        if uploaded_file:
            size_kb = len(uploaded_file.getvalue()) / 1024
            size_mb = size_kb / 1024

            if size_mb > 5:
                st.warning(
                    f"File is {size_mb:.1f}MB. Large files may timeout on free-tier. "
                    f"Recommended: keep under 5MB."
                )

            st.markdown(f"""
            <div style="font-family: 'Geist Mono', monospace; font-size: 0.68rem;
                        color: var(--accent); background: var(--bg1);
                        border: 1px solid var(--border2); border-radius: 6px;
                        padding: 10px 14px; margin: 10px 0;">
                &#9679; &nbsp; {uploaded_file.name} &nbsp;·&nbsp; {size_kb:.0f} KB
            </div>
            """, unsafe_allow_html=True)

            if st.button("Run Ingestion Pipeline"):
                with st.spinner("Ingesting document..."):
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
                                f"Ingestion complete — {data.get('total_chunks', 0)} chunks indexed"
                            )
                            if uploaded_file.name not in st.session_state.uploaded_docs:
                                st.session_state.uploaded_docs.append(uploaded_file.name)
                        elif resp.status_code == 413:
                            st.error("File too large. Maximum 10MB allowed.")
                        elif resp.status_code == 500:
                            st.error(
                                "Server error — file may exceed free-tier memory (512MB). "
                                "Try a smaller or compressed file."
                            )
                        else:
                            st.error(f"Upload failed: {resp.status_code}")

                    except requests.exceptions.Timeout:
                        st.warning("Timeout — large files take longer. Try again.")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

        st.markdown("""
        <div class="up-note">
            Documents are processed page-by-page using RecursiveCharacterTextSplitter<br>
            (chunk_size=500, overlap=100) to stay within 512MB free-tier RAM.<br>
            Embeddings via gemini-embedding-001 (3072 dims) stored in Pinecone.
        </div>
        """, unsafe_allow_html=True)

    with col2:
        indexed_html = ""
        if st.session_state.uploaded_docs:
            for d in st.session_state.uploaded_docs:
                indexed_html += f"""
                <div class="doc-entry">
                    <span class="doc-dot"></span>{d}
                </div>"""
        else:
            indexed_html = """
            <div style="font-family: 'Geist Mono', monospace; font-size: 0.62rem;
                        color: var(--border2);">No documents ingested this session</div>"""

        st.markdown(f"""
        <div class="up-stats">
            <div class="up-stats-title">Indexed This Session</div>
            {indexed_html}
            <div class="session-info">
                SESSION ID<br>
                <span style="color: var(--text3);">{st.session_state.session_id}</span>
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
            <div class="acard-title">RAG Pipeline</div>
            <div class="acard-body">
                USER QUERY<br>
                &darr;&nbsp; embed via gemini-embedding-001<br>
                VECTOR SEARCH<br>
                &darr;&nbsp; pinecone top-k=5, cosine similarity<br>
                GUARDRAIL FILTER<br>
                &darr;&nbsp; score threshold = 0.30<br>
                CONTEXT ASSEMBLY<br>
                &darr;&nbsp; join top chunks<br>
                LLM GENERATION<br>
                &darr;&nbsp; gemini-2.5-flash with context<br>
                ANSWER + CITATIONS
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="acard">
            <div class="acard-title">Stack</div>
            <div class="acard-body">
                BACKEND &nbsp;&nbsp;&nbsp;&nbsp; FastAPI + Uvicorn<br>
                HOST &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Railway (free tier)<br>
                FRONTEND &nbsp;&nbsp;&nbsp; Streamlit Cloud<br>
                VECTOR DB &nbsp;&nbsp; Pinecone serverless<br>
                DIMS &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 3072 cosine<br>
                EMBED MODEL &nbsp;gemini-embedding-001<br>
                LLM &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Gemini 2.5 Flash<br>
                CHUNKER &nbsp;&nbsp;&nbsp;&nbsp; RecursiveCharacterSplitter<br>
                SESSION &nbsp;&nbsp;&nbsp;&nbsp; {st.session_state.session_id}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="acard">
        <div class="acard-title">Roadmap</div>
        <div class="feat-grid">
            <div class="feat-item"><span class="feat-dot"></span>Multi-document Knowledge Base</div>
            <div class="feat-item"><span class="feat-dot"></span>RAG Evaluation (RAGAS)</div>
            <div class="feat-item"><span class="feat-dot"></span>Hybrid Retrieval BM25 + Vector</div>
            <div class="feat-item"><span class="feat-dot"></span>Multi-Agent Workflow (LangGraph)</div>
            <div class="feat-item"><span class="feat-dot"></span>Streaming Token Responses</div>
            <div class="feat-item"><span class="feat-dot"></span>Observability + Tracing</div>
            <div class="feat-item"><span class="feat-dot"></span>Redis Conversation Memory</div>
            <div class="feat-item"><span class="feat-dot"></span>DOCX / HTML / CSV Ingestion</div>
        </div>
    </div>
    """, unsafe_allow_html=True)