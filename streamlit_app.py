import streamlit as st
import requests
import uuid
import time

# ------------------------------------------------
# Backend Configuration
# ------------------------------------------------

API_BASE = "https://genai-knowledge-api-production.up.railway.app"

ASK_URL = f"{API_BASE}/ask"
UPLOAD_URL = f"{API_BASE}/upload"


# ------------------------------------------------
# Page Configuration
# ------------------------------------------------

st.set_page_config(
    page_title="Enterprise Knowledge Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ------------------------------------------------
# Premium Theme + Animations
# ------------------------------------------------

st.markdown("""
<style>

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

html, body {
    font-family: Inter, sans-serif;
}

.stApp {
    background:
    radial-gradient(circle at top,#0f172a,#020617);
}

/* Container */

.block-container{
    max-width:1000px;
    padding-top:3rem;
}

/* Gradient title */

.main-title{
    text-align:center;
    font-size:48px;
    font-weight:800;
    background:linear-gradient(90deg,#60a5fa,#a78bfa);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
}

/* Subtitle */

.sub-title{
    text-align:center;
    color:#94a3b8;
    margin-bottom:30px;
}

/* Glass card */

.glass{
    background:rgba(30,41,59,0.35);
    backdrop-filter:blur(10px);
    border:1px solid rgba(148,163,184,0.2);
    border-radius:14px;
    padding:20px;
    transition:0.2s;
}

.glass:hover{
    transform:translateY(-2px);
}

/* Metrics */

.metric{
    font-size:28px;
    font-weight:700;
    color:white;
    text-align:center;
}

/* Chat bubbles */

.user-bubble{
    background:#2563eb;
    color:white;
    padding:14px 18px;
    border-radius:14px;
    margin-bottom:12px;
    animation:fadein .25s;
}

.bot-bubble{
    background:#1e293b;
    color:white;
    padding:14px 18px;
    border-radius:14px;
    margin-bottom:12px;
    animation:fadein .25s;
}

/* Sources */

.source-card{
    background:#020617;
    border:1px solid #334155;
    border-radius:10px;
    padding:12px;
    margin-bottom:8px;
}

/* Typing animation */

.typing span{
    animation:blink 1.4s infinite;
}

.typing span:nth-child(2){animation-delay:.2s}
.typing span:nth-child(3){animation-delay:.4s}

@keyframes blink{
    0%{opacity:.2}
    20%{opacity:1}
    100%{opacity:.2}
}

/* Fade animation */

@keyframes fadein{
    from{opacity:0;transform:translateY(5px)}
    to{opacity:1}
}

/* Sidebar */

.sidebar{
    background:#020617;
}

/* Chat input */

[data-testid="stChatInput"] textarea{
    font-size:16px;
}

</style>
""", unsafe_allow_html=True)


# ------------------------------------------------
# Session State
# ------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "questions" not in st.session_state:
    st.session_state.questions = 0

if "time_total" not in st.session_state:
    st.session_state.time_total = 0

if "conversation_list" not in st.session_state:
    st.session_state.conversation_list = []


# ------------------------------------------------
# Sidebar (Conversation History)
# ------------------------------------------------

with st.sidebar:

    st.title("💬 Conversations")

    if st.button("➕ New Chat"):

        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())

    for i,conv in enumerate(st.session_state.conversation_list):

        if st.button(conv):

            st.session_state.messages = []
            st.session_state.session_id = str(uuid.uuid4())


# ------------------------------------------------
# Header
# ------------------------------------------------

st.markdown(
"<div class='main-title'>Enterprise Knowledge Assistant</div>",
unsafe_allow_html=True
)

st.markdown(
"<div class='sub-title'>RAG · Vector Search · Guardrails · Conversational Memory</div>",
unsafe_allow_html=True
)


# ------------------------------------------------
# Metrics
# ------------------------------------------------

avg = 0
if st.session_state.questions > 0:
    avg = st.session_state.time_total / st.session_state.questions

c1,c2,c3 = st.columns(3)

with c1:
    st.markdown(f"<div class='glass'><div class='metric'>{st.session_state.questions}</div>Questions</div>",unsafe_allow_html=True)

with c2:
    st.markdown(f"<div class='glass'><div class='metric'>{len(st.session_state.messages)}</div>Messages</div>",unsafe_allow_html=True)

with c3:
    st.markdown(f"<div class='glass'><div class='metric'>{avg:.2f}s</div>Avg Response</div>",unsafe_allow_html=True)

st.write("")


# ------------------------------------------------
# Tabs
# ------------------------------------------------

chat_tab, upload_tab, about_tab = st.tabs(["💬 Chat","📄 Upload","ℹ️ About"])


# ========================================================
# CHAT TAB
# ========================================================

with chat_tab:

    for msg in st.session_state.messages:

        if msg["role"] == "user":

            st.markdown(
                f"<div class='user-bubble'>{msg['content']}</div>",
                unsafe_allow_html=True
            )

        else:

            st.markdown(
                f"<div class='bot-bubble'>{msg['content']}</div>",
                unsafe_allow_html=True
            )

            if msg.get("sources"):

                with st.expander("Sources"):

                    for s in msg["sources"]:

                        st.markdown(
                        f"<div class='source-card'><b>{s.get('source','')}</b><br>{s.get('text','')[:400]}</div>",
                        unsafe_allow_html=True
                        )

    question = st.chat_input("Ask about company policies...")

    if question:

        st.session_state.questions += 1

        st.session_state.messages.append({
            "role":"user",
            "content":question
        })

        with st.spinner("Thinking..."):

            start=time.time()

            try:

                payload={
                    "question":question,
                    "session_id":st.session_state.session_id
                }

                r=requests.post(ASK_URL,json=payload,timeout=60)

                end=time.time()

                st.session_state.time_total += (end-start)

                if r.status_code==200:

                    data=r.json()

                    answer=data.get("answer","No answer")

                    sources=data.get("sources",[])

                else:

                    answer="Backend error"
                    sources=[]

            except Exception as e:

                answer=str(e)
                sources=[]

        # Streaming style render

        message_container = st.empty()
        displayed = ""

        for word in answer.split():

            displayed += word + " "
            message_container.markdown(
                f"<div class='bot-bubble'>{displayed}</div>",
                unsafe_allow_html=True
            )
            time.sleep(0.02)

        st.session_state.messages.append({
            "role":"assistant",
            "content":answer,
            "sources":sources
        })

        st.rerun()

    if st.button("Clear Chat"):

        st.session_state.messages = []


# ========================================================
# UPLOAD TAB
# ========================================================

with upload_tab:

    st.markdown("### Upload Company Documents")

    file = st.file_uploader(
        "Upload PDF or TXT",
        type=["pdf","txt"]
    )

    if file:

        if st.button("Index Document"):

            with st.spinner("Processing document..."):

                try:

                    files={
                        "file":(
                            file.name,
                            file.getvalue(),
                            file.type
                        )
                    }

                    r=requests.post(
                        UPLOAD_URL,
                        files=files,
                        timeout=300
                    )

                    if r.status_code==200:

                        data=r.json()

                        st.success(
                            f"Indexed {data.get('chunks',0)} chunks"
                        )

                    else:

                        st.error("Upload failed")

                except Exception as e:

                    st.error(str(e))


# ========================================================
# ABOUT TAB
# ========================================================

with about_tab:

    st.markdown("### Architecture")

    st.code("""
User Question
      ↓
Query Rewriting
      ↓
Multiple Queries
      ↓
Gemini Embeddings
      ↓
Pinecone Vector Search
      ↓
Context Retrieval
      ↓
LLM Router
   Gemini / Groq
      ↓
Answer + Sources
""")

    st.markdown("""
Stack

FastAPI  
Streamlit  
Pinecone  
Gemini API  
Groq  
LangChain Splitter
""")