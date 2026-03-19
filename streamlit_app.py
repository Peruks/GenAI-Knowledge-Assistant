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

st.set_page_config(
    page_title="NEXUS — Enterprise AI OS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap');

/* ══════════════════════════════════════════════
   ROOT VARIABLES — Modern AI Dark Theme
══════════════════════════════════════════════ */
:root {
    --bg-base:      #050814;
    --bg-card:      rgba(15, 23, 42, 0.6);
    --bg-card-hover:rgba(30, 41, 59, 0.8);
    --text-main:    #F8FAFC;
    --text-muted:   #94A3B8;
    --text-dim:     #64748B;
    
    --neon-cyan:    #00E5FF;
    --neon-blue:    #2979FF;
    --neon-purple:  #B388FF;
    --neon-green:   #00E676;
    --neon-orange:  #FF9100;
    
    --bdr-color:    rgba(255, 255, 255, 0.08);
    --bdr-hover:    rgba(0, 229, 255, 0.3);
    
    --shadow-glow:  0 0 20px rgba(0, 229, 255, 0.15);
    --glass-blur:   blur(12px);
}

/* ══════════════════════════════════════════════
   BASE RESET & BACKGROUND
══════════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }

html, body, .stApp {
    font-family: 'Inter', sans-serif !important;
    background-color: var(--bg-base) !important;
    color: var(--text-main) !important;
}

/* Subtle animated tech grid background */
.stApp {
    background-image: 
        linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px) !important;
    background-size: 40px 40px !important;
    background-position: center center !important;
    animation: grid-move 20s linear infinite;
}

@keyframes grid-move {
    0% { background-position: 0 0; }
    100% { background-position: 40px 40px; }
}

/* hide chrome */
#MainMenu, footer, header { visibility: hidden !important; }
.stDeployButton { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
[data-testid="chatAvatarIcon-user"], [data-testid="chatAvatarIcon-assistant"],
[data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] { display: none !important; }
[data-testid="stChatMessage"] {
    background: transparent !important; border: none !important; padding: 0 !important; gap: 0 !important;
}

.block-container {
    padding-top: 1rem !important;
    max-width: 1200px !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}

/* ══════════════════════════════════════════════
   MASTHEAD
══════════════════════════════════════════════ */
.masthead {
    border-bottom: 1px solid var(--bdr-color);
    padding: 20px 0;
    margin-bottom: 20px;
    animation: fade-slide-down 0.6s ease-out both;
}

.masthead-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
}

.masthead-brand {
    display: flex;
    align-items: center;
    gap: 16px;
}

.brand-mark {
    width: 48px; height: 48px;
    background: linear-gradient(135deg, var(--neon-cyan), var(--neon-blue));
    border-radius: 12px;
    display: grid; place-items: center;
    font-family: 'Fira Code', monospace !important;
    font-weight: 700; font-size: 1.1rem;
    color: #000 !important;
    box-shadow: var(--shadow-glow);
    animation: pulse-glow 3s infinite alternate;
}

.brand-text-name {
    font-weight: 700; font-size: 1.8rem;
    letter-spacing: -0.03em;
    background: linear-gradient(to right, #FFF, var(--text-muted));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1.1;
}

.brand-text-sub {
    font-family: 'Fira Code', monospace !important;
    font-size: 0.65rem; color: var(--neon-cyan) !important;
    letter-spacing: 0.2em; text-transform: uppercase; margin-top: 4px;
}

.masthead-right {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 8px;
}

.live-indicator {
    display: flex; align-items: center; gap: 8px;
    font-family: 'Fira Code', monospace !important;
    font-size: 0.65rem; color: var(--neon-green) !important;
    letter-spacing: 0.1em; text-transform: uppercase;
    background: rgba(0, 230, 118, 0.1);
    padding: 4px 12px; border-radius: 20px;
    border: 1px solid rgba(0, 230, 118, 0.2);
}

.live-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--neon-green);
    box-shadow: 0 0 8px var(--neon-green);
    animation: blink 1.5s infinite;
}

/* ══════════════════════════════════════════════
   STATS STRIP
══════════════════════════════════════════════ */
.stats-strip {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 20px;
    animation: fade-slide-up 0.7s ease-out both;
    animation-delay: 0.1s;
}

.stat-cell {
    background: var(--bg-card);
    backdrop-filter: var(--glass-blur);
    border: 1px solid var(--bdr-color);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
}

.stat-cell:hover {
    border-color: var(--bdr-hover);
    transform: translateY(-2px);
    box-shadow: var(--shadow-glow);
}

.stat-cell::before {
    content: '';
    position: absolute; top: 0; left: 0; width: 100%; height: 2px;
    background: var(--c); opacity: 0.8;
}

.stat-cell:nth-child(1) { --c: var(--neon-cyan); }
.stat-cell:nth-child(2) { --c: var(--neon-purple); }
.stat-cell:nth-child(3) { --c: var(--neon-green); }
.stat-cell:nth-child(4) { --c: var(--neon-orange); }

.stat-num {
    font-weight: 700; font-size: 2.5rem; line-height: 1;
    color: var(--text-main);
    text-shadow: 0 0 10px rgba(255,255,255,0.1);
}

.stat-lbl {
    font-family: 'Fira Code', monospace !important;
    font-size: 0.6rem; color: var(--text-muted) !important;
    text-transform: uppercase; letter-spacing: 0.15em; margin-top: 8px;
}

/* ══════════════════════════════════════════════
   TABS
══════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--bdr-color) !important;
    gap: 24px !important;
    margin-bottom: 24px !important;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    color: var(--text-muted) !important;
    font-family: 'Fira Code', monospace !important;
    font-size: 0.75rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    padding: 12px 0 !important;
    transition: all 0.3s !important;
}

.stTabs [data-baseweb="tab"]:hover {
    color: var(--text-main) !important;
}

.stTabs [aria-selected="true"] {
    color: var(--neon-cyan) !important;
    border-bottom: 2px solid var(--neon-cyan) !important;
    text-shadow: 0 0 8px rgba(0, 229, 255, 0.4) !important;
}

.stTabs [data-baseweb="tab-highlight"] { display: none !important; }

/* ══════════════════════════════════════════════
   CHAT — USER MESSAGE
══════════════════════════════════════════════ */
.msg-u-wrap {
    display: flex; justify-content: flex-end;
    margin: 20px 0; animation: slide-left 0.3s ease-out both;
}

.msg-u-inner { max-width: 75%; }

.msg-u-lbl {
    text-align: right;
    font-family: 'Fira Code', monospace !important;
    font-size: 0.6rem; letter-spacing: 0.15em; color: var(--text-dim) !important;
    text-transform: uppercase; margin-bottom: 6px;
}

.msg-u-bubble {
    background: rgba(41, 121, 255, 0.1);
    border: 1px solid rgba(41, 121, 255, 0.3);
    color: var(--text-main) !important;
    border-radius: 16px 16px 4px 16px;
    padding: 16px 24px;
    font-size: 0.95rem; line-height: 1.6;
    backdrop-filter: var(--glass-blur);
}

/* ══════════════════════════════════════════════
   CHAT — BOT MESSAGE
══════════════════════════════════════════════ */
.msg-b-lbl {
    font-family: 'Fira Code', monospace !important;
    font-size: 0.6rem; letter-spacing: 0.15em;
    color: var(--neon-cyan) !important; text-transform: uppercase;
    margin: 20px 0 6px; display: flex; align-items: center; gap: 8px;
    animation: slide-right 0.3s ease-out both;
}

.msg-b-lbl-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--neon-cyan); box-shadow: 0 0 8px var(--neon-cyan);
}

.msg-b-wrap {
    max-width: 85%;
    animation: slide-right 0.3s ease-out both;
    margin-bottom: 8px;
}

.msg-b-bubble {
    background: var(--bg-card);
    border: 1px solid var(--bdr-color);
    border-left: 3px solid var(--neon-cyan);
    border-radius: 4px 16px 16px 16px;
    padding: 18px 24px;
    font-size: 0.95rem; line-height: 1.7;
    color: var(--text-main) !important;
    backdrop-filter: var(--glass-blur);
    box-shadow: 0 4px 20px rgba(0,0,0,0.2);
}

/* ══════════════════════════════════════════════
   META BADGE & STREAMING CURSOR
══════════════════════════════════════════════ */
.msg-meta {
    display: inline-flex; align-items: center; gap: 8px;
    font-family: 'Fira Code', monospace !important;
    font-size: 0.6rem; color: var(--text-muted) !important;
    background: rgba(0,0,0,0.3); border: 1px solid var(--bdr-color);
    border-radius: 6px; padding: 4px 12px; margin: 8px 0 20px;
}

.cur {
    display: inline-block; width: 6px; height: 1em;
    background: var(--neon-cyan); margin-left: 4px; vertical-align: text-bottom;
    animation: blink 0.8s infinite;
    box-shadow: 0 0 8px var(--neon-cyan);
}

/* ══════════════════════════════════════════════
   SOURCE CARDS
══════════════════════════════════════════════ */
.src-card {
    background: rgba(0,0,0,0.2);
    border: 1px solid var(--bdr-color);
    border-left: 2px solid var(--neon-purple);
    border-radius: 6px;
    padding: 14px 18px; margin: 10px 0;
}

.src-lbl {
    font-family: 'Fira Code', monospace !important;
    font-size: 0.6rem; color: var(--neon-purple) !important;
    text-transform: uppercase; letter-spacing: 0.15em; margin-bottom: 6px;
}

.src-txt {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.8rem; color: var(--text-muted) !important; line-height: 1.6;
}

/* ══════════════════════════════════════════════
   EMPTY STATE
══════════════════════════════════════════════ */
.empty-state {
    text-align: center; padding: 6rem 2rem;
    animation: fade-slide-up 0.5s ease out both;
}

.empty-mark {
    font-size: 3.5rem; color: rgba(255,255,255,0.05);
    display: block; margin-bottom: 24px;
    animation: float 4s ease-in-out infinite;
}

.empty-head {
    font-weight: 600; font-size: 1.5rem;
    color: var(--text-main); margin-bottom: 12px;
}

.empty-sub {
    font-family: 'Fira Code', monospace !important;
    font-size: 0.75rem; color: var(--text-dim) !important; line-height: 1.8;
}

/* ══════════════════════════════════════════════
   INPUTS & EXPANDERS
══════════════════════════════════════════════ */
[data-testid="stChatInput"] {
    background: var(--bg-card) !important;
    backdrop-filter: var(--glass-blur) !important;
    border: 1px solid var(--bdr-color) !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
    transition: all 0.3s ease !important;
    margin-top: 24px !important;
}

[data-testid="stChatInput"]:focus-within {
    border-color: var(--neon-cyan) !important;
    box-shadow: var(--shadow-glow) !important;
}

[data-testid="stChatInput"] textarea {
    color: var(--text-main) !important;
    font-size: 1rem !important;
    caret-color: var(--neon-cyan) !important;
}

.streamlit-expanderHeader {
    background: rgba(0,0,0,0.2) !important;
    border: 1px solid var(--bdr-color) !important;
    border-radius: 8px !important;
    font-family: 'Fira Code', monospace !important;
    font-size: 0.7rem !important; color: var(--text-muted) !important;
}

.streamlit-expanderContent {
    background: transparent !important; border: none !important;
}

/* ══════════════════════════════════════════════
   BUTTONS & TOGGLES
══════════════════════════════════════════════ */
.stButton > button {
    background: rgba(41, 121, 255, 0.1) !important;
    border: 1px solid var(--neon-blue) !important;
    color: var(--text-main) !important;
    font-family: 'Fira Code', monospace !important;
    font-size: 0.7rem !important; letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    border-radius: 8px !important;
    padding: 12px 24px !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    background: var(--neon-blue) !important;
    box-shadow: 0 0 15px rgba(41, 121, 255, 0.4) !important;
}

.stToggle label { 
    font-family: 'Fira Code', monospace !important; 
    font-size: 0.7rem !important; color: var(--text-muted) !important; 
}

/* ══════════════════════════════════════════════
   FILE UPLOADER & CARDS
══════════════════════════════════════════════ */
[data-testid="stFileUploaderDropzone"] {
    background: rgba(0,0,0,0.2) !important;
    border: 1px dashed var(--bdr-color) !important;
    border-radius: 12px !important;
    transition: all 0.3s !important;
}
[data-testid="stFileUploaderDropzone"]:hover { 
    border-color: var(--neon-cyan) !important; 
    background: rgba(0, 229, 255, 0.05) !important;
}

.sec-card {
    background: var(--bg-card);
    backdrop-filter: var(--glass-blur);
    border: 1px solid var(--bdr-color);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 20px;
    transition: all 0.3s ease;
}

.sec-card:hover { border-color: var(--bdr-hover); box-shadow: var(--shadow-glow); transform: translateY(-2px); }

.sec-card-title {
    font-weight: 600; font-size: 1.1rem; color: var(--text-main);
    margin-bottom: 20px; display: flex; align-items: center; gap: 12px;
    padding-bottom: 12px; border-bottom: 1px solid var(--bdr-color);
}

.accent-rule {
    display: inline-block; width: 24px; height: 4px;
    background: var(--neon-cyan); border-radius: 4px;
    box-shadow: 0 0 8px var(--neon-cyan);
}

.sec-card-body {
    font-family: 'Fira Code', monospace !important;
    font-size: 0.75rem; color: var(--text-muted) !important; line-height: 2.2;
}

.feat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.feat-item {
    font-family: 'Fira Code', monospace !important; font-size: 0.65rem; color: var(--text-muted);
    background: rgba(0,0,0,0.3); border: 1px solid var(--bdr-color);
    border-radius: 6px; padding: 12px;
    display: flex; align-items: center; gap: 10px;
}
.feat-item.done { border-left: 3px solid var(--neon-green); color: var(--text-main); }
.feat-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--text-dim); }
.feat-item.done .feat-dot { background: var(--neon-green); box-shadow: 0 0 8px var(--neon-green); }

/* ══════════════════════════════════════════════
   KEYFRAMES
══════════════════════════════════════════════ */
@keyframes fade-slide-down { from{opacity:0;transform:translateY(-20px)} to{opacity:1;transform:translateY(0)} }
@keyframes fade-slide-up   { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }
@keyframes slide-right     { from{opacity:0;transform:translateX(-20px)} to{opacity:1;transform:translateX(0)} }
@keyframes slide-left      { from{opacity:0;transform:translateX(20px)} to{opacity:1;transform:translateX(0)} }
@keyframes pulse-glow      { 0%{box-shadow:0 0 10px rgba(0,229,255,0.2)} 100%{box-shadow:0 0 25px rgba(0,229,255,0.6)} }
@keyframes blink           { 0%,100%{opacity:1} 50%{opacity:0} }
@keyframes float           { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-15px)} }
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
if "use_stream"    not in st.session_state: st.session_state.use_stream    = True
if "eval_results"  not in st.session_state: st.session_state.eval_results  = None

def extract_src_text(src) -> str:
    if isinstance(src, dict):
        return str(src.get("text", src.get("content", str(src))))
    return str(src)

def extract_src_meta(src) -> str:
    if isinstance(src, dict):
        s = src.get("source", "")
        p = src.get("page", "")
        return f"{s} · p.{p}" if s and p else s
    return ""

def score_color(v: float) -> str:
    if v >= 0.8: return "var(--neon-green)"
    if v >= 0.6: return "var(--neon-orange)"
    return "#FF1744"

def score_label(v: float) -> str:
    if v >= 0.8: return "OPTIMAL"
    if v >= 0.6: return "ACCEPTABLE"
    return "DEGRADED"

def render_score(name: str, score: float):
    col = score_color(score)
    pct = int(score * 100)
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:16px;margin-bottom:16px;">
        <div style="font-family:'Fira Code',monospace;font-size:0.65rem;color:var(--text-muted);width:150px;text-transform:uppercase;letter-spacing:0.08em;">{name}</div>
        <div style="flex:1;height:8px;background:rgba(255,255,255,0.05);border-radius:4px;overflow:hidden;box-shadow:inset 0 1px 3px rgba(0,0,0,0.5);">
            <div style="height:100%;width:{pct}%;background:{col};box-shadow:0 0 10px {col};border-radius:4px;transition:width 1s ease-out;"></div>
        </div>
        <div style="font-weight:700;font-size:1rem;width:50px;text-align:right;color:{col};text-shadow:0 0 8px {col};">{score:.2f}</div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════
# MASTHEAD
# ══════════════════════════════════════════════

st.markdown("""
<div class="masthead">
    <div class="masthead-top">
        <div class="masthead-brand">
            <div class="brand-mark">NX</div>
            <div>
                <div class="brand-text-name">NEXUS Core</div>
                <div class="brand-text-sub">Enterprise AI OS &nbsp;·&nbsp; v4.5</div>
            </div>
        </div>
        <div class="masthead-right">
            <div class="live-indicator">
                <span class="live-dot"></span>System Active
            </div>
            <div style="font-family:'Fira Code',monospace;font-size:0.6rem;color:var(--text-dim);letter-spacing:0.1em;margin-top:4px;">
                Hybrid RAG · Edge Native
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# STATS STRIP
# ══════════════════════════════════════════════

avg = st.session_state.time_total / st.session_state.questions if st.session_state.questions > 0 else 0.0

st.markdown(f"""
<div class="stats-strip">
    <div class="stat-cell">
        <div class="stat-num" style="color:var(--neon-cyan);">{st.session_state.questions}</div>
        <div class="stat-lbl">Queries Executed</div>
    </div>
    <div class="stat-cell">
        <div class="stat-num" style="color:var(--neon-purple);">{len(st.session_state.messages)//2}</div>
        <div class="stat-lbl">Neural Exchanges</div>
    </div>
    <div class="stat-cell">
        <div class="stat-num" style="color:var(--neon-green);">{avg:.1f}s</div>
        <div class="stat-lbl">Avg Response Latency</div>
    </div>
    <div class="stat-cell">
        <div class="stat-num" style="color:var(--neon-orange);">{st.session_state.src_total}</div>
        <div class="stat-lbl">Vector Chunks Sourced</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════

tab1, tab2, tab3, tab4 = st.tabs(["Neural Chat", "Data Ingestion", "System Diagnostics", "Architecture"])


# ════════════════════════════════════════════════
# TAB 1 — CHAT
# ════════════════════════════════════════════════

with tab1:

    col_tog, _ = st.columns([2, 8])
    with col_tog:
        st.session_state.use_stream = st.toggle(
            "Enable SSE Streaming", value=st.session_state.use_stream)

    if not st.session_state.messages:
        st.markdown("""
        <div class="empty-state">
            <span class="empty-mark">⬡</span>
            <div class="empty-head">Neural Matrix Initialized</div>
            <div class="empty-sub">
                Input queries to access the enterprise knowledge base.<br>
                Model context window optimized for dense retrieval.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="msg-u-wrap">
                    <div class="msg-u-inner">
                        <div class="msg-u-lbl">Operator</div>
                        <div class="msg-u-bubble">{msg['content']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="msg-b-lbl">
                    <span class="msg-b-lbl-dot"></span>NEXUS Core
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div class="msg-b-wrap">
                    <div class="msg-b-bubble">{msg['content']}</div>
                </div>
                """, unsafe_allow_html=True)
                rt = msg.get("response_time", 0)
                sc = msg.get("source_count", 0)
                if rt:
                    st.markdown(f"""
                    <div class="msg-meta">
                        <span style="color:var(--neon-cyan)">⚡</span>
                        {rt:.2f}s latency &nbsp;·&nbsp; {sc} vector{'s' if sc != 1 else ''} retrieved &nbsp;·&nbsp; Hybrid Fusion
                    </div>
                    """, unsafe_allow_html=True)
                srcs = msg.get("sources", [])
                if srcs:
                    with st.expander(f"Inspect Data Sources [{len(srcs)} found]"):
                        for j, src in enumerate(srcs, 1):
                            text = extract_src_text(src)
                            meta = extract_src_meta(src)
                            st.markdown(f"""
                            <div class="src-card">
                                <div class="src-lbl">Node Context {j:02d}</div>
                                {f'<div style="font-family:Fira Code,monospace;font-size:0.55rem;color:var(--text-dim);margin-bottom:8px;">{meta}</div>' if meta else ''}
                                <div class="src-txt">{text}</div>
                            </div>
                            """, unsafe_allow_html=True)

    question = st.chat_input("Query the organizational neural net...")

    if question:
        st.session_state.questions += 1
        st.session_state.messages.append({"role":"user","content":question,"sources":[]})

        st.markdown(f"""
        <div class="msg-u-wrap">
            <div class="msg-u-inner">
                <div class="msg-u-lbl">Operator</div>
                <div class="msg-u-bubble">{question}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="msg-b-lbl"><span class="msg-b-lbl-dot"></span>NEXUS Core</div>', unsafe_allow_html=True)

        t0 = time.time(); full_answer = ""; sources = []; streamed_ok = False

        if st.session_state.use_stream:
            placeholder = st.empty()
            try:
                with requests.post(STREAM_URL,
                    json={"question":question,"session_id":st.session_state.session_id},
                    stream=True, timeout=60) as res:
                    if res.status_code == 200:
                        streamed_ok = True
                        for raw in res.iter_lines():
                            if raw:
                                line = raw.decode("utf-8")
                                if line.startswith("data: "):
                                    try: data = json.loads(line[6:])
                                    except: continue
                                    if not data.get("done"):
                                        full_answer += data.get("token","")
                                        placeholder.markdown(f'<div class="msg-b-wrap"><div class="msg-b-bubble">{full_answer}<span class="cur"></span></div></div>', unsafe_allow_html=True)
                                    else:
                                        sources = data.get("sources",[])
                                        placeholder.markdown(f'<div class="msg-b-wrap"><div class="msg-b-bubble">{full_answer}</div></div>', unsafe_allow_html=True)
            except: streamed_ok = False

        if not st.session_state.use_stream or not streamed_ok:
            with st.spinner("Processing semantics..."):
                try:
                    res = requests.post(ASK_URL, json={"question":question,"session_id":st.session_state.session_id}, timeout=30)
                    if res.status_code == 200:
                        data = res.json(); full_answer = data.get("answer",""); sources = data.get("sources",[])
                    else:
                        full_answer = f"Backend error {res.status_code}."
                except requests.exceptions.Timeout:
                    full_answer = "Timeout exception during inference. Retry."
                except Exception as e:
                    full_answer = f"Fatal system error: {str(e)}"
            st.markdown(f'<div class="msg-b-wrap"><div class="msg-b-bubble">{full_answer}</div></div>', unsafe_allow_html=True)

        elapsed = time.time() - t0
        st.session_state.time_total += elapsed
        st.session_state.src_total  += len(sources)

        st.markdown(f"""
        <div class="msg-meta">
            <span style="color:var(--neon-cyan)">⚡</span>
            {elapsed:.2f}s latency &nbsp;·&nbsp; {len(sources)} vector{'s' if len(sources)!=1 else ''} retrieved &nbsp;·&nbsp; Hybrid Fusion
        </div>
        """, unsafe_allow_html=True)

        if sources:
            with st.expander(f"Inspect Data Sources [{len(sources)} found]"):
                for j, src in enumerate(sources, 1):
                    text = extract_src_text(src); meta = extract_src_meta(src)
                    st.markdown(f"""
                    <div class="src-card">
                        <div class="src-lbl">Node Context {j:02d}</div>
                        {f'<div style="font-family:Fira Code,monospace;font-size:0.55rem;color:var(--text-dim);margin-bottom:8px;">{meta}</div>' if meta else ''}
                        <div class="src-txt">{text}</div>
                    </div>
                    """, unsafe_allow_html=True)

        st.session_state.messages.append({
            "role":"assistant","content":full_answer,"sources":sources,
            "response_time":elapsed,"source_count":len(sources),"streamed":streamed_ok
        })
        st.rerun()

    col_c, _ = st.columns([2,8])
    with col_c:
        if st.button("Purge Memory"):
            st.session_state.messages=[]; st.session_state.questions=0
            st.session_state.time_total=0.0; st.session_state.src_total=0
            st.session_state.session_id=f"nx_{str(uuid.uuid4())[:8]}"
            st.rerun()


# ════════════════════════════════════════════════
# TAB 2 — INGEST
# ════════════════════════════════════════════════

with tab2:
    st.markdown("""
    <div style="margin-bottom:24px;">
        <div style="font-weight:600;font-size:1.4rem;color:var(--text-main);margin-bottom:8px;text-shadow:0 0 10px rgba(255,255,255,0.1);">
            Knowledge Pipeline Ingestion
        </div>
        <div style="font-family:'Fira Code',monospace;font-size:0.7rem;color:var(--text-muted);line-height:1.6;">
            [SUPPORTED PROTOCOLS: PDF, TXT] &nbsp;·&nbsp; [LIMIT: 5MB MAX]<br>
            Payloads undergo recursive character splitting (500 tokens) before Pinecone + BM25 indexing.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2], gap="large")

    with col1:
        uploaded_file = st.file_uploader("Upload Payload", type=["pdf","txt"], label_visibility="collapsed")

        if uploaded_file:
            size_kb = len(uploaded_file.getvalue()) / 1024
            size_mb = size_kb / 1024
            if size_mb > 5:
                st.warning(f"File payload is {size_mb:.1f}MB. Free-tier timeouts may occur.")
            
            st.markdown(f"""
            <div style="font-family:'Fira Code',monospace;font-size:0.75rem;color:var(--neon-cyan);
                        background:rgba(0, 229, 255, 0.05);border:1px solid rgba(0, 229, 255, 0.2);
                        border-left:3px solid var(--neon-cyan);border-radius:4px;
                        padding:14px 18px;margin:16px 0;box-shadow:0 0 10px rgba(0, 229, 255, 0.1);">
                &#9679;&nbsp; PAYLOAD DETECTED: {uploaded_file.name} [{size_kb:.0f} KB]
            </div>
            """, unsafe_allow_html=True)

            if st.button("Execute Indexing"):
                with st.spinner("Encrypting and transferring payload..."):
                    try:
                        files = {"file":(uploaded_file.name,uploaded_file.getvalue(),uploaded_file.type)}
                        resp  = requests.post(UPLOAD_URL, files=files, timeout=180)
                        if resp.status_code == 200:
                            data = resp.json()
                            st.success(f"Indexed {data.get('total_chunks',0)} chunks into vector space.")
                            if uploaded_file.name not in st.session_state.uploaded_docs:
                                st.session_state.uploaded_docs.append(uploaded_file.name)
                        elif resp.status_code == 413:
                            st.error("Payload exceeded structural limits (10MB).")
                        else:
                            st.error(f"Transfer failed. Error code: {resp.status_code}")
                    except Exception as e:
                        st.error(f"System Exception: {str(e)}")

        st.markdown("""
        <div style="font-family:'Fira Code',monospace;font-size:0.65rem;color:var(--text-muted);
                    background:rgba(0,0,0,0.3); border:1px solid var(--bdr-color);
                    border-left:3px solid var(--neon-purple); border-radius:4px;
                    padding:16px; margin-top:24px; line-height:1.9;">
            <span style="color:var(--neon-purple);">> INGESTION_PROTOCOL_ACTIVE</span><br>
            Vector embeddings generated concurrently with BM25 keyword indices. Query retrieval will execute Reciprocal Rank Fusion on both data sets.
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="sec-card" style="padding:16px;">
            <div style="font-family:'Fira Code',monospace;font-size:0.6rem;color:var(--text-dim);
                        text-transform:uppercase;letter-spacing:0.15em;margin-bottom:16px;
                        padding-bottom:12px;border-bottom:1px solid var(--bdr-color);">
                Current Session Ledger
            </div>
        """, unsafe_allow_html=True)

        if st.session_state.uploaded_docs:
            for d in st.session_state.uploaded_docs:
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;font-family:'Fira Code',monospace;
                            font-size:0.7rem;color:var(--neon-green);padding:8px 0;
                            border-bottom:1px solid rgba(255,255,255,0.05);">
                    <span style="width:6px;height:6px;border-radius:50%;background:var(--neon-green);
                                 box-shadow:0 0 8px var(--neon-green);flex-shrink:0;"></span>
                    {d}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""<div style="font-family:'Fira Code',monospace;font-size:0.7rem;color:var(--text-dim);padding:8px 0;text-align:center;">[ NO DATA FRAGMENTS DETECTED ]</div>""", unsafe_allow_html=True)

        st.markdown(f"""
            <div style="font-family:'Fira Code',monospace;font-size:0.65rem;color:var(--text-dim);
                        margin-top:20px;padding-top:16px;border-top:1px dashed rgba(255,255,255,0.1);line-height:2;">
                SYS_SESSION_ID<br>
                <span style="color:var(--text-main);">{st.session_state.session_id}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════
# TAB 3 — EVALUATION
# ════════════════════════════════════════════════

with tab3:
    st.markdown("""
    <div style="margin-bottom:24px;">
        <div style="font-weight:600;font-size:1.4rem;color:var(--text-main);margin-bottom:8px;">
            RAG Integrity Diagnostics
        </div>
        <div style="font-family:'Fira Code',monospace;font-size:0.7rem;color:var(--text-muted);line-height:1.6;">
            RAGAS framework executing 4-dimensional retrieval evaluation.<br>
            TruLens verifying groundedness and contextual integrity. Engine: Groq LLM Judge.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_btn, col_info = st.columns([2, 5])
    with col_btn:
        run_eval = st.button("Initiate Diagnostics", use_container_width=True)
    with col_info:
        st.markdown("""
        <div style="font-family:'Fira Code',monospace;font-size:0.65rem;color:var(--text-dim);padding-top:10px;line-height:1.8;">
            > Est. completion time: ~60.00s <br>
            > Caching results for persistent verification...
        </div>
        """, unsafe_allow_html=True)

    if run_eval:
        with st.spinner("Running deep evaluation matrices..."):
            try:
                resp = requests.post(EVALUATE_URL, timeout=180)
                if resp.status_code == 200:
                    st.session_state.eval_results = resp.json()
                    st.success("Diagnostics Complete. Matrix updated.")
                else:
                    st.error(f"Diagnostics failed. Status Code: {resp.status_code}")
            except requests.exceptions.Timeout:
                st.warning("Timeout threshold reached on Groq judge node. Please retry.")
            except Exception as e:
                st.error(f"Critical diagnostic failure: {str(e)}")

    if st.session_state.eval_results:
        res     = st.session_state.eval_results
        ragas   = res.get("ragas", {})
        trulens = res.get("trulens", {})
        rs      = ragas.get("scores", {})
        ts      = trulens.get("scores", {})

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2, gap="large")

        with col1:
            st.markdown("""
            <div class="sec-card">
                <div style="font-family:'Fira Code',monospace;font-size:0.7rem;color:var(--neon-blue);
                            text-transform:uppercase;letter-spacing:0.15em;margin-bottom:20px;
                            display:flex;align-items:center;gap:10px;">
                    <span style="width:8px;height:8px;background:var(--neon-blue);box-shadow:0 0 10px var(--neon-blue);"></span>
                    RAGAS telemetry
                </div>
            """, unsafe_allow_html=True)
            for k, label in [("faithfulness","Faithfulness"),("answer_relevancy","Answer Relevancy"),
                              ("context_precision","Context Precision"),("context_recall","Context Recall")]:
                render_score(label, rs.get(k, 0))

            ov_r = rs.get("overall", 0)
            col_ovr = score_color(ov_r)
            st.markdown(f"""
                <div style="background:rgba(0,0,0,0.4);border-radius:8px;padding:20px;text-align:center;margin-top:20px;border:1px solid rgba(255,255,255,0.05);">
                    <div style="font-weight:700;font-size:3rem;line-height:1;color:{col_ovr};text-shadow:0 0 15px {col_ovr};">{ov_r:.2f}</div>
                    <div style="font-family:'Fira Code',monospace;font-size:0.6rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.15em;margin-top:10px;">RAGAS Overall · {score_label(ov_r)}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="sec-card">
                <div style="font-family:'Fira Code',monospace;font-size:0.7rem;color:var(--neon-purple);
                            text-transform:uppercase;letter-spacing:0.15em;margin-bottom:20px;
                            display:flex;align-items:center;gap:10px;">
                    <span style="width:8px;height:8px;background:var(--neon-purple);box-shadow:0 0 10px var(--neon-purple);"></span>
                    TruLens Integrity
                </div>
            """, unsafe_allow_html=True)
            for k, label in [("groundedness","Groundedness"),("answer_relevance","Answer Relevance"),
                              ("context_relevance","Context Relevance")]:
                render_score(label, ts.get(k, 0))

            ov_t = ts.get("overall", 0)
            col_ovt = score_color(ov_t)
            st.markdown(f"""
                <div style="background:rgba(0,0,0,0.4);border-radius:8px;padding:20px;text-align:center;margin-top:20px;border:1px solid rgba(255,255,255,0.05);">
                    <div style="font-weight:700;font-size:3rem;line-height:1;color:{col_ovt};text-shadow:0 0 15px {col_ovt};">{ov_t:.2f}</div>
                    <div style="font-family:'Fira Code',monospace;font-size:0.6rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.15em;margin-top:10px;">TruLens Overall · {score_label(ov_t)}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    else:
        st.markdown("""
        <div style="text-align:center;padding:5rem 2rem;border:1px dashed var(--bdr-color);border-radius:12px;margin-top:20px;background:rgba(0,0,0,0.2);">
            <div style="font-size:3rem;color:var(--text-dim);margin-bottom:20px;">⚡</div>
            <div style="font-weight:600;font-size:1.2rem;color:var(--text-muted);">Awaiting Telemetry Execution</div>
            <div style="font-family:'Fira Code',monospace;font-size:0.7rem;color:var(--text-dim);margin-top:10px;">Run Diagnostics to analyze vector semantic accuracy</div>
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════
# TAB 4 — ARCHITECTURE
# ════════════════════════════════════════════════

with tab4:
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("""
        <div class="sec-card">
            <div class="sec-card-title">
                <span class="accent-rule"></span>Neural RAG Pipeline
            </div>
            <div class="sec-card-body" style="color:var(--neon-cyan) !important;">
                [QUERY_RECEIVED]<br>
                <span style="color:var(--text-dim);">├─</span> Multi-query rewriting (Groq LLM)<br>
                <span style="color:var(--text-dim);">├─</span> [HYBRID_RETRIEVAL_ACTIVE]<br>
                <span style="color:var(--text-dim);">│  ├─</span> Pinecone Vector Graph (Cosine Dist)<br>
                <span style="color:var(--text-dim);">│  └─</span> BM25 Lexical Keyword Memory<br>
                <span style="color:var(--text-dim);">├─</span> [RRF_FUSION_MERGE]<br>
                <span style="color:var(--text-dim);">├─</span> Contextual Guardrails (Threshold > 0.30)<br>
                <span style="color:var(--text-dim);">└─</span> [GENERATION]<br>
                &nbsp;&nbsp;&nbsp; Gemini 2.5 Flash + SSE Stream Out
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="sec-card">
            <div class="sec-card-title">
                <span class="accent-rule" style="background:var(--neon-purple);box-shadow:0 0 8px var(--neon-purple);"></span>Stack Configuration
            </div>
            <div class="sec-card-body" style="display: grid; grid-template-columns: 120px 1fr; gap: 4px;">
                <span style="color:var(--text-muted);">FRONTEND</span> <span style="color:var(--text-main);">Streamlit / Migrating to Vercel UI</span>
                <span style="color:var(--text-muted);">API CORE</span> <span style="color:var(--text-main);">FastAPI / Uvicorn Edge</span>
                <span style="color:var(--text-muted);">AUTH / DB</span> <span style="color:var(--text-main);">Firebase Integration Module</span>
                <span style="color:var(--text-muted);">VECTOR DB</span> <span style="color:var(--text-main);">Pinecone Serverless (3072-dim)</span>
                <span style="color:var(--text-muted);">EMBEDDER</span> <span style="color:var(--text-main);">gemini-embedding-001</span>
                <span style="color:var(--text-muted);">PRIMARY LLM</span> <span style="color:var(--text-main);">Gemini 2.5 Flash API</span>
                <span style="color:var(--text-muted);">FALLBACK</span> <span style="color:var(--text-main);">Groq llama-3.1-8b-instant</span>
                <span style="color:var(--text-muted);">SESSION</span> <span style="color:var(--text-main);">{st.session_state.session_id}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="sec-card">
        <div class="sec-card-title">
            <span class="accent-rule" style="background:var(--neon-green);box-shadow:0 0 8px var(--neon-green);"></span>Development Matrix Roadmap
        </div>
        <div class="feat-grid">
            <div class="feat-item done"><span class="feat-dot"></span>SSE Streaming Protocols</div>
            <div class="feat-item done"><span class="feat-dot"></span>BM25 + Vector Fusion</div>
            <div class="feat-item done"><span class="feat-dot"></span>RAGAS Deep Evaluation</div>
            <div class="feat-item done"><span class="feat-dot"></span>TruLens Quality Guards</div>
            <div class="feat-item done"><span class="feat-dot"></span>Reciprocal Rank Scaling</div>
            <div class="feat-item done"><span class="feat-dot"></span>LLM Multi-query Translation</div>
            <div class="feat-item"><span class="feat-dot"></span>Firebase Authentication Lock</div>
            <div class="feat-item"><span class="feat-dot"></span>Vercel Edge Deployment</div>
            <div class="feat-item"><span class="feat-dot"></span>Cross-encoder Re-ranking</div>
            <div class="feat-item"><span class="feat-dot"></span>LangGraph Agent Support</div>
        </div>
    </div>
    """, unsafe_allow_html=True)