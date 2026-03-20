"""
LangGraph Multi-Agent RAG System
NEXUS Enterprise Knowledge Assistant

Agent Graph:
─────────────────────────────────────────
 User Query
     ↓
 [PLANNER AGENT]
     → Understands intent
     → Decides search strategy
     → Generates targeted sub-queries
     ↓
 [RETRIEVER AGENT]
     → Runs hybrid search (BM25 + Vector)
     → Deduplicates and ranks chunks
     → Returns top context
     ↓
 [VALIDATOR AGENT]
     → Checks if context is sufficient
     → Scores relevance 0-1
     → Routes: sufficient → Answer
               insufficient → Clarify
     ↓
 [ANSWER AGENT]          [CLARIFIER AGENT]
     → Generates grounded   → Asks user for
       final answer           more context
     → Cites sources        → Human-in-the-loop
─────────────────────────────────────────

Free-tier safe:
- All LLM calls via API (Gemini/Groq/NVIDIA)
- No local models
- Lightweight state dict (no heavy objects)
- Lazy imports to avoid startup crashes
"""

import os
import re
from typing import TypedDict, Annotated, Literal
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY     = os.getenv("GROQ_API_KEY")
NVIDIA_API_KEY   = os.getenv("NVIDIA_API_KEY")


# ─────────────────────────────────────────────
# Agent State Schema
# ─────────────────────────────────────────────

class AgentState(TypedDict):
    """
    Shared state passed between all agents in the graph.
    Each agent reads and updates this state.
    """
    # Input
    question:        str
    session_id:      str
    chat_history:    str

    # Planner output
    search_queries:  list[str]
    search_strategy: str

    # Retriever output
    context:         str
    sources:         list[dict]
    chunk_count:     int

    # Validator output
    validation_score:   float
    validation_reason:  str
    is_sufficient:      bool

    # Answer / Clarifier output
    answer:          str
    needs_clarification: bool
    clarification_question: str

    # Metadata
    agents_used:     list[str]
    llm_used:        str
    error:           str


# ─────────────────────────────────────────────
# LLM Helper — 3-way fallback
# ─────────────────────────────────────────────

def call_llm(prompt: str, max_tokens: int = 512) -> tuple[str, str]:
    """
    Call LLMs in order: Gemini → Groq → NVIDIA
    Returns (response_text, llm_name)
    """
    # 1. Gemini
    try:
        from google import genai
        client   = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip(), "gemini-2.5-flash"
    except Exception as e:
        print(f"Gemini error in agent: {e}")

    # 2. Groq
    try:
        from groq import Groq
        client   = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.2
        )
        return response.choices[0].message.content.strip(), "groq/llama-3.1-8b"
    except Exception as e:
        print(f"Groq error in agent: {e}")

    # 3. NVIDIA NIM
    try:
        from openai import OpenAI
        client   = OpenAI(
            api_key=NVIDIA_API_KEY,
            base_url="https://integrate.api.nvidia.com/v1"
        )
        response = client.chat.completions.create(
            model="meta/llama-3.1-8b-instruct",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.2
        )
        return response.choices[0].message.content.strip(), "nvidia/llama-3.1-8b"
    except Exception as e:
        print(f"NVIDIA error in agent: {e}")

    return "All LLMs failed. Please try again.", "none"


# ─────────────────────────────────────────────
# AGENT 1 — Planner
# ─────────────────────────────────────────────

def planner_agent(state: AgentState) -> AgentState:
    """
    Understands user intent and creates a search strategy.

    Responsibilities:
    - Classify question type (factual, procedural, policy-based)
    - Generate 3-4 targeted search queries
    - Decide search strategy (broad vs specific)
    """
    question      = state["question"]
    chat_history  = state.get("chat_history", "")
    agents_used   = state.get("agents_used", [])

    print(f"[PLANNER] Processing: {question[:60]}...")

    prompt = f"""You are a search planning agent for an enterprise knowledge base.

Your job is to analyze the user's question and create an optimal search strategy.

User Question: {question}
{"Previous conversation:" + chat_history if chat_history else ""}

Respond in this EXACT format (no extra text):
INTENT: <one sentence describing what the user wants>
TYPE: <one of: factual / procedural / policy / comparison / general>
STRATEGY: <one of: specific / broad / multi-aspect>
QUERY_1: <first search query>
QUERY_2: <second search query>
QUERY_3: <third search query>"""

    response, llm = call_llm(prompt, max_tokens=300)

    # Parse response
    queries  = []
    strategy = "broad"
    intent   = question

    for line in response.split("\n"):
        line = line.strip()
        if line.startswith("QUERY_"):
            q = line.split(":", 1)[-1].strip()
            if q:
                queries.append(q)
        elif line.startswith("STRATEGY:"):
            strategy = line.split(":", 1)[-1].strip()
        elif line.startswith("INTENT:"):
            intent = line.split(":", 1)[-1].strip()

    # Always include original question
    queries.append(question)
    queries = list(dict.fromkeys(queries))[:4]  # deduplicate, keep max 4

    print(f"[PLANNER] Strategy: {strategy}, Queries: {len(queries)}")

    return {
        **state,
        "search_queries":  queries,
        "search_strategy": strategy,
        "agents_used":     agents_used + ["planner"],
        "llm_used":        llm
    }


# ─────────────────────────────────────────────
# AGENT 2 — Retriever
# ─────────────────────────────────────────────

def retriever_agent(state: AgentState) -> AgentState:
    """
    Executes hybrid search using planned queries.

    Responsibilities:
    - Run BM25 + Vector search for each query
    - Apply RRF fusion
    - Deduplicate and return top chunks
    """
    queries   = state.get("search_queries", [state["question"]])
    agents_used = state.get("agents_used", [])

    print(f"[RETRIEVER] Running {len(queries)} queries...")

    try:
        # Import here to avoid circular imports
        from app.api.rag_api import (
            vector_search,
            bm25_search,
            reciprocal_rank_fusion
        )

        all_vector = []
        all_bm25   = []

        for q in queries:
            all_vector.extend(vector_search(q, top_k=3))
            all_bm25.extend(bm25_search(q, top_k=3))

        # Deduplicate
        seen_v        = set()
        unique_vector = []
        for r in all_vector:
            if r["text"] not in seen_v:
                seen_v.add(r["text"])
                unique_vector.append(r)

        seen_b      = set()
        unique_bm25 = []
        for r in all_bm25:
            if r["text"] not in seen_b:
                seen_b.add(r["text"])
                unique_bm25.append(r)

        # RRF fusion
        fused = reciprocal_rank_fusion(unique_vector, unique_bm25)
        top   = fused[:5]

        if not top:
            return {
                **state,
                "context":     "",
                "sources":     [],
                "chunk_count": 0,
                "agents_used": agents_used + ["retriever"]
            }

        context = "\n\n".join([r["text"] for r in top])
        sources = [
            {
                "text":   r["text"],
                "source": r["metadata"].get("source", ""),
                "page":   r["metadata"].get("page", "")
            }
            for r in top
        ]

        print(f"[RETRIEVER] Retrieved {len(top)} chunks")

        return {
            **state,
            "context":     context,
            "sources":     sources,
            "chunk_count": len(top),
            "agents_used": agents_used + ["retriever"]
        }

    except Exception as e:
        print(f"[RETRIEVER] Error: {e}")
        return {
            **state,
            "context":     "",
            "sources":     [],
            "chunk_count": 0,
            "agents_used": agents_used + ["retriever"],
            "error":       str(e)
        }


# ─────────────────────────────────────────────
# AGENT 3 — Validator
# ─────────────────────────────────────────────

def validator_agent(state: AgentState) -> AgentState:
    """
    Validates whether retrieved context is sufficient to answer.

    Responsibilities:
    - Score relevance of context to question (0.0 - 1.0)
    - Decide: sufficient → proceed to Answer
              insufficient → proceed to Clarifier
    - Threshold: 0.5 (below = needs clarification)
    """
    question    = state["question"]
    context     = state.get("context", "")
    agents_used = state.get("agents_used", [])

    print(f"[VALIDATOR] Checking context sufficiency...")

    if not context:
        print("[VALIDATOR] No context — routing to clarifier")
        return {
            **state,
            "validation_score":  0.0,
            "validation_reason": "No relevant documents found in knowledge base.",
            "is_sufficient":     False,
            "agents_used":       agents_used + ["validator"]
        }

    prompt = f"""You are a quality validation agent for a RAG system.

Evaluate whether the retrieved context contains sufficient information to answer the question.

Question: {question}

Retrieved Context:
{context[:800]}

Reply in this EXACT format (no extra text):
SCORE: <decimal 0.0-1.0>
REASON: <one sentence explaining the score>
SUFFICIENT: <YES or NO>

Scoring guide:
0.8-1.0 = context directly and completely answers the question
0.5-0.7 = context partially answers the question
0.0-0.4 = context does not contain relevant information"""

    response, _ = call_llm(prompt, max_tokens=150)

    # Parse response
    score       = 0.5
    reason      = "Context partially relevant."
    is_sufficient = True

    for line in response.split("\n"):
        line = line.strip()
        if line.startswith("SCORE:"):
            try:
                val = float(re.findall(r"\d+\.?\d*", line)[0])
                score = val if val <= 1.0 else val / 10
            except Exception:
                score = 0.5
        elif line.startswith("REASON:"):
            reason = line.split(":", 1)[-1].strip()
        elif line.startswith("SUFFICIENT:"):
            val = line.split(":", 1)[-1].strip().upper()
            is_sufficient = val == "YES"

    # Override: if score below threshold, mark insufficient
    if score < 0.5:
        is_sufficient = False

    print(f"[VALIDATOR] Score: {score:.2f} | Sufficient: {is_sufficient}")

    return {
        **state,
        "validation_score":  score,
        "validation_reason": reason,
        "is_sufficient":     is_sufficient,
        "agents_used":       agents_used + ["validator"]
    }


# ─────────────────────────────────────────────
# AGENT 4A — Answer Agent
# ─────────────────────────────────────────────

def answer_agent(state: AgentState) -> AgentState:
    """
    Generates the final grounded answer.

    Responsibilities:
    - Use ONLY retrieved context
    - Generate complete, well-structured answer
    - Never hallucinate
    """
    question     = state["question"]
    context      = state["context"]
    chat_history = state.get("chat_history", "")
    agents_used  = state.get("agents_used", [])

    print(f"[ANSWER] Generating response...")

    prompt = (
        "You are an enterprise AI assistant. Answer the question using ONLY "
        "the provided context. Give complete answers with full sentences.\n\n"
        "Rules:\n"
        "- Use ONLY information from the context\n"
        "- Never invent or assume information\n"
        "- Give complete, well-structured answers\n"
        "- If context is insufficient say: "
        "'The information is not fully available in the provided documents'\n\n"
        f"{'Previous conversation:\n' + chat_history + chr(10) if chat_history else ''}"
        f"Context:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer:"
    )

    answer, llm = call_llm(prompt, max_tokens=1024)

    print(f"[ANSWER] Generated via {llm}")

    return {
        **state,
        "answer":                answer,
        "needs_clarification":   False,
        "clarification_question": "",
        "agents_used":           agents_used + ["answer"],
        "llm_used":              llm
    }


# ─────────────────────────────────────────────
# AGENT 4B — Clarifier Agent (Human-in-the-loop)
# ─────────────────────────────────────────────

def clarifier_agent(state: AgentState) -> AgentState:
    """
    Human-in-the-loop agent.
    When context is insufficient, asks user to clarify
    instead of hallucinating an answer.

    Responsibilities:
    - Explain what was found (if anything)
    - Ask a specific clarifying question
    - Guide user to rephrase or narrow their query
    """
    question    = state["question"]
    reason      = state.get("validation_reason", "")
    agents_used = state.get("agents_used", [])

    print(f"[CLARIFIER] Insufficient context — asking for clarification")

    prompt = f"""You are a helpful assistant. The knowledge base doesn't have enough 
information to fully answer the user's question.

User Question: {question}
Reason context was insufficient: {reason}

Generate a helpful response that:
1. Acknowledges you couldn't find complete information
2. Asks ONE specific clarifying question to help find better results
3. Suggests how to rephrase the question

Keep it concise and friendly."""

    clarification, llm = call_llm(prompt, max_tokens=200)

    return {
        **state,
        "answer":                clarification,
        "needs_clarification":   True,
        "clarification_question": clarification,
        "agents_used":           agents_used + ["clarifier"],
        "llm_used":              llm
    }


# ─────────────────────────────────────────────
# Router — Validator decision
# ─────────────────────────────────────────────

def route_after_validation(state: AgentState) -> Literal["answer", "clarify"]:
    """
    Routing function called after Validator agent.
    Determines next node based on validation result.
    """
    if state.get("is_sufficient", True):
        return "answer"
    return "clarify"


# ─────────────────────────────────────────────
# Build LangGraph
# ─────────────────────────────────────────────

def build_agent_graph():
    """
    Builds the LangGraph StateGraph with all 4 agents.

    Graph structure:
    START → planner → retriever → validator → (answer | clarifier) → END
    """
    from langgraph.graph import StateGraph, END

    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("planner",   planner_agent)
    graph.add_node("retriever", retriever_agent)
    graph.add_node("validator", validator_agent)
    graph.add_node("answer",    answer_agent)
    graph.add_node("clarifier", clarifier_agent)

    # Add edges
    graph.set_entry_point("planner")
    graph.add_edge("planner",   "retriever")
    graph.add_edge("retriever", "validator")

    # Conditional routing after validator
    graph.add_conditional_edges(
        "validator",
        route_after_validation,
        {
            "answer":  "answer",
            "clarify": "clarifier"
        }
    )

    # Both answer and clarifier go to END
    graph.add_edge("answer",    END)
    graph.add_edge("clarifier", END)

    return graph.compile()


# ─────────────────────────────────────────────
# Public Function
# ─────────────────────────────────────────────

def run_agent(question: str, session_id: str, chat_history: str = "") -> dict:
    """
    Run the full multi-agent pipeline.

    Args:
        question:     User question
        session_id:   Session ID for tracking
        chat_history: Previous conversation context

    Returns:
        dict with answer, sources, agents_used, metadata
    """
    try:
        agent_graph = build_agent_graph()

        initial_state: AgentState = {
            "question":               question,
            "session_id":             session_id,
            "chat_history":           chat_history,
            "search_queries":         [],
            "search_strategy":        "",
            "context":                "",
            "sources":                [],
            "chunk_count":            0,
            "validation_score":       0.0,
            "validation_reason":      "",
            "is_sufficient":          True,
            "answer":                 "",
            "needs_clarification":    False,
            "clarification_question": "",
            "agents_used":            [],
            "llm_used":               "",
            "error":                  ""
        }

        final_state = agent_graph.invoke(initial_state)

        return {
            "answer":              final_state.get("answer", "No answer generated."),
            "sources":             final_state.get("sources", []),
            "session_id":          session_id,
            "agents_used":         final_state.get("agents_used", []),
            "llm_used":            final_state.get("llm_used", "unknown"),
            "validation_score":    final_state.get("validation_score", 0.0),
            "needs_clarification": final_state.get("needs_clarification", False),
            "search_queries":      final_state.get("search_queries", []),
            "chunk_count":         final_state.get("chunk_count", 0),
            "pipeline":            "langgraph-multi-agent"
        }

    except Exception as e:
        print(f"Agent graph error: {e}")
        return {
            "answer":              f"Agent pipeline error: {str(e)}",
            "sources":             [],
            "session_id":          session_id,
            "agents_used":         [],
            "llm_used":            "none",
            "validation_score":    0.0,
            "needs_clarification": False,
            "search_queries":      [question],
            "chunk_count":         0,
            "pipeline":            "langgraph-multi-agent",
            "error":               str(e)
        }