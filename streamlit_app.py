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

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400;1,600&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&family=DM+Mono:wght@300;400;500&display=swap');

/* ══════════════════════════════════════════════
   ROOT VARIABLES — Warm editorial palette
══════════════════════════════════════════════ */
:root {
    --cream:    #f7f4ef;
    --cream2:   #ede9e2;
    --cream3:   #e2ddd5;
    --ink:      #1a1714;
    --ink2:     #3d3830;
    --ink3:     #6b6358;
    --ink4:     #9b9088;
    --ink5:     #c8c0b8;
    --acc:      #c84b2f;
    --acc2:     #e8693a;
    --acc-pale: #f5e8e4;
    --grn:      #2d6a4f;
    --grn-pale: #e8f4ee;
    --blu:      #1e3a5f;
    --blu-pale: #e8eef5;
    --amb:      #b5621e;
    --amb-pale: #f5ede4;
    --bdr:      rgba(26,23,20,0.10);
    --bdr2:     rgba(26,23,20,0.06);
    --shadow:   0 2px 16px rgba(26,23,20,0.08);
    --shadow2:  0 8px 40px rgba(26,23,20,0.12);
}

/* ══════════════════════════════════════════════
   BASE RESET
══════════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }

html, body, .stApp {
    font-family: 'DM Sans', sans-serif !important;
    background: var(--cream) !important;
    color: var(--ink) !important;
}

.stApp {
    background: var(--cream) !important;
    background-image:
        radial-gradient(ellipse 80% 50% at 50% -20%,
            rgba(200,75,47,0.04) 0%, transparent 60%) !important;
}

/* hide chrome */
#MainMenu, footer { visibility: hidden !important; }
header { visibility: hidden !important; }
.stDeployButton { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
[data-testid="chatAvatarIcon-user"],
[data-testid="chatAvatarIcon-assistant"],
[data-testid="stChatMessageAvatarUser"],
[data-testid="stChatMessageAvatarAssistant"] { display: none !important; }
[data-testid="stChatMessage"] {
    background: transparent !important; border: none !important;
    padding: 0 !important; gap: 0 !important;
}

.block-container {
    padding-top: 0 !important;
    max-width: 1100px !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}

/* ══════════════════════════════════════════════
   MASTHEAD
══════════════════════════════════════════════ */
.masthead {
    border-bottom: 3px solid var(--ink);
    padding: 28px 0 20px;
    margin-bottom: 0;
    animation: fadein .6s ease both;
}

.masthead-top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 12px;
}

.masthead-brand {
    display: flex;
    align-items: center;
    gap: 14px;
}

.brand-mark {
    width: 44px; height: 44px;
    background: var(--ink);
    clip-path: polygon(50% 0%,100% 25%,100% 75%,50% 100%,0% 75%,0% 25%);
    display: grid; place-items: center;
    font-family: 'DM Mono', monospace !important;
    font-weight: 500; font-size: 0.75rem;
    color: var(--cream) !important;
    flex-shrink: 0;
    animation: hexspin 20s linear infinite;
}

@keyframes hexspin {
    0%   { filter: brightness(1); }
    50%  { filter: brightness(1.2); }
    100% { filter: brightness(1); }
}

.brand-text-name {
    font-family: 'Playfair Display', serif !important;
    font-weight: 700; font-size: 1.6rem;
    letter-spacing: -0.02em; color: var(--ink) !important;
    line-height: 1;
}

.brand-text-sub {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.55rem; color: var(--ink4) !important;
    letter-spacing: 0.14em; text-transform: uppercase; margin-top: 3px;
}

.masthead-right {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 6px;
}

.live-indicator {
    display: flex; align-items: center; gap: 6px;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.58rem; color: var(--grn) !important;
    letter-spacing: 0.1em; text-transform: uppercase;
}

.live-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--grn);
    animation: livepulse 2s ease-in-out infinite;
}

@keyframes livepulse {
    0%,100% { opacity: 1; box-shadow: 0 0 0 0 rgba(45,106,79,.5); }
    50%      { opacity: .6; box-shadow: 0 0 0 5px rgba(45,106,79,0); }
}

.version-tag {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.52rem; color: var(--ink5) !important;
    letter-spacing: 0.1em;
}

/* Hero headline */
.masthead-headline {
    font-family: 'Playfair Display', serif !important;
    font-weight: 400; font-style: italic;
    font-size: 1.05rem; color: var(--ink3) !important;
    border-top: 1px solid var(--bdr);
    padding-top: 12px;
    display: flex; align-items: center;
    justify-content: space-between;
}

.masthead-tags {
    display: flex; gap: 8px; flex-wrap: wrap;
}

.mtag {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.52rem; color: var(--ink4) !important;
    background: var(--cream2); border: 1px solid var(--bdr);
    border-radius: 2px; padding: 2px 8px; letter-spacing: 0.06em;
    text-transform: uppercase;
}

.mtag.acc { background: var(--acc-pale); color: var(--acc) !important; border-color: rgba(200,75,47,0.2); }

/* ══════════════════════════════════════════════
   STATS STRIP
══════════════════════════════════════════════ */
.stats-strip {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    border-bottom: 1px solid var(--bdr);
    animation: fadein .7s ease both;
}

.stat-cell {
    padding: 18px 0;
    text-align: center;
    border-right: 1px solid var(--bdr);
    position: relative;
    transition: background .2s;
}

.stat-cell:last-child { border-right: none; }
.stat-cell:hover { background: var(--cream2); }

.stat-cell::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: var(--c); opacity: 0;
    transition: opacity .2s;
}
.stat-cell:hover::before { opacity: 1; }

.stat-cell:nth-child(1) { --c: var(--acc); }
.stat-cell:nth-child(2) { --c: var(--blu); }
.stat-cell:nth-child(3) { --c: var(--grn); }
.stat-cell:nth-child(4) { --c: var(--amb); }

.stat-num {
    font-family: 'Playfair Display', serif !important;
    font-weight: 700; font-size: 2.2rem; line-height: 1;
}

.stat-num.a { color: var(--acc) !important; }
.stat-num.b { color: var(--blu) !important; }
.stat-num.c { color: var(--grn) !important; }
.stat-num.d { color: var(--amb) !important; }

.stat-lbl {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.52rem; color: var(--ink4) !important;
    text-transform: uppercase; letter-spacing: 0.12em; margin-top: 4px;
}

/* ══════════════════════════════════════════════
   TABS
══════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--bdr) !important;
    gap: 0 !important;
    margin-bottom: 28px !important;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    color: var(--ink4) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.65rem !important;
    font-weight: 400 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    padding: 14px 24px !important;
    transition: all .2s !important;
}

.stTabs [data-baseweb="tab"]:hover {
    color: var(--ink) !important;
    background: var(--cream2) !important;
}

.stTabs [aria-selected="true"] {
    color: var(--acc) !important;
    border-bottom: 2px solid var(--acc) !important;
    background: transparent !important;
}

.stTabs [data-baseweb="tab-highlight"] { display: none !important; }

/* ══════════════════════════════════════════════
   CHAT — USER MESSAGE
══════════════════════════════════════════════ */
.msg-u-wrap {
    display: flex; justify-content: flex-end;
    margin: 16px 0; animation: slideright .25s ease both;
}

.msg-u-inner { max-width: 70%; }

.msg-u-lbl {
    text-align: right;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.5rem; letter-spacing: 0.16em; color: var(--ink4) !important;
    text-transform: uppercase; margin-bottom: 5px;
}

.msg-u-bubble {
    background: var(--ink);
    color: var(--cream) !important;
    border-radius: 16px 16px 4px 16px;
    padding: 14px 20px;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.92rem; line-height: 1.65;
}

/* ══════════════════════════════════════════════
   CHAT — BOT MESSAGE
══════════════════════════════════════════════ */
.msg-b-lbl {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.5rem; letter-spacing: 0.16em;
    color: var(--grn) !important; text-transform: uppercase;
    margin: 16px 0 5px; display: flex; align-items: center; gap: 7px;
    animation: slideleft .25s ease both;
}

.msg-b-lbl-dot {
    width: 5px; height: 5px; border-radius: 50%;
    background: var(--grn); flex-shrink: 0;
}

.msg-b-wrap {
    max-width: 82%;
    animation: slideleft .25s ease both;
    margin-bottom: 4px;
}

.msg-b-bubble {
    background: white;
    border: 1px solid var(--bdr);
    border-left: 3px solid var(--acc);
    border-radius: 0 16px 16px 16px;
    padding: 16px 22px;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.92rem; line-height: 1.78;
    color: var(--ink) !important;
    box-shadow: var(--shadow);
}

/* ══════════════════════════════════════════════
   META BADGE
══════════════════════════════════════════════ */
.msg-meta {
    display: inline-flex; align-items: center; gap: 8px;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.55rem; color: var(--ink4) !important;
    background: var(--cream2); border: 1px solid var(--bdr);
    border-radius: 3px; padding: 3px 10px; margin: 6px 0 16px;
    letter-spacing: 0.05em;
}

.meta-dot { width: 4px; height: 4px; border-radius: 50%; background: var(--grn); }

/* ══════════════════════════════════════════════
   STREAMING CURSOR
══════════════════════════════════════════════ */
.cur {
    display: inline-block; width: 2px; height: 0.9em;
    background: var(--acc); margin-left: 2px; vertical-align: text-bottom;
    animation: blink .7s ease-in-out infinite;
}

@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }

/* ══════════════════════════════════════════════
   SOURCE CARDS
══════════════════════════════════════════════ */
.src-card {
    background: var(--cream2);
    border: 1px solid var(--bdr);
    border-left: 3px solid var(--blu);
    border-radius: 0 6px 6px 0;
    padding: 12px 16px; margin: 8px 0;
}

.src-lbl {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.5rem; color: var(--blu) !important;
    text-transform: uppercase; letter-spacing: 0.14em; margin-bottom: 3px;
}

.src-origin {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.48rem; color: var(--ink5) !important;
    margin-bottom: 7px;
}

.src-txt {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.68rem; color: var(--ink3) !important; line-height: 1.75;
}

/* ══════════════════════════════════════════════
   EMPTY STATE
══════════════════════════════════════════════ */
.empty-state {
    text-align: center; padding: 5rem 2rem;
    animation: fadein .5s ease both;
}

.empty-mark {
    font-family: 'Playfair Display', serif !important;
    font-style: italic; font-size: 4rem;
    color: var(--cream3) !important;
    display: block; margin-bottom: 20px;
    animation: floatmark 4s ease-in-out infinite;
}

@keyframes floatmark { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-12px)} }

.empty-head {
    font-family: 'Playfair Display', serif !important;
    font-weight: 600; font-size: 1.3rem;
    color: var(--ink3) !important; margin-bottom: 8px;
}

.empty-sub {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.62rem; color: var(--ink5) !important; letter-spacing: 0.05em;
}

/* ══════════════════════════════════════════════
   CHAT INPUT
══════════════════════════════════════════════ */
[data-testid="stChatInput"] {
    background: white !important;
    border: 1px solid var(--bdr) !important;
    border-bottom: 2px solid var(--ink) !important;
    border-radius: 0 !important;
    box-shadow: var(--shadow) !important;
    transition: border-color .2s !important;
    margin-top: 20px !important;
}

[data-testid="stChatInput"]:focus-within {
    border-bottom-color: var(--acc) !important;
    box-shadow: var(--shadow2) !important;
}

[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: var(--ink) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.92rem !important;
    caret-color: var(--acc) !important;
}

[data-testid="stChatInput"] textarea::placeholder { color: var(--ink5) !important; }

/* ══════════════════════════════════════════════
   EXPANDER
══════════════════════════════════════════════ */
.streamlit-expanderHeader {
    background: var(--cream2) !important;
    border: 1px solid var(--bdr) !important;
    border-radius: 4px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.6rem !important; letter-spacing: 0.1em !important;
    color: var(--ink3) !important; text-transform: uppercase !important;
}

.streamlit-expanderContent {
    background: var(--cream2) !important;
    border: 1px solid var(--bdr) !important; border-top: none !important;
}

/* ══════════════════════════════════════════════
   BUTTONS
══════════════════════════════════════════════ */
.stButton > button {
    background: var(--ink) !important;
    border: 2px solid var(--ink) !important;
    color: var(--cream) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.62rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    border-radius: 3px !important;
    padding: 10px 22px !important;
    transition: all .15s ease !important;
}

.stButton > button:hover {
    background: var(--acc) !important;
    border-color: var(--acc) !important;
    color: white !important;
}

/* ══════════════════════════════════════════════
   FILE UPLOADER
══════════════════════════════════════════════ */
[data-testid="stFileUploaderDropzone"] {
    background: white !important;
    border: 2px dashed var(--bdr) !important;
    border-radius: 4px !important;
    transition: border-color .2s !important;
}

[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--acc) !important; }

[data-testid="stFileUploaderDropzone"] p,
[data-testid="stFileUploaderDropzone"] span,
[data-testid="stFileUploaderDropzone"] small {
    font-family: 'DM Mono', monospace !important;
    color: var(--ink4) !important; font-size: 0.68rem !important;
}

/* ══════════════════════════════════════════════
   SECTION CARDS
══════════════════════════════════════════════ */
.sec-card {
    background: white;
    border: 1px solid var(--bdr);
    border-radius: 6px;
    padding: 24px;
    margin-bottom: 14px;
    box-shadow: var(--shadow);
    transition: box-shadow .2s, transform .2s;
}

.sec-card:hover { box-shadow: var(--shadow2); transform: translateY(-2px); }

.sec-card-title {
    font-family: 'Playfair Display', serif !important;
    font-weight: 600; font-size: 1rem;
    color: var(--ink) !important;
    margin-bottom: 16px;
    display: flex; align-items: center; gap: 10px;
    padding-bottom: 10px; border-bottom: 1px solid var(--bdr);
}

.sec-card-title .accent-rule {
    display: inline-block; width: 24px; height: 3px;
    background: var(--acc); border-radius: 2px;
}

.sec-card-body {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.64rem; color: var(--ink3) !important; line-height: 2.2;
}

.feat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }

.feat-item {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.58rem; color: var(--ink3) !important;
    background: var(--cream2); border: 1px solid var(--bdr);
    border-radius: 3px; padding: 9px 12px;
    display: flex; align-items: center; gap: 8px;
    transition: all .15s;
}

.feat-item:hover { background: var(--cream3); }
.feat-item.done { border-left: 3px solid var(--grn); }
.feat-dot { width: 4px; height: 4px; border-radius: 50%; background: var(--ink4); flex-shrink: 0; }
.feat-item.done .feat-dot { background: var(--grn); }

/* ══════════════════════════════════════════════
   EVAL TAB
══════════════════════════════════════════════ */
.eval-section-title {
    font-family: 'Playfair Display', serif !important;
    font-weight: 600; font-size: 0.95rem;
    color: var(--ink) !important;
    margin-bottom: 4px;
}

.eval-section-sub {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.58rem; color: var(--ink4) !important;
    margin-bottom: 18px; line-height: 1.8;
}

.score-panel {
    background: white;
    border: 1px solid var(--bdr);
    border-radius: 6px;
    padding: 20px;
    box-shadow: var(--shadow);
}

.score-panel-label {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.56rem; color: var(--ink4) !important;
    text-transform: uppercase; letter-spacing: 0.14em;
    margin-bottom: 16px; padding-bottom: 10px;
    border-bottom: 1px solid var(--bdr);
    display: flex; align-items: center; gap: 8px;
}

.score-panel-label .tool-dot {
    width: 6px; height: 6px; border-radius: 50%;
    flex-shrink: 0;
}

.score-row {
    display: flex; align-items: center; gap: 12px; margin-bottom: 12px;
}

.score-name {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.58rem; color: var(--ink3) !important;
    width: 140px; flex-shrink: 0;
    text-transform: uppercase; letter-spacing: 0.06em;
}

.score-track {
    flex: 1; height: 6px; background: var(--cream2);
    border-radius: 3px; overflow: hidden;
}

.score-fill { height: 6px; border-radius: 3px; }

.score-num {
    font-family: 'Playfair Display', serif !important;
    font-weight: 700; font-size: 1rem;
    width: 50px; text-align: right; flex-shrink: 0;
}

.overall-panel {
    background: var(--ink);
    border-radius: 6px; padding: 20px; text-align: center;
    margin-top: 12px;
}

.overall-big {
    font-family: 'Playfair Display', serif !important;
    font-weight: 700; font-size: 2.8rem; line-height: 1;
    color: var(--cream) !important;
}

.overall-sub {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.52rem; color: var(--ink4) !important;
    text-transform: uppercase; letter-spacing: 0.12em; margin-top: 6px;
}

.q-entry {
    background: var(--cream2); border: 1px solid var(--bdr);
    border-radius: 4px; padding: 12px 16px; margin: 8px 0;
}

.q-text {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.85rem; color: var(--ink) !important; margin-bottom: 8px;
}

.q-badges { display: flex; flex-wrap: wrap; gap: 6px; }

.q-badge {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.56rem; border-radius: 3px; padding: 2px 8px;
    letter-spacing: 0.04em;
}

/* ══════════════════════════════════════════════
   INGEST NOTE
══════════════════════════════════════════════ */
.ingest-note {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.6rem; color: var(--ink3) !important;
    background: var(--cream2);
    border: 1px solid var(--bdr);
    border-left: 3px solid var(--acc);
    border-radius: 0 4px 4px 0;
    padding: 12px 16px; margin-top: 14px; line-height: 1.9;
}

/* ══════════════════════════════════════════════
   ALERTS + SPINNER
══════════════════════════════════════════════ */
[data-testid="stAlert"] {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.7rem !important; border-radius: 4px !important;
}

.stSpinner > div { border-top-color: var(--acc) !important; }

/* ══════════════════════════════════════════════
   TOGGLE
══════════════════════════════════════════════ */
.stToggle label { font-family: 'DM Mono', monospace !important; font-size: 0.62rem !important; color: var(--ink3) !important; }

/* ══════════════════════════════════════════════
   KEYFRAMES
══════════════════════════════════════════════ */
@keyframes fadein    { from{opacity:0} to{opacity:1} }
@keyframes slideright { from{opacity:0;transform:translateX(16px)} to{opacity:1;transform:translateX(0)} }
@keyframes slideleft  { from{opacity:0;transform:translateX(-16px)} to{opacity:1;transform:translateX(0)} }
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
    if v >= 0.8: return "#2d6a4f"
    if v >= 0.6: return "#b5621e"
    return "#c84b2f"

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
            <div class="score-fill" style="width:{pct}%;background:{col};"></div>
        </div>
        <div class="score-num" style="color:{col};">{score:.2f}</div>
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
                <div class="brand-text-name">NEXUS</div>
                <div class="brand-text-sub">Enterprise Knowledge OS &nbsp;·&nbsp; v4.1</div>
            </div>
        </div>
        <div class="masthead-right">
            <div class="live-indicator">
                <span class="live-dot"></span>System Online
            </div>
            <div class="version-tag">Hybrid RAG · RAGAS · TruLens</div>
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

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════

tab1, tab2, tab3, tab4 = st.tabs(["Chat", "Ingest", "Evaluation", "System"])


# ════════════════════════════════════════════════
# TAB 1 — CHAT
# ════════════════════════════════════════════════

with tab1:

    col_tog, _ = st.columns([2, 8])
    with col_tog:
        st.session_state.use_stream = st.toggle(
            "Streaming mode", value=st.session_state.use_stream)

    if not st.session_state.messages:
        st.markdown("""
        <div class="empty-state">
            <span class="empty-mark">◈</span>
            <div class="empty-head">Knowledge base is ready</div>
            <div class="empty-sub">
                Send a query below &nbsp;·&nbsp;
                Upload documents in Ingest &nbsp;·&nbsp;
                Check Evaluation for quality scores
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="msg-u-wrap">
                    <div class="msg-u-inner">
                        <div class="msg-u-lbl">You</div>
                        <div class="msg-u-bubble">{msg['content']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="msg-b-lbl">
                    <span class="msg-b-lbl-dot"></span>NEXUS
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
                        <span class="meta-dot"></span>
                        {rt:.2f}s &nbsp;·&nbsp; {sc} chunk{'s' if sc != 1 else ''} &nbsp;·&nbsp; hybrid retrieval
                    </div>
                    """, unsafe_allow_html=True)
                srcs = msg.get("sources", [])
                if srcs:
                    with st.expander(f"Sources — {len(srcs)} chunks retrieved"):
                        for j, src in enumerate(srcs, 1):
                            text = extract_src_text(src)
                            meta = extract_src_meta(src)
                            st.markdown(f"""
                            <div class="src-card">
                                <div class="src-lbl">Chunk {j:02d}</div>
                                {f'<div class="src-origin">{meta}</div>' if meta else ''}
                                <div class="src-txt">{text}</div>
                            </div>
                            """, unsafe_allow_html=True)

    question = st.chat_input("Ask about company policies, procedures, or uploaded documents...")

    if question:
        st.session_state.questions += 1
        st.session_state.messages.append({"role":"user","content":question,"sources":[]})

        st.markdown(f"""
        <div class="msg-u-wrap">
            <div class="msg-u-inner">
                <div class="msg-u-lbl">You</div>
                <div class="msg-u-bubble">{question}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="msg-b-lbl"><span class="msg-b-lbl-dot"></span>NEXUS</div>', unsafe_allow_html=True)

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
            with st.spinner(""):
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
            st.markdown(f'<div class="msg-b-wrap"><div class="msg-b-bubble">{full_answer}</div></div>', unsafe_allow_html=True)

        elapsed = time.time() - t0
        st.session_state.time_total += elapsed
        st.session_state.src_total  += len(sources)

        st.markdown(f"""
        <div class="msg-meta">
            <span class="meta-dot"></span>
            {elapsed:.2f}s &nbsp;·&nbsp; {len(sources)} chunk{'s' if len(sources)!=1 else ''} &nbsp;·&nbsp; hybrid retrieval
        </div>
        """, unsafe_allow_html=True)

        if sources:
            with st.expander(f"Sources — {len(sources)} chunks retrieved"):
                for j, src in enumerate(sources, 1):
                    text = extract_src_text(src); meta = extract_src_meta(src)
                    st.markdown(f"""
                    <div class="src-card">
                        <div class="src-lbl">Chunk {j:02d}</div>
                        {f'<div class="src-origin">{meta}</div>' if meta else ''}
                        <div class="src-txt">{text}</div>
                    </div>
                    """, unsafe_allow_html=True)

        st.session_state.messages.append({
            "role":"assistant","content":full_answer,"sources":sources,
            "response_time":elapsed,"source_count":len(sources),"streamed":streamed_ok
        })
        st.rerun()

    col_c, _ = st.columns([1,9])
    with col_c:
        if st.button("Clear"):
            st.session_state.messages=[]; st.session_state.questions=0
            st.session_state.time_total=0.0; st.session_state.src_total=0
            st.session_state.session_id=f"nx_{str(uuid.uuid4())[:8]}"
            st.rerun()


# ════════════════════════════════════════════════
# TAB 2 — INGEST
# ════════════════════════════════════════════════

with tab2:

    st.markdown("""
    <div style="margin-bottom:22px;">
        <div style="font-family:'Playfair Display',serif;font-weight:600;font-size:1.1rem;color:#1a1714;margin-bottom:5px;">
            Document Ingestion
        </div>
        <div style="font-family:'DM Mono',monospace;font-size:0.6rem;color:#9b9088;">
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
            <div style="font-family:'DM Mono',monospace;font-size:0.65rem;color:#c84b2f;
                        background:white;border:1px solid rgba(26,23,20,0.1);
                        border-left:3px solid #c84b2f;border-radius:0 4px 4px 0;
                        padding:10px 14px;margin:10px 0;">
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
        <div style="background:white;border:1px solid rgba(26,23,20,0.10);
                    border-radius:6px;padding:20px;box-shadow:0 2px 16px rgba(26,23,20,0.08);">
            <div style="font-family:'DM Mono',monospace;font-size:0.52rem;color:#9b9088;
                        text-transform:uppercase;letter-spacing:0.12em;margin-bottom:14px;
                        padding-bottom:10px;border-bottom:1px solid rgba(26,23,20,0.06);">
                Indexed This Session
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.uploaded_docs:
            for d in st.session_state.uploaded_docs:
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:8px;font-family:'DM Mono',monospace;
                            font-size:0.62rem;color:#2d6a4f;padding:6px 0;
                            border-bottom:1px solid rgba(26,23,20,0.06);">
                    <span style="width:5px;height:5px;border-radius:50%;background:#2d6a4f;
                                 flex-shrink:0;display:inline-block;"></span>{d}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""<div style="font-family:'DM Mono',monospace;font-size:0.62rem;color:#c8c0b8;padding:4px 0;">No documents this session</div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div style="font-family:'DM Mono',monospace;font-size:0.56rem;color:#c8c0b8;
                    margin-top:14px;padding-top:12px;border-top:1px solid rgba(26,23,20,0.06);line-height:2;">
            SESSION ID<br>
            <span style="color:#9b9088;">{st.session_state.session_id}</span>
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
        <div style="font-family:'DM Mono',monospace;font-size:0.58rem;color:#9b9088;padding-top:10px;line-height:1.8;">
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
                    <span class="tool-dot" style="background:#1e3a5f;"></span>
                    RAGAS Metrics
                </div>
            </div>
            """, unsafe_allow_html=True)
            with st.container():
                for k, label in [("faithfulness","Faithfulness"),("answer_relevancy","Answer Relevancy"),
                                  ("context_precision","Context Precision"),("context_recall","Context Recall")]:
                    render_score(label, rs.get(k, 0))

            ov_r = rs.get("overall", 0)
            st.markdown(f"""
            <div class="overall-panel">
                <div class="overall-big">{ov_r:.2f}</div>
                <div class="overall-sub">RAGAS Overall &nbsp;·&nbsp; {score_label(ov_r)}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="score-panel">
                <div class="score-panel-label">
                    <span class="tool-dot" style="background:#b5621e;"></span>
                    TruLens Metrics
                </div>
            </div>
            """, unsafe_allow_html=True)
            with st.container():
                for k, label in [("groundedness","Groundedness"),("answer_relevance","Answer Relevance"),
                                  ("context_relevance","Context Relevance")]:
                    render_score(label, ts.get(k, 0))

            ov_t = ts.get("overall", 0)
            st.markdown(f"""
            <div class="overall-panel">
                <div class="overall-big">{ov_t:.2f}</div>
                <div class="overall-sub">TruLens Overall &nbsp;·&nbsp; {score_label(ov_t)}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        with st.expander("Per-question RAGAS scores"):
            for item in ragas.get("per_question", []):
                f=item.get("faithfulness",0); ar=item.get("answer_relevancy",0)
                cp=item.get("context_precision",0); cr=item.get("context_recall",0)
                st.markdown(f"""
                <div class="q-entry">
                    <div class="q-text">{item['question']}</div>
                    <div class="q-badges">
                        <span class="q-badge" style="background:#e8eef5;color:#1e3a5f;">Faith {f:.2f}</span>
                        <span class="q-badge" style="background:#e8f4ee;color:#2d6a4f;">Ans Rel {ar:.2f}</span>
                        <span class="q-badge" style="background:#e8eef5;color:#1e3a5f;">Ctx Pre {cp:.2f}</span>
                        <span class="q-badge" style="background:#f5ede4;color:#b5621e;">Ctx Rec {cr:.2f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with st.expander("Per-question TruLens scores"):
            for item in trulens.get("per_question", []):
                gs=item.get("groundedness",0); ar=item.get("answer_relevance",0); cr=item.get("context_relevance",0)
                st.markdown(f"""
                <div class="q-entry">
                    <div class="q-text">{item['question']}</div>
                    <div style="font-family:'DM Mono',monospace;font-size:0.62rem;color:#9b9088;margin:4px 0 8px;">{item.get('answer','')[:120]}…</div>
                    <div class="q-badges">
                        <span class="q-badge" style="background:#f5ede4;color:#b5621e;">Ground {gs:.2f}</span>
                        <span class="q-badge" style="background:#e8f4ee;color:#2d6a4f;">Ans Rel {ar:.2f}</span>
                        <span class="q-badge" style="background:#e8eef5;color:#1e3a5f;">Ctx Rel {cr:.2f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    else:
        st.markdown("""
        <div style="text-align:center;padding:4rem 2rem;border:2px dashed rgba(26,23,20,0.08);border-radius:6px;margin-top:16px;">
            <div style="font-family:'Playfair Display',serif;font-style:italic;font-size:3rem;color:rgba(26,23,20,0.08);margin-bottom:16px;">◈</div>
            <div style="font-family:'Playfair Display',serif;font-weight:600;font-size:1rem;color:#9b9088;">No evaluation run yet</div>
            <div style="font-family:'DM Mono',monospace;font-size:0.6rem;color:#c8c0b8;margin-top:6px;">Click Run Evaluation above to score the RAG pipeline</div>
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
                USER QUERY<br>
                &darr;&nbsp; multi-query rewriting via Groq<br>
                HYBRID RETRIEVAL<br>
                &darr;&nbsp; Pinecone vector search (cosine)<br>
                &darr;&nbsp; BM25 keyword search (in-memory)<br>
                RRF FUSION<br>
                &darr;&nbsp; Reciprocal Rank Fusion merge<br>
                GUARDRAIL &darr;&nbsp; score threshold 0.30<br>
                LLM GENERATION<br>
                &darr;&nbsp; Gemini 2.5 Flash + Groq fallback<br>
                STREAMING ANSWER + CITATIONS
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="sec-card">
            <div class="sec-card-title">
                <span class="accent-rule"></span>Stack
            </div>
            <div class="sec-card-body">
                BACKEND &nbsp;&nbsp;&nbsp;&nbsp; FastAPI + Uvicorn · Railway<br>
                FRONTEND &nbsp;&nbsp;&nbsp; Streamlit Cloud<br>
                VECTOR DB &nbsp;&nbsp; Pinecone serverless · 3072-dim<br>
                KEYWORD &nbsp;&nbsp;&nbsp;&nbsp; rank-bm25 (in-memory)<br>
                FUSION &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Reciprocal Rank Fusion<br>
                EMBED &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; gemini-embedding-001<br>
                LLM PRIMARY &nbsp;Gemini 2.5 Flash<br>
                LLM FALLBACK Groq llama-3.1-8b-instant<br>
                EVALUATION &nbsp; RAGAS + TruLens (Groq judge)<br>
                SESSION &nbsp;&nbsp;&nbsp;&nbsp; {st.session_state.session_id}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="sec-card">
        <div class="sec-card-title">
            <span class="accent-rule"></span>Roadmap
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