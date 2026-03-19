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
    page_title="NEXUS — Enterprise Knowledge",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ------------------------------------------------
# ULTRA PREMIUM CSS OVERHAUL - TERMINAL LUXE
# ------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Fira+Code:wght@400;500;600&display=swap');

/* ══════════════════════════════════════════════
   ROOT VARIABLES — Dark Tech OS Theme
══════════════════════════════════════════════ */
:root {
    --bg-base:      #0b1121;
    --bg-panel:     rgba(15, 23, 42, 0.5);
    --bg-card:      rgba(30, 41, 59, 0.4);
    
    --text-main:    #F8FAFC;
    --text-muted:   #94A3B8;
    --text-dim:     #475569;
    
    --neon-cyan:    #00E5FF;
    --neon-purple:  #8B5CF6;
    --neon-orange:  #F97316;
    --neon-green:   #10B981;
    --neon-pink:    #EC4899;
    
    --bdr-color:    rgba(255, 255, 255, 0.08);
    --bdr-strong:   rgba(255, 255, 255, 0.15);
    
    --glass-blur:   blur(16px);
}

*, *::before, *::after { box-sizing: border-box; }

html, body, .stApp {
    font-family: 'Inter', sans-serif !important;
    background-color: var(--bg-base) !important;
    color: var(--text-main) !important;
}

/* Animated Grid Background */
.stApp {
    background-image: 
        linear-gradient(rgba(255, 255, 255, 0.02) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.02) 1px, transparent 1px) !important;
    background-size: 40px 40px !important;
    background-position: center center !important;
    animation: grid-scroll 30s linear infinite;
}

@keyframes grid-scroll {
    0% { background-position: 0 0; }
    100% { background-position: 40px 40px; }
}

/* Hide Default Streamlit UI elements */
#MainMenu, footer, header { visibility: hidden !important; }
.stDeployButton { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }

/* Remove standard Streamlit chat UI padding/borders */
[data-testid="stChatMessage"] { background: transparent !important; border: none !important; padding: 0 !important; gap: 0 !important; }
[data-testid="chatAvatarIcon-user"], [data-testid="chatAvatarIcon-assistant"],
[data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] { display: none !important; }

.block-container {
    padding-top: 1.5rem !important;
    max-width: 1200px !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}

/* ══════════════════════════════════════════════
   GLOBAL UI ELEMENTS (Masthead, Tabs, Cards)
══════════════════════════════════════════════ */
.masthead { border-bottom: 1px solid var(--bdr-color); padding-bottom: 20px; margin-bottom: 24px; animation: fadeInDown 0.6s ease-out; }
.masthead-top { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 12px; }
.masthead-brand { display: flex; align-items: center; gap: 16px; }
.brand-mark {
    width: 48px; height: 48px; border-radius: 12px;
    background: linear-gradient(135deg, var(--neon-cyan), var(--neon-purple));
    display: grid; place-items: center; font-family: 'Fira Code', monospace !important;
    font-weight: 700; font-size: 1.1rem; color: #000 !important;
    box-shadow: 0 0 20px rgba(0, 229, 255, 0.2);
}
.brand-text-name { font-weight: 700; font-size: 1.8rem; color: var(--text-main) !important; line-height: 1.1; letter-spacing: -0.02em; }
.brand-text-sub { font-family: 'Fira Code', monospace !important; font-size: 0.65rem; color: var(--neon-cyan) !important; letter-spacing: 0.2em; text-transform: uppercase; margin-top: 4px; }
.masthead-right { display: flex; flex-direction: column; align-items: flex-end; gap: 6px; }
.live-indicator {
    display: flex; align-items: center; gap: 8px; font-family: 'Fira Code', monospace !important;
    font-size: 0.65rem; color: var(--neon-green) !important; letter-spacing: 0.1em; text-transform: uppercase;
    background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); padding: 4px 12px; border-radius: 20px;
}
.live-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--neon-green); box-shadow: 0 0 8px var(--neon-green); animation: pulse 2s infinite; }
.masthead-headline { font-size: 0.95rem; color: var(--text-muted) !important; border-top: 1px solid var(--bdr-color); padding-top: 16px; display: flex; align-items: center; justify-content: space-between; }
.mtag { font-family: 'Fira Code', monospace !important; font-size: 0.6rem; color: var(--text-muted) !important; background: rgba(255,255,255,0.05); border: 1px solid var(--bdr-color); border-radius: 4px; padding: 4px 10px; text-transform: uppercase; letter-spacing: 0.05em; }
.mtag.acc { background: rgba(0, 229, 255, 0.1); color: var(--neon-cyan) !important; border-color: rgba(0, 229, 255, 0.3); }

/* Stats */
.stats-strip { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; animation: fadeInUp 0.7s ease-out; }
.stat-cell { background: var(--bg-panel); backdrop-filter: var(--glass-blur); border: 1px solid var(--bdr-color); border-radius: 12px; padding: 20px; text-align: center; position: relative; overflow: hidden; }
.stat-cell::before { content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 3px; background: var(--c); opacity: 0.8; box-shadow: 0 0 10px var(--c); }
.stat-cell:nth-child(1) { --c: var(--neon-cyan); }
.stat-cell:nth-child(2) { --c: var(--neon-purple); }
.stat-cell:nth-child(3) { --c: var(--neon-green); }
.stat-cell:nth-child(4) { --c: var(--neon-orange); }
.stat-num { font-weight: 700; font-size: 2.5rem; line-height: 1; text-shadow: 0 0 15px rgba(255,255,255,0.1); }
.stat-num.a { color: var(--neon-cyan) !important; }
.stat-num.b { color: var(--neon-purple) !important; }
.stat-num.c { color: var(--neon-green) !important; }
.stat-num.d { color: var(--neon-orange) !important; }
.stat-lbl { font-family: 'Fira Code', monospace !important; font-size: 0.65rem; color: var(--text-muted) !important; text-transform: uppercase; letter-spacing: 0.15em; margin-top: 8px; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background: transparent !important; border-bottom: 1px solid var(--bdr-color) !important; gap: 24px !important; margin-bottom: 28px !important; }
.stTabs [data-baseweb="tab"] { background: transparent !important; border: none !important; border-bottom: 2px solid transparent !important; color: var(--text-dim) !important; font-family: 'Fira Code', monospace !important; font-size: 0.75rem !important; font-weight: 500 !important; letter-spacing: 0.1em !important; text-transform: uppercase !important; padding: 12px 0 !important; transition: all 0.3s ease !important; }
.stTabs [data-baseweb="tab"]:hover { color: var(--text-main) !important; }
.stTabs [aria-selected="true"] { color: var(--neon-cyan) !important; border-bottom: 2px solid var(--neon-cyan) !important; text-shadow: 0 0 10px rgba(0, 229, 255, 0.4) !important; }
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }

/* ══════════════════════════════════════════════
   NEW PREMIUM CHAT AREA: THE "CONTEXT RAIL"
══════════════════════════════════════════════ */

/* User Query - Sharp & Minimal */
.msg-u-wrap { 
    display: flex; justify-content: flex-end; 
    margin: 28px 0; 
    animation: fadeSlideLeft 0.5s cubic-bezier(0.2, 0.8, 0.2, 1) forwards; 
}
.msg-u-inner { max-width: 65%; }
.msg-u-bubble {
    background: rgba(255, 255, 255, 0.02); 
    border: 1px solid var(--bdr-strong);
    border-right: 3px solid var(--neon-purple); /* OS-style anchor edge */
    color: var(--text-main) !important; 
    border-radius: 8px 0px 0px 8px;
    padding: 18px 24px; 
    font-size: 0.95rem; 
    line-height: 1.6; 
    backdrop-filter: var(--glass-blur);
    box-shadow: -8px 8px 20px rgba(0,0,0,0.15);
}

/* System Response - The Full-Width Rail */
.msg-b-wrap { 
    margin-bottom: 32px; 
    animation: fadeSlideRight 0.5s cubic-bezier(0.2, 0.8, 0.2, 1) forwards; 
}
.msg-b-header {
    display: flex; align-items: center; gap: 10px;
    font-family: 'Fira Code', monospace !important; 
    font-size: 0.7rem; 
    color: var(--neon-cyan) !important; 
    text-transform: uppercase; 
    letter-spacing: 0.1em;
    margin-bottom: 12px;
}
.msg-b-header .live-dot-cyan {
    width: 6px; height: 6px; border-radius: 50%; 
    background: var(--neon-cyan); box-shadow: 0 0 8px var(--neon-cyan);
    animation: pulse 2s infinite;
}
.msg-b-header .badge {
    background: rgba(0, 229, 255, 0.1); border: 1px solid rgba(0, 229, 255, 0.25);
    padding: 3px 8px; border-radius: 4px; font-size: 0.6rem; letter-spacing: 0.15em;
    color: var(--neon-cyan); margin-left: auto;
}
.msg-b-bubble {
    background: linear-gradient(90deg, rgba(15, 23, 42, 0.8) 0%, rgba(15, 23, 42, 0.2) 100%);
    border: 1px solid var(--bdr-color); 
    border-left: 3px solid var(--neon-cyan);
    border-radius: 0px 8px 8px 0px; 
    padding: 24px; 
    font-size: 0.95rem; line-height: 1.75;
    color: var(--text-main) !important; 
    backdrop-filter: var(--glass-blur);
    box-shadow: 8px 12px 30px rgba(0,0,0,0.25), inset 2px 0 15px rgba(0,229,255,0.03);
}

/* Chat Input Overrides */
[data-testid="stChatInput"] {
    background: rgba(15, 23, 42, 0.85) !important; border: 1px solid var(--bdr-strong) !important;
    border-radius: 12px !important; box-shadow: 0 8px 32px rgba(0,0,0,0.5) !important;
    transition: all 0.3s ease !important; margin-top: 20px !important; backdrop-filter: blur(24px) !important;
}
[data-testid="stChatInput"]:focus-within { border-color: var(--neon-cyan) !important; box-shadow: 0 0 25px rgba(0, 229, 255, 0.2) !important; }
[data-testid="stChatInput"] textarea { color: var(--text-main) !important; font-size: 0.95rem !important; caret-color: var(--neon-cyan) !important; }
[data-testid="stChatInput"] textarea::placeholder { color: var(--text-dim) !important; }

/* Empty State - Luxe Edition */
.empty-state { text-align: center; padding: 8rem 2rem; animation: fadeInUp 0.8s cubic-bezier(0.2, 0.8, 0.2, 1); }
.empty-icon-wrapper { position: relative; display: inline-block; margin-bottom: 24px; }
.empty-icon-glow { position: absolute; top: 50%; left: 50%; width: 60px; height: 60px; transform: translate(-50%, -50%); background: var(--neon-cyan); border-radius: 50%; filter: blur(40px); opacity: 0.2; animation: pulse 4s infinite; }
.empty-icon { font-size: 3.5rem; filter: drop-shadow(0 0 15px rgba(255,255,255,0.1)); animation: float 4s ease-in-out infinite; position: relative; z-index: 2; }
.empty-head { font-weight: 600; font-size: 1.4rem; color: var(--text-main) !important; margin-bottom: 10px; letter-spacing: -0.01em; }
.empty-sub { font-family: 'Fira Code', monospace !important; font-size: 0.75rem; color: var(--text-muted) !important; line-height: 1.6; text-transform: uppercase; letter-spacing: 0.1em; }

/* ══════════════════════════════════════════════
   REST OF THE STYLES (Identical for Tabs 2,3,4)
══════════════════════════════════════════════ */
.cur { display: inline-block; width: 6px; height: 1.1em; background: var(--neon-cyan); margin-left: 6px; vertical-align: text-bottom; animation: pulse 0.8s infinite; box-shadow: 0 0 10px var(--neon-cyan); }
.streamlit-expanderHeader { background: rgba(0,0,0,0.3) !important; border: 1px solid var(--bdr-color) !important; border-radius: 6px !important; font-family: 'Fira Code', monospace !important; font-size: 0.7rem !important; color: var(--text-muted) !important; margin-top: 16px !important; }
.streamlit-expanderContent { background: rgba(0,0,0,0.15) !important; border: 1px solid var(--bdr-color) !important; border-top: none !important; }
.src-card { background: rgba(0,0,0,0.2); border: 1px solid var(--bdr-color); border-left: 3px solid var(--neon-purple); border-radius: 4px; padding: 16px; margin: 10px 0; }
.src-lbl { font-family: 'Fira Code', monospace !important; font-size: 0.65rem; color: var(--neon-purple) !important; text-transform: uppercase; margin-bottom: 6px; }
.src-origin { font-family: 'Fira Code', monospace !important; font-size: 0.6rem; color: var(--text-dim) !important; margin-bottom: 8px; }
.src-txt { font-size: 0.85rem; color: var(--text-muted) !important; line-height: 1.6; }
.stButton > button { background: rgba(255,255,255,0.05) !important; border: 1px solid var(--bdr-strong) !important; color: var(--text-main) !important; font-family: 'Fira Code', monospace !important; font-size: 0.7rem !important; border-radius: 8px !important; padding: 12px 24px !important; transition: all .2s ease !important; }
.stButton > button:hover { background: rgba(0, 229, 255, 0.1) !important; border-color: var(--neon-cyan) !important; box-shadow: 0 0 15px rgba(0,229,255,0.2) !important; }
[data-testid="stFileUploaderDropzone"] { background: rgba(0,0,0,0.2) !important; border: 1px dashed var(--bdr-strong) !important; border-radius: 8px !important; transition: all .2s !important; }
[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--neon-cyan) !important; background: rgba(0,229,255,0.05) !important; }
[data-testid="stFileUploaderDropzone"] p, [data-testid="stFileUploaderDropzone"] span { font-family: 'Fira Code', monospace !important; color: var(--text-muted) !important; font-size: 0.75rem !important; }
.sec-card { background: var(--bg-card); border: 1px solid var(--bdr-color); border-radius: 12px; padding: 24px; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); backdrop-filter: var(--glass-blur); transition: transform .2s; }
.sec-card:hover { border-color: var(--bdr-strong); transform: translateY(-2px); }
.sec-card-title { font-weight: 600; font-size: 1.1rem; color: var(--text-main) !important; margin-bottom: 16px; display: flex; align-items: center; gap: 12px; padding-bottom: 12px; border-bottom: 1px solid var(--bdr-color); }
.sec-card-title .accent-rule { display: inline-block; width: 24px; height: 4px; background: var(--neon-cyan); border-radius: 2px; box-shadow: 0 0 8px var(--neon-cyan); }
.sec-card-body { font-family: 'Fira Code', monospace !important; font-size: 0.75rem; color: var(--text-muted) !important; line-height: 2.2; }
.feat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.feat-item { font-family: 'Fira Code', monospace !important; font-size: 0.7rem; color: var(--text-muted) !important; background: rgba(0,0,0,0.3); border: 1px solid var(--bdr-color); border-radius: 6px; padding: 12px; display: flex; align-items: center; gap: 10px; }
.feat-item.done { border-left: 3px solid var(--neon-green); color: var(--text-main) !important; }
.feat-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--text-dim); flex-shrink: 0; }
.feat-item.done .feat-dot { background: var(--neon-green); box-shadow: 0 0 8px var(--neon-green); }
.eval-section-title { font-weight: 600; font-size: 1.3rem; color: var(--text-main) !important; margin-bottom: 8px; }
.eval-section-sub { font-family: 'Fira Code', monospace !important; font-size: 0.75rem; color: var(--text-dim) !important; margin-bottom: 24px; line-height: 1.8; }
.score-panel { background: var(--bg-card); border: 1px solid var(--bdr-color); border-radius: 12px; padding: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); backdrop-filter: var(--glass-blur); }
.score-panel-label { font-family: 'Fira Code', monospace !important; font-size: 0.7rem; color: var(--text-main) !important; text-transform: uppercase; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid var(--bdr-color); display: flex; align-items: center; gap: 10px; }
.score-panel-label .tool-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.score-row { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; }
.score-name { font-family: 'Fira Code', monospace !important; font-size: 0.7rem; color: var(--text-muted) !important; width: 150px; flex-shrink: 0; text-transform: uppercase; }
.score-track { flex: 1; height: 8px; background: rgba(255,255,255,0.05); border-radius: 4px; overflow: hidden; box-shadow: inset 0 1px 3px rgba(0,0,0,0.5); }
.score-fill { height: 8px; border-radius: 4px; }
.score-num { font-weight: 700; font-size: 1rem; width: 50px; text-align: right; flex-shrink: 0; }
.overall-panel { background: rgba(0,0,0,0.4); border-radius: 8px; padding: 24px; text-align: center; margin-top: 20px; border: 1px solid rgba(255,255,255,0.05); }
.overall-big { font-weight: 700; font-size: 3rem; line-height: 1; }
.overall-sub { font-family: 'Fira Code', monospace !important; font-size: 0.65rem; color: var(--text-muted) !important; text-transform: uppercase; margin-top: 12px; }
.q-entry { background: rgba(0,0,0,0.3); border: 1px solid var(--bdr-color); border-radius: 8px; padding: 16px; margin: 12px 0; }
.q-text { font-size: 0.95rem; color: var(--text-main) !important; margin-bottom: 12px; font-weight: 500; }
.q-badges { display: flex; flex-wrap: wrap; gap: 8px; }
.q-badge { font-family: 'Fira Code', monospace !important; font-size: 0.65rem; border-radius: 4px; padding: 6px 10px; background: rgba(255,255,255,0.05); border: 1px solid var(--bdr-color); }
.ingest-note { font-family: 'Fira Code', monospace !important; font-size: 0.7rem; color: var(--text-muted) !important; background: rgba(0,0,0,0.3); border: 1px solid var(--bdr-color); border-left: 3px solid var(--neon-cyan); border-radius: 6px; padding: 16px 20px; margin-top: 20px; line-height: 1.9; }
[data-testid="stAlert"] { font-family: 'Fira Code', monospace !important; font-size: 0.75rem !important; border-radius: 8px !important; }
.stSpinner > div { border-top-color: var(--neon-cyan) !important; }
.stToggle label { font-family: 'Fira Code', monospace !important; font-size: 0.7rem !important; color: var(--text-muted) !important; }

/* Animations */
@keyframes fadeInDown { from{opacity:0;transform:translateY(-15px)} to{opacity:1;transform:translateY(0)} }
@keyframes fadeInUp   { from{opacity:0;transform:translateY(15px)} to{opacity:1;transform:translateY(0)} }
@keyframes fadeSlideRight { from{opacity:0;transform:translateX(-25px)} to{opacity:1;transform:translateX(0)} }
@keyframes fadeSlideLeft  { from{opacity:0;transform:translateX(25px)} to{opacity:1;transform:translateX(0)} }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
@keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-10px)} }
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
    if v >= 0.8: return "STRONG"
    if v >= 0.6: return "FAIR"
    return "WEAK"

def render_score(name: str, score: float):
    col = score_color(score)
    pct = int(score * 100)
    st.markdown(f"""
    <div class="score-row">
        <div class="score-name">{name}</div>
        <div class="score-track">
            <div class="score-fill" style="width:{pct}%;background:{col};box-shadow:0 0 8px {col};"></div>
        </div>
        <div class="score-num" style="color:{col};text-shadow:0 0 8px {col};">{score:.2f}</div>
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
                <div class="brand-text-sub">Enterprise Knowledge OS &nbsp;·&nbsp; v4.5</div>
            </div>
        </div>
        <div class="masthead-right">
            <div class="live-indicator">
                <span class="live-dot"></span>System Online
            </div>
        </div>
    </div>
    <div class="masthead-headline">
        <span><em>Ask anything. Get grounded answers with source citations.</em></span>
        <div class="masthead-tags">
            <span class="mtag acc">Gemini 2.5 Flash</span>
            <span class="mtag">Pinecone 3072-dim</span>
            <span class="mtag">BM25 + Vector</span>
            <span class="mtag">RRF Fusion</span>
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
        <div class="stat-num a">{st.session_state.questions}</div>
        <div class="stat-lbl">Queries</div>
    </div>
    <div class="stat-cell">
        <div class="stat-num b">{len(st.session_state.messages)//2}</div>
        <div class="stat-lbl">Exchanges</div>
    </div>
    <div class="stat-cell">
        <div class="stat-num c">{avg:.1f}s</div>
        <div class="stat-lbl">Avg Latency</div>
    </div>
    <div class="stat-cell">
        <div class="stat-num d">{st.session_state.src_total}</div>
        <div class="stat-lbl">Chunks Retrieved</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════

tab1, tab2, tab3, tab4 = st.tabs(["Chat Area", "Ingest", "Evaluation", "System"])


# ════════════════════════════════════════════════
# TAB 1 — ULTRA PREMIUM CHAT AREA (Overhauled)
# ════════════════════════════════════════════════

with tab1:

    # --- 1. Toggles & Controls ---
    st.markdown("<br>", unsafe_allow_html=True)
    col_tog, col_btn = st.columns([8, 2])
    with col_tog:
        st.session_state.use_stream = st.toggle("Enable Streaming", value=st.session_state.use_stream)
    with col_btn:
        if st.button("Clear Memory", use_container_width=True):
            st.session_state.messages=[]; st.session_state.questions=0
            st.session_state.time_total=0.0; st.session_state.src_total=0
            st.session_state.session_id=f"nx_{str(uuid.uuid4())[:8]}"
            st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)

    # --- 2. Chat Messages Rendering ---
    if not st.session_state.messages:
        # Luxe Empty State
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon-wrapper">
                <div class="empty-icon-glow"></div>
                <div class="empty-icon">⬡</div>
            </div>
            <div class="empty-head">Knowledge Base is Online</div>
            <div class="empty-sub">Send a query below to initiate hybrid retrieval</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="msg-u-wrap">
                    <div class="msg-u-inner">
                        <div class="msg-u-bubble">{msg['content']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="msg-b-wrap">
                    <div class="msg-b-header">
                        <span class="live-dot-cyan"></span> NEXUS Core
                        <span class="badge">Verified Response</span>
                    </div>
                    <div class="msg-b-bubble">
                        {msg['content']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                rt = msg.get("response_time", 0)
                sc = msg.get("source_count", 0)
                srcs = msg.get("sources", [])
                
                if srcs:
                    with st.expander("Explore Synthesized Sources"):
                        st.markdown(f"""
                        <div style="font-family:'Inter',sans-serif; font-size: 0.85rem; color:var(--text-muted); margin-bottom:12px; padding-bottom:12px; border-bottom:1px solid rgba(255,255,255,0.05);">
                            Chunks Merged: <span style="color:var(--neon-cyan);">{sc}</span> | Pipeline: Hybrid (BM25 + Vector) | RTT: {rt:.2f}s
                        </div>
                        """, unsafe_allow_html=True)
                        
                        for j, src in enumerate(srcs, 1):
                            text = extract_src_text(src)
                            meta = extract_src_meta(src)
                            st.markdown(f"""
                            <div class="src-card">
                                <div class="src-lbl">Source node [{j}]</div>
                                {f'<div class="src-origin">{meta}</div>' if meta else ''}
                                <div class="src-txt">{text}</div>
                            </div>
                            """, unsafe_allow_html=True)


    # --- 3. Chat Input Handling ---
    question = st.chat_input("Ask about company policies, documents, or knowledge base...")

    if question:
        st.session_state.questions += 1
        st.session_state.messages.append({"role":"user","content":question,"sources":[]})

        # Render immediate user message
        st.markdown(f"""
        <div class="msg-u-wrap">
            <div class="msg-u-inner">
                <div class="msg-u-bubble">{question}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

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
                                        # Output with header and blinking cursor
                                        placeholder.markdown(f"""
                                        <div class="msg-b-wrap">
                                            <div class="msg-b-header">
                                                <span class="live-dot-cyan"></span> NEXUS Core
                                                <span class="badge">Generating...</span>
                                            </div>
                                            <div class="msg-b-bubble">{full_answer}<span class="cur"></span></div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    else:
                                        sources = data.get("sources",[])
                                        # Final output without cursor
                                        placeholder.markdown(f"""
                                        <div class="msg-b-wrap">
                                            <div class="msg-b-header">
                                                <span class="live-dot-cyan"></span> NEXUS Core
                                                <span class="badge">Verified Response</span>
                                            </div>
                                            <div class="msg-b-bubble">{full_answer}</div>
                                        </div>
                                        """, unsafe_allow_html=True)
            except: streamed_ok = False

        if not st.session_state.use_stream or not streamed_ok:
            with st.spinner("Executing hybrid retrieval pipeline..."):
                try:
                    res = requests.post(ASK_URL, json={"question":question,"session_id":st.session_state.session_id}, timeout=30)
                    if res.status_code == 200:
                        data = res.json(); full_answer = data.get("answer",""); sources = data.get("sources",[])
                    else:
                        full_answer = f"Backend error {res.status_code}."
                except requests.exceptions.Timeout:
                    full_answer = "Request timed out. Try again."
                except Exception as e:
                    full_answer = f"Error: {str(e)}"
            st.markdown(f"""
            <div class="msg-b-wrap">
                <div class="msg-b-header">
                    <span class="live-dot-cyan"></span> NEXUS Core
                    <span class="badge">Verified Response</span>
                </div>
                <div class="msg-b-bubble">{full_answer}</div>
            </div>
            """, unsafe_allow_html=True)

        elapsed = time.time() - t0
        st.session_state.time_total += elapsed
        st.session_state.src_total  += len(sources)

        if sources:
            with st.expander("Explore Synthesized Sources"):
                st.markdown(f"""
                <div style="font-family:'Inter',sans-serif; font-size: 0.85rem; color:var(--text-muted); margin-bottom:12px; padding-bottom:12px; border-bottom:1px solid rgba(255,255,255,0.05);">
                    Chunks Merged: <span style="color:var(--neon-cyan);">{len(sources)}</span> | Pipeline: Hybrid (BM25 + Vector) | RTT: {elapsed:.2f}s
                </div>
                """, unsafe_allow_html=True)
                for j, src in enumerate(sources, 1):
                    text = extract_src_text(src); meta = extract_src_meta(src)
                    st.markdown(f"""
                    <div class="src-card">
                        <div class="src-lbl">Source node [{j}]</div>
                        {f'<div class="src-origin">{meta}</div>' if meta else ''}
                        <div class="src-txt">{text}</div>
                    </div>
                    """, unsafe_allow_html=True)

        st.session_state.messages.append({
            "role":"assistant","content":full_answer,"sources":sources,
            "response_time":elapsed,"source_count":len(sources),"streamed":streamed_ok
        })
        st.rerun()


# ════════════════════════════════════════════════
# TAB 2 — INGEST 
# ════════════════════════════════════════════════

with tab2:

    st.markdown("""
    <div style="margin-bottom:22px;">
        <div style="font-family:'Inter',sans-serif;font-weight:600;font-size:1.3rem;color:var(--text-main);margin-bottom:8px;">
            Document Ingestion
        </div>
        <div style="font-family:'Fira Code',monospace;font-size:0.75rem;color:var(--text-muted);">
            PDF &nbsp;·&nbsp; TXT &nbsp;·&nbsp; Max 5MB recommended &nbsp;·&nbsp;
            Chunked at 500 tokens &nbsp;·&nbsp; Indexed in Pinecone + BM25
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])

    with col1:
        uploaded_file = st.file_uploader("Drop file", type=["pdf","txt"], label_visibility="collapsed")

        if uploaded_file:
            size_kb = len(uploaded_file.getvalue()) / 1024
            size_mb = size_kb / 1024
            if size_mb > 5:
                st.warning(f"File is {size_mb:.1f}MB — may timeout on free-tier. Recommended: under 5MB.")
            st.markdown(f"""
            <div style="font-family:'Fira Code',monospace;font-size:0.75rem;color:var(--neon-cyan);
                        background:rgba(0,229,255,0.05);border:1px solid rgba(0,229,255,0.2);
                        border-left:3px solid var(--neon-cyan);border-radius:6px;
                        padding:14px 18px;margin:16px 0;">
                &#9679;&nbsp; {uploaded_file.name} &nbsp;·&nbsp; {size_kb:.0f} KB
            </div>
            """, unsafe_allow_html=True)

            if st.button("Index Document"):
                with st.spinner("Ingesting..."):
                    try:
                        files = {"file":(uploaded_file.name,uploaded_file.getvalue(),uploaded_file.type)}
                        resp  = requests.post(UPLOAD_URL, files=files, timeout=180)
                        if resp.status_code == 200:
                            data = resp.json()
                            st.success(f"Indexed {data.get('total_chunks',0)} chunks · BM25 corpus: {data.get('bm25_corpus',0)}")
                            if uploaded_file.name not in st.session_state.uploaded_docs:
                                st.session_state.uploaded_docs.append(uploaded_file.name)
                        elif resp.status_code == 413:
                            st.error("File too large. Max 10MB.")
                        else:
                            st.error(f"Upload failed: {resp.status_code}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

        st.markdown("""
        <div class="ingest-note">
            Files split via RecursiveCharacterTextSplitter (chunk=500, overlap=100).<br>
            Each chunk indexed in Pinecone (vector) AND BM25 (keyword) simultaneously.<br>
            Hybrid retrieval merges both using Reciprocal Rank Fusion at query time.
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="sec-card">
            <div style="font-family:'Fira Code',monospace;font-size:0.65rem;color:var(--text-muted);
                        text-transform:uppercase;letter-spacing:0.12em;margin-bottom:16px;
                        padding-bottom:12px;border-bottom:1px solid var(--bdr-color);">
                Indexed This Session
            </div>
        """, unsafe_allow_html=True)

        if st.session_state.uploaded_docs:
            for d in st.session_state.uploaded_docs:
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;font-family:'Fira Code',monospace;
                            font-size:0.75rem;color:var(--neon-green);padding:8px 0;
                            border-bottom:1px solid rgba(255,255,255,0.05);">
                    <span style="width:6px;height:6px;border-radius:50%;background:var(--neon-green);
                                 flex-shrink:0;box-shadow:0 0 8px var(--neon-green);"></span>{d}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""<div style="font-family:'Fira Code',monospace;font-size:0.75rem;color:var(--text-dim);padding:8px 0;">No documents this session</div>""", unsafe_allow_html=True)

        st.markdown(f"""
            <div style="font-family:'Fira Code',monospace;font-size:0.65rem;color:var(--text-dim);
                        margin-top:20px;padding-top:16px;border-top:1px dashed var(--bdr-color);line-height:2;">
                SESSION ID<br>
                <span style="color:var(--text-muted);">{st.session_state.session_id}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════
# TAB 3 — EVALUATION 
# ════════════════════════════════════════════════

with tab3:

    st.markdown("""
    <div class="eval-section-title">RAG Quality Evaluation</div>
    <div class="eval-section-sub">
        RAGAS measures retrieval and answer quality across 4 metrics.<br>
        TruLens measures groundedness and contextual relevance across 3 metrics.<br>
        5 ground truth Q&amp;A pairs · Groq LLM as judge · ~60 seconds to complete.
    </div>
    """, unsafe_allow_html=True)

    col_btn, col_info = st.columns([2, 5])
    with col_btn:
        run_eval = st.button("Run Evaluation", use_container_width=True)
    with col_info:
        st.markdown("""
        <div style="font-family:'Fira Code',monospace;font-size:0.7rem;color:var(--text-muted);padding-top:10px;line-height:1.8;">
            Runs 5 predefined questions through the full RAG pipeline.<br>
            Results cached until next run.
        </div>
        """, unsafe_allow_html=True)

    if run_eval:
        with st.spinner("Running evaluation — this takes about 60 seconds..."):
            try:
                resp = requests.post(EVALUATE_URL, timeout=180)
                if resp.status_code == 200:
                    st.session_state.eval_results = resp.json()
                    st.success("Evaluation complete!")
                else:
                    st.error(f"Evaluation failed: {resp.status_code}")
            except requests.exceptions.Timeout:
                st.warning("Timed out — free-tier server is slow. Try again.")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    if st.session_state.eval_results:
        res     = st.session_state.eval_results
        ragas   = res.get("ragas", {})
        trulens = res.get("trulens", {})
        rs      = ragas.get("scores", {})
        ts      = trulens.get("scores", {})

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            <div class="score-panel">
                <div class="score-panel-label">
                    <span class="tool-dot" style="background:var(--neon-blue);box-shadow:0 0 8px var(--neon-blue);"></span>
                    RAGAS Metrics
                </div>
            """, unsafe_allow_html=True)
            for k, label in [("faithfulness","Faithfulness"),("answer_relevancy","Answer Relevancy"),
                              ("context_precision","Context Precision"),("context_recall","Context Recall")]:
                render_score(label, rs.get(k, 0))

            ov_r = rs.get("overall", 0)
            col_ovr = score_color(ov_r)
            st.markdown(f"""
                <div class="overall-panel">
                    <div class="overall-big" style="color:{col_ovr};text-shadow:0 0 15px {col_ovr};">{ov_r:.2f}</div>
                    <div class="overall-sub">RAGAS Overall &nbsp;·&nbsp; {score_label(ov_r)}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="score-panel">
                <div class="score-panel-label">
                    <span class="tool-dot" style="background:var(--neon-orange);box-shadow:0 0 8px var(--neon-orange);"></span>
                    TruLens Metrics
                </div>
            """, unsafe_allow_html=True)
            for k, label in [("groundedness","Groundedness"),("answer_relevance","Answer Relevance"),
                              ("context_relevance","Context Relevance")]:
                render_score(label, ts.get(k, 0))

            ov_t = ts.get("overall", 0)
            col_ovt = score_color(ov_t)
            st.markdown(f"""
                <div class="overall-panel">
                    <div class="overall-big" style="color:{col_ovt};text-shadow:0 0 15px {col_ovt};">{ov_t:.2f}</div>
                    <div class="overall-sub">TruLens Overall &nbsp;·&nbsp; {score_label(ov_t)}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        with st.expander("Per-question RAGAS scores"):
            for item in ragas.get("per_question", []):
                f=item.get("faithfulness",0); ar=item.get("answer_relevancy",0)
                cp=item.get("context_precision",0); cr=item.get("context_recall",0)
                st.markdown(f"""
                <div class="q-entry">
                    <div class="q-text">{item.get('question', 'Unknown')}</div>
                    <div class="q-badges">
                        <span class="q-badge" style="color:var(--neon-cyan);border-color:rgba(0,229,255,0.3);">Faith {f:.2f}</span>
                        <span class="q-badge" style="color:var(--neon-green);border-color:rgba(0,230,118,0.3);">Ans Rel {ar:.2f}</span>
                        <span class="q-badge" style="color:var(--neon-purple);border-color:rgba(139,92,246,0.3);">Ctx Pre {cp:.2f}</span>
                        <span class="q-badge" style="color:var(--neon-orange);border-color:rgba(249,115,22,0.3);">Ctx Rec {cr:.2f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with st.expander("Per-question TruLens scores"):
            for item in trulens.get("per_question", []):
                gs=item.get("groundedness",0); ar=item.get("answer_relevance",0); cr=item.get("context_relevance",0)
                st.markdown(f"""
                <div class="q-entry">
                    <div class="q-text">{item.get('question', 'Unknown')}</div>
                    <div style="font-family:'Inter',sans-serif;font-size:0.85rem;color:var(--text-muted);margin:4px 0 12px;font-style:italic;">{item.get('answer','')[:120]}…</div>
                    <div class="q-badges">
                        <span class="q-badge" style="color:var(--neon-orange);border-color:rgba(249,115,22,0.3);">Ground {gs:.2f}</span>
                        <span class="q-badge" style="color:var(--neon-green);border-color:rgba(0,230,118,0.3);">Ans Rel {ar:.2f}</span>
                        <span class="q-badge" style="color:var(--neon-cyan);border-color:rgba(0,229,255,0.3);">Ctx Rel {cr:.2f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    else:
        st.markdown("""
        <div style="text-align:center;padding:5rem 2rem;border:2px dashed rgba(255,255,255,0.08);border-radius:12px;margin-top:20px;background:var(--bg-panel);">
            <div style="font-size:3rem;color:var(--text-dim);margin-bottom:20px;">⚡</div>
            <div style="font-family:'Inter',sans-serif;font-weight:600;font-size:1.2rem;color:var(--text-main);">No evaluation run yet</div>
            <div style="font-family:'Fira Code',monospace;font-size:0.75rem;color:var(--text-muted);margin-top:10px;">Click Run Evaluation above to score the RAG pipeline</div>
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════
# TAB 4 — SYSTEM 
# ════════════════════════════════════════════════

with tab4:

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="sec-card">
            <div class="sec-card-title">
                <span class="accent-rule"></span>Hybrid RAG Pipeline
            </div>
            <div class="sec-card-body">
                <span style="color:var(--text-main);">USER QUERY</span><br>
                <span style="color:var(--neon-cyan);">↓</span>&nbsp; multi-query rewriting via Groq<br>
                <span style="color:var(--text-main);">HYBRID RETRIEVAL</span><br>
                <span style="color:var(--neon-cyan);">↓</span>&nbsp; Pinecone vector search (cosine)<br>
                <span style="color:var(--neon-cyan);">↓</span>&nbsp; BM25 keyword search (in-memory)<br>
                <span style="color:var(--text-main);">RRF FUSION</span><br>
                <span style="color:var(--neon-cyan);">↓</span>&nbsp; Reciprocal Rank Fusion merge<br>
                <span style="color:var(--text-main);">GUARDRAIL</span> <span style="color:var(--neon-cyan);">↓</span>&nbsp; score threshold 0.30<br>
                <span style="color:var(--text-main);">LLM GENERATION</span><br>
                <span style="color:var(--neon-cyan);">↓</span>&nbsp; Gemini 2.5 Flash + Groq fallback<br>
                <span style="color:var(--text-main);">STREAMING ANSWER + CITATIONS</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="sec-card">
            <div class="sec-card-title">
                <span class="accent-rule" style="background:var(--neon-purple);box-shadow:0 0 8px var(--neon-purple);"></span>Stack
            </div>
            <div class="sec-card-body" style="display:grid;grid-template-columns:120px 1fr;gap:4px;">
                <span style="color:var(--text-muted);">BACKEND</span> <span style="color:var(--text-main);">FastAPI + Uvicorn · Railway</span>
                <span style="color:var(--text-muted);">FRONTEND</span> <span style="color:var(--text-main);">Streamlit Cloud</span>
                <span style="color:var(--text-muted);">VECTOR DB</span> <span style="color:var(--text-main);">Pinecone serverless · 3072-dim</span>
                <span style="color:var(--text-muted);">KEYWORD</span> <span style="color:var(--text-main);">rank-bm25 (in-memory)</span>
                <span style="color:var(--text-muted);">FUSION</span> <span style="color:var(--text-main);">Reciprocal Rank Fusion</span>
                <span style="color:var(--text-muted);">EMBED</span> <span style="color:var(--text-main);">gemini-embedding-001</span>
                <span style="color:var(--text-muted);">LLM PRIMARY</span> <span style="color:var(--text-main);">Gemini 2.5 Flash</span>
                <span style="color:var(--text-muted);">LLM FALLBACK</span><span style="color:var(--text-main);">Groq llama-3.1-8b-instant</span>
                <span style="color:var(--text-muted);">EVALUATION</span> <span style="color:var(--text-main);">RAGAS + TruLens (Groq judge)</span>
                <span style="color:var(--text-muted);">SESSION</span> <span style="color:var(--text-main);">{st.session_state.session_id}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="sec-card">
        <div class="sec-card-title">
            <span class="accent-rule" style="background:var(--neon-green);box-shadow:0 0 8px var(--neon-green);"></span>Roadmap
        </div>
        <div class="feat-grid">
            <div class="feat-item done"><span class="feat-dot"></span>Streaming Responses (SSE)</div>
            <div class="feat-item done"><span class="feat-dot"></span>Hybrid BM25 + Vector Retrieval</div>
            <div class="feat-item done"><span class="feat-dot"></span>RAGAS Evaluation Pipeline</div>
            <div class="feat-item done"><span class="feat-dot"></span>TruLens Quality Tracing</div>
            <div class="feat-item done"><span class="feat-dot"></span>Reciprocal Rank Fusion</div>
            <div class="feat-item done"><span class="feat-dot"></span>Multi-query Rewriting</div>
            <div class="feat-item"><span class="feat-dot"></span>Redis Conversation Memory</div>
            <div class="feat-item"><span class="feat-dot"></span>Multi-Agent LangGraph</div>
            <div class="feat-item"><span class="feat-dot"></span>Cross-encoder Re-ranking</div>
            <div class="feat-item"><span class="feat-dot"></span>DOCX / HTML / CSV Ingestion</div>
        </div>
    </div>
    """, unsafe_allow_html=True)