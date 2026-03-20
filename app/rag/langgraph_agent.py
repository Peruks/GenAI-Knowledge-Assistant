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
# Agent State Schema
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
# LLM Helper — 3-way fallback
# ─────────────────────────────────────────────

def call_llm(prompt: str, max_tokens: int = 512) -> tuple:
    """Call LLMs in order: Gemini → Groq → NVIDIA. Returns (text, llm_name)."""

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
    Generates 3-4 targeted sub-queries from the original question.
    """
    question     = state["question"]
    chat_history = state.get("chat_history", "")
    agents_used  = state.get("agents_used", [])

    print(f"[PLANNER] Processing: {question[:60]}...")

    history_section = ""
    if chat_history:
        history_section = "Previous conversation:\n" + chat_history + "\n\n"

    prompt = (
        "You are a search planning agent for an enterprise knowledge base.\n\n"
        "Analyze the user question and create an optimal search strategy.\n\n"
        + history_section
        + "User Question: " + question + "\n\n"
        "Respond in this EXACT format (no extra text):\n"
        "INTENT: <one sentence describing what the user wants>\n"
        "TYPE: <one of: factual / procedural / policy / comparison / general>\n"
        "STRATEGY: <one of: specific / broad / multi-aspect>\n"
        "QUERY_1: <first search query>\n"
        "QUERY_2: <second search query>\n"
        "QUERY_3: <third search query>"
    )

    response, llm = call_llm(prompt, max_tokens=300)

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
    Executes hybrid BM25 + Vector search using planned queries.
    Applies RRF fusion and returns top ranked chunks.
    """
    queries     = state.get("search_queries", [state["question"]])
    agents_used = state.get("agents_used", [])

    print(f"[RETRIEVER] Running {len(queries)} queries...")

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
    Score >= 0.5 → Answer Agent
    Score < 0.5  → Clarifier Agent (human-in-the-loop)
    """
    question    = state["question"]
    context     = state.get("context", "")
    agents_used = state.get("agents_used", [])

    print("[VALIDATOR] Checking context sufficiency...")

    if not context:
        print("[VALIDATOR] No context — routing to clarifier")
        return {
            **state,
            "validation_score":  0.0,
            "validation_reason": "No relevant documents found in knowledge base.",
            "is_sufficient":     False,
            "agents_used":       agents_used + ["validator"]
        }

    prompt = (
        "You are a quality validation agent for a RAG system.\n\n"
        "Evaluate whether the retrieved context contains sufficient information "
        "to answer the question.\n\n"
        "Question: " + question + "\n\n"
        "Retrieved Context:\n" + context[:800] + "\n\n"
        "Reply in this EXACT format (no extra text):\n"
        "SCORE: <decimal 0.0-1.0>\n"
        "REASON: <one sentence explaining the score>\n"
        "SUFFICIENT: <YES or NO>\n\n"
        "Scoring guide:\n"
        "0.8-1.0 = context directly and completely answers the question\n"
        "0.5-0.7 = context partially answers the question\n"
        "0.0-0.4 = context does not contain relevant information"
    )

    response, _ = call_llm(prompt, max_tokens=150)

    score         = 0.5
    reason        = "Context partially relevant."
    is_sufficient = True

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
        elif line.startswith("SUFFICIENT:"):
            val = line.split(":", 1)[-1].strip().upper()
            is_sufficient = (val == "YES")

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
    Generates final grounded answer using ONLY retrieved context.
    Never hallucinates — strictly context-bound.
    """
    question     = state["question"]
    context      = state["context"]
    chat_history = state.get("chat_history", "")
    agents_used  = state.get("agents_used", [])

    print("[ANSWER] Generating response...")

    history_section = ""
    if chat_history:
        history_section = "Previous conversation:\n" + chat_history + "\n\n"

    prompt = (
        "You are an enterprise AI assistant. Answer using ONLY the provided context.\n\n"
        "Rules:\n"
        "- Use ONLY information from the context\n"
        "- Never invent or assume information\n"
        "- Give complete, well-structured answers with full sentences\n"
        "- Include relevant details, not just numbers\n"
        "- If context is insufficient say: "
        "'The information is not fully available in the provided documents'\n\n"
        + history_section
        + "Context:\n" + context + "\n\n"
        + "Question: " + question + "\n\n"
        + "Answer:"
    )

    answer, llm = call_llm(prompt, max_tokens=1024)

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
# AGENT 4B — Clarifier Agent (Human-in-the-loop)
# ─────────────────────────────────────────────

def clarifier_agent(state: AgentState) -> AgentState:
    """
    Human-in-the-loop agent.
    When context is insufficient, asks user to clarify
    instead of hallucinating. Guides user to rephrase.
    """
    question    = state["question"]
    reason      = state.get("validation_reason", "")
    agents_used = state.get("agents_used", [])

    print("[CLARIFIER] Insufficient context — asking for clarification")

    prompt = (
        "You are a helpful assistant. The knowledge base does not have enough "
        "information to fully answer the user's question.\n\n"
        "User Question: " + question + "\n"
        "Reason context was insufficient: " + reason + "\n\n"
        "Generate a helpful response that:\n"
        "1. Acknowledges you could not find complete information\n"
        "2. Asks ONE specific clarifying question to help find better results\n"
        "3. Suggests how to rephrase the question\n\n"
        "Keep it concise and friendly."
    )

    clarification, llm = call_llm(prompt, max_tokens=200)

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
    """
    Builds and compiles the LangGraph StateGraph.
    START → planner → retriever → validator → answer|clarifier → END
    """
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
        {
            "answer":  "answer",
            "clarify": "clarifier"
        }
    )

    graph.add_edge("answer",    END)
    graph.add_edge("clarifier", END)

    return graph.compile()


# ─────────────────────────────────────────────
# Public Entry Point
# ─────────────────────────────────────────────

def run_agent(question: str, session_id: str, chat_history: str = "") -> dict:
    """
    Run the full 4-agent LangGraph pipeline.
    Returns answer, sources, agent trace, and metadata.
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
            "search_strategy":     final_state.get("search_strategy", ""),
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
            "search_strategy":     "",
            "pipeline":            "langgraph-multi-agent",
            "error":               str(e)
        }