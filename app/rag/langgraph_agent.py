"""
LangGraph Multi-Agent RAG System
NEXUS Enterprise Knowledge Assistant

Smart LLM routing — each agent uses the best LLM for its task:
- Planner   → Groq      (fast query rewriting, cheap)
- Retriever → No LLM    (pure vector + BM25 search)
- Validator → NVIDIA    (separate quota for scoring)
- Answer    → Groq      (fast generation, high quota)
- Clarifier → Groq      (conversational, fast)
- Fallback  → Gemini    (last resort only)

Agent Graph:
START → planner → retriever → validator → answer|clarifier → END
"""

import os
import re
from typing import TypedDict, Literal
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")


# ─────────────────────────────────────────────
# Agent State
# ─────────────────────────────────────────────

class AgentState(TypedDict):
    question:               str
    session_id:             str
    chat_history:           str
    search_queries:         list
    search_strategy:        str
    context:                str
    sources:                list
    chunk_count:            int
    validation_score:       float
    validation_reason:      str
    is_sufficient:          bool
    answer:                 str
    needs_clarification:    bool
    clarification_question: str
    agents_used:            list
    llm_used:               str
    error:                  str


# ─────────────────────────────────────────────
# Per-agent LLM callers
# ─────────────────────────────────────────────

def call_groq(prompt: str, max_tokens: int = 512) -> tuple:
    """Groq — primary for Planner, Answer, Clarifier."""
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
        print(f"Groq error: {e}")
        return None, None


def call_nvidia(prompt: str, max_tokens: int = 256) -> tuple:
    """NVIDIA NIM — primary for Validator."""
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
            temperature=0.0
        )
        return response.choices[0].message.content.strip(), "nvidia/llama-3.1-8b"
    except Exception as e:
        print(f"NVIDIA error: {e}")
        return None, None


def call_gemini(prompt: str, max_tokens: int = 1024) -> tuple:
    """Gemini — fallback of last resort."""
    try:
        from google import genai
        client   = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip(), "gemini-2.5-flash"
    except Exception as e:
        print(f"Gemini error: {e}")
        return None, None


def call_with_fallback(prompt: str, primary: str = "groq", max_tokens: int = 512) -> tuple:
    """
    Call LLM with smart fallback.
    primary = "groq"   → Groq → NVIDIA → Gemini
    primary = "nvidia" → NVIDIA → Groq → Gemini
    """
    if primary == "groq":
        order = [call_groq, call_nvidia, call_gemini]
    elif primary == "nvidia":
        order = [call_nvidia, call_groq, call_gemini]
    else:
        order = [call_gemini, call_groq, call_nvidia]

    for caller in order:
        text, llm = caller(prompt, max_tokens)
        if text:
            return text, llm

    return "All LLMs failed. Please try again.", "none"


# ─────────────────────────────────────────────
# AGENT 1 — Planner (Groq)
# ─────────────────────────────────────────────

def planner_agent(state: AgentState) -> AgentState:
    """
    Analyzes user intent and generates targeted search queries.
    Uses Groq — fast and high quota for query rewriting.
    """
    question     = state["question"]
    chat_history = state.get("chat_history", "")
    agents_used  = state.get("agents_used", [])

    print(f"[PLANNER/Groq] {question[:60]}...")

    history_section = ""
    if chat_history:
        history_section = "Previous conversation:\n" + chat_history + "\n\n"

    prompt = (
        "You are a search planning agent for an enterprise knowledge base.\n\n"
        "Analyze the user question and create an optimal search strategy.\n\n"
        + history_section
        + "User Question: " + question + "\n\n"
        "Respond in this EXACT format:\n"
        "INTENT: <what the user wants>\n"
        "TYPE: <factual / procedural / policy / comparison / general>\n"
        "STRATEGY: <specific / broad / multi-aspect>\n"
        "QUERY_1: <first search query>\n"
        "QUERY_2: <second search query>\n"
        "QUERY_3: <third search query>"
    )

    response, llm = call_with_fallback(prompt, primary="groq", max_tokens=300)

    queries  = []
    strategy = "broad"

    for line in response.split("\n"):
        line = line.strip()
        if line.startswith("QUERY_"):
            q = line.split(":", 1)[-1].strip()
            if q:
                queries.append(q)
        elif line.startswith("STRATEGY:"):
            strategy = line.split(":", 1)[-1].strip()

    queries.append(question)
    queries = list(dict.fromkeys(queries))[:4]

    print(f"[PLANNER] {len(queries)} queries via {llm}")

    return {
        **state,
        "search_queries":  queries,
        "search_strategy": strategy,
        "agents_used":     agents_used + ["planner"],
        "llm_used":        llm
    }


# ─────────────────────────────────────────────
# AGENT 2 — Retriever (No LLM)
# ─────────────────────────────────────────────

def retriever_agent(state: AgentState) -> AgentState:
    """
    Pure hybrid search — no LLM involved.
    BM25 + Vector search + RRF fusion.
    Zero API quota consumed.
    """
    queries     = state.get("search_queries", [state["question"]])
    agents_used = state.get("agents_used", [])

    print(f"[RETRIEVER/NoLLM] {len(queries)} queries...")

    try:
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

        print(f"[RETRIEVER] {len(top)} chunks (no LLM used)")

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
# AGENT 3 — Validator (NVIDIA)
# ─────────────────────────────────────────────

def validator_agent(state: AgentState) -> AgentState:
    """
    Scores context sufficiency for answering the question.
    Uses NVIDIA — keeps NVIDIA quota separate from answer generation.
    Score >= 0.5 → Answer Agent
    Score < 0.5  → Clarifier Agent
    """
    question    = state["question"]
    context     = state.get("context", "")
    agents_used = state.get("agents_used", [])

    print("[VALIDATOR/NVIDIA] Checking sufficiency...")

    if not context:
        return {
            **state,
            "validation_score":  0.0,
            "validation_reason": "No relevant documents found.",
            "is_sufficient":     False,
            "agents_used":       agents_used + ["validator"]
        }

    prompt = (
        "You are a quality validation agent. Evaluate context sufficiency.\n\n"
        "Question: " + question + "\n\n"
        "Context:\n" + context[:800] + "\n\n"
        "Reply EXACTLY in this format:\n"
        "SCORE: <0.0-1.0>\n"
        "REASON: <one sentence>\n"
        "SUFFICIENT: <YES or NO>\n\n"
        "0.8-1.0 = fully answers the question\n"
        "0.5-0.7 = partially answers\n"
        "0.0-0.4 = insufficient information"
    )

    response, llm = call_with_fallback(prompt, primary="nvidia", max_tokens=150)

    score  = 0.5
    reason = "Context partially relevant."

    for line in response.split("\n"):
        line = line.strip()
        if line.startswith("SCORE:"):
            try:
                nums = re.findall(r"\d+\.?\d*", line)
                if nums:
                    val   = float(nums[0])
                    score = val if val <= 1.0 else val / 10
            except Exception:
                score = 0.5
        elif line.startswith("REASON:"):
            reason = line.split(":", 1)[-1].strip()

    # Derive is_sufficient purely from score
    # Fixes bug: NVIDIA returns "NO" text but score >= 0.5
    is_sufficient = score >= 0.6

    print(f"[VALIDATOR] Score: {score:.2f} via {llm}")

    return {
        **state,
        "validation_score":  score,
        "validation_reason": reason,
        "is_sufficient":     is_sufficient,
        "agents_used":       agents_used + ["validator"]
    }


# ─────────────────────────────────────────────
# AGENT 4A — Answer Agent (Groq → Gemini fallback)
# ─────────────────────────────────────────────

def answer_agent(state: AgentState) -> AgentState:
    """
    Generates final grounded answer.
    Uses Groq (fast, high quota) → Gemini fallback.
    """
    question     = state["question"]
    context      = state["context"]
    chat_history = state.get("chat_history", "")
    agents_used  = state.get("agents_used", [])

    print("[ANSWER/Groq] Generating...")

    history_section = ""
    if chat_history:
        history_section = "Previous conversation:\n" + chat_history + "\n\n"

    prompt = (
        "You are an enterprise AI assistant. Answer using ONLY the provided context.\n\n"
        "Rules:\n"
        "- Use ONLY information from the context\n"
        "- Never invent information\n"
        "- Give complete answers with full sentences\n"
        "- Include relevant details, not just numbers\n"
        "- If context is insufficient say: "
        "'The information is not fully available in the provided documents'\n\n"
        + history_section
        + "Context:\n" + context + "\n\n"
        + "Question: " + question + "\n\n"
        + "Answer:"
    )

    answer, llm = call_with_fallback(prompt, primary="groq", max_tokens=1024)

    # If Groq and NVIDIA both failed, try Gemini directly
    if not answer or llm == "none":
        answer, llm = call_gemini(prompt, max_tokens=1024)
        if not answer:
            answer = "Unable to generate answer. Please try again."
            llm    = "none"

    print(f"[ANSWER] Generated via {llm}")

    return {
        **state,
        "answer":                 answer,
        "needs_clarification":    False,
        "clarification_question": "",
        "agents_used":            agents_used + ["answer"],
        "llm_used":               llm
    }


# ─────────────────────────────────────────────
# AGENT 4B — Clarifier Agent (Groq)
# ─────────────────────────────────────────────

def clarifier_agent(state: AgentState) -> AgentState:
    """
    Human-in-the-loop. Asks user to clarify when context insufficient.
    Uses Groq — conversational, fast.
    """
    question    = state["question"]
    reason      = state.get("validation_reason", "")
    agents_used = state.get("agents_used", [])

    print("[CLARIFIER/Groq] Asking for clarification...")

    prompt = (
        "You are a helpful assistant. The knowledge base lacks sufficient info.\n\n"
        "User Question: " + question + "\n"
        "Why insufficient: " + reason + "\n\n"
        "Write a response that:\n"
        "1. Acknowledges the limitation politely\n"
        "2. Asks ONE specific clarifying question\n"
        "3. Suggests how to rephrase\n\n"
        "Keep it concise and friendly."
    )

    clarification, llm = call_with_fallback(prompt, primary="groq", max_tokens=200)

    return {
        **state,
        "answer":                 clarification,
        "needs_clarification":    True,
        "clarification_question": clarification,
        "agents_used":            agents_used + ["clarifier"],
        "llm_used":               llm
    }


# ─────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────

def route_after_validation(state: AgentState) -> Literal["answer", "clarify"]:
    if state.get("is_sufficient", True):
        return "answer"
    return "clarify"


# ─────────────────────────────────────────────
# Build LangGraph
# ─────────────────────────────────────────────

def build_agent_graph():
    from langgraph.graph import StateGraph, END

    graph = StateGraph(AgentState)

    graph.add_node("planner",   planner_agent)
    graph.add_node("retriever", retriever_agent)
    graph.add_node("validator", validator_agent)
    graph.add_node("answer",    answer_agent)
    graph.add_node("clarifier", clarifier_agent)

    graph.set_entry_point("planner")
    graph.add_edge("planner",   "retriever")
    graph.add_edge("retriever", "validator")

    graph.add_conditional_edges(
        "validator",
        route_after_validation,
        {"answer": "answer", "clarify": "clarifier"}
    )

    graph.add_edge("answer",    END)
    graph.add_edge("clarifier", END)

    return graph.compile()


# ─────────────────────────────────────────────
# Public Entry Point
# ─────────────────────────────────────────────

def run_agent(question: str, session_id: str, chat_history: str = "") -> dict:
    """Run the full 4-agent LangGraph pipeline."""
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
            "search_strategy":     final_state.get("search_strategy", ""),
            "pipeline":            "langgraph-multi-agent"
        }

    except Exception as e:
        print(f"Agent graph error: {e}")
        return {
            "answer":              "Agent pipeline error: " + str(e),
            "sources":             [],
            "session_id":          session_id,
            "agents_used":         [],
            "llm_used":            "none",
            "validation_score":    0.0,
            "needs_clarification": False,
            "search_queries":      [question],
            "chunk_count":         0,
            "search_strategy":     "",
            "pipeline":            "langgraph-multi-agent",
            "error":               str(e)
        }