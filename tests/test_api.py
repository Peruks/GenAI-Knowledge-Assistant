"""
NEXUS API Test Suite
Runs on every git push via GitHub Actions.

Tests cover:
- Health check
- /ask endpoint
- /ask-agent endpoint
- /upload endpoint
- /evaluate endpoint
"""

import pytest
import requests

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────

BASE_URL    = "https://genai-knowledge-api-production.up.railway.app"
SESSION_ID  = "ci_test_session"
TIMEOUT     = 60


# ─────────────────────────────────────────────
# 1. Health Check
# ─────────────────────────────────────────────

def test_health_check():
    """API must be reachable and return correct version."""
    res = requests.get(f"{BASE_URL}/", timeout=TIMEOUT)

    assert res.status_code == 200

    data = res.json()
    assert "version"     in data
    assert "retrieval"   in data
    assert "bm25_corpus" in data
    assert data["retrieval"] == "hybrid (vector + BM25 + RRF)"


# ─────────────────────────────────────────────
# 2. /ask Endpoint
# ─────────────────────────────────────────────

def test_ask_returns_answer():
    """/ask must return a non-empty answer."""
    res = requests.post(
        f"{BASE_URL}/ask",
        json={
            "question":   "What is the sick leave policy?",
            "session_id": SESSION_ID
        },
        timeout=TIMEOUT
    )

    assert res.status_code == 200

    data = res.json()
    assert "answer"     in data
    assert "sources"    in data
    assert "session_id" in data
    assert len(data["answer"]) > 10


def test_ask_returns_sources():
    """/ask must return source chunks with the answer."""
    res = requests.post(
        f"{BASE_URL}/ask",
        json={
            "question":   "What is the annual leave entitlement?",
            "session_id": SESSION_ID
        },
        timeout=TIMEOUT
    )

    assert res.status_code == 200

    data    = res.json()
    sources = data.get("sources", [])
    assert isinstance(sources, list)


def test_ask_session_id_returned():
    """/ask must echo back the session_id."""
    res = requests.post(
        f"{BASE_URL}/ask",
        json={
            "question":   "What is the password policy?",
            "session_id": "test_session_abc"
        },
        timeout=TIMEOUT
    )

    assert res.status_code == 200
    assert res.json().get("session_id") == "test_session_abc"


# ─────────────────────────────────────────────
# 3. /ask-agent Endpoint
# ─────────────────────────────────────────────

def test_ask_agent_returns_answer():
    """/ask-agent must return answer with agent trace."""
    res = requests.post(
        f"{BASE_URL}/ask-agent",
        json={
            "question":   "What is the notice period for resignation?",
            "session_id": SESSION_ID
        },
        timeout=90
    )

    assert res.status_code == 200

    data = res.json()
    assert "answer"      in data
    assert "agents_used" in data
    assert "pipeline"    in data
    assert data["pipeline"] == "langgraph-multi-agent"
    assert len(data["agents_used"]) >= 3   # at minimum: planner, retriever, validator


def test_ask_agent_has_validation_score():
    """/ask-agent must return a validation score between 0 and 1."""
    res = requests.post(
        f"{BASE_URL}/ask-agent",
        json={
            "question":   "What is the expense reimbursement policy?",
            "session_id": SESSION_ID
        },
        timeout=90
    )

    assert res.status_code == 200

    data  = res.json()
    score = data.get("validation_score", -1)
    assert 0.0 <= score <= 1.0


# ─────────────────────────────────────────────
# 4. /upload Endpoint
# ─────────────────────────────────────────────

def test_upload_rejects_invalid_format():
    """/upload must reject non-PDF/TXT files."""
    res = requests.post(
        f"{BASE_URL}/upload",
        files={"file": ("test.csv", b"col1,col2\n1,2", "text/csv")},
        timeout=TIMEOUT
    )

    assert res.status_code == 400


def test_upload_accepts_txt():
    """/upload must accept TXT files and return chunk count."""
    sample_text = (
        "1. LEAVE POLICY\n\n"
        "Employees are entitled to 20 days of annual leave per year.\n\n"
        "2. SICK LEAVE\n\n"
        "Employees are entitled to 10 days of sick leave per year.\n"
    )

    res = requests.post(
        f"{BASE_URL}/upload",
        files={"file": ("ci_test.txt", sample_text.encode(), "text/plain")},
        timeout=TIMEOUT
    )

    assert res.status_code == 200

    data = res.json()
    assert "total_chunks" in data
    assert data["total_chunks"] > 0


# ─────────────────────────────────────────────
# 5. /evaluate Endpoint
# ─────────────────────────────────────────────

def test_evaluate_returns_scores():
    """/evaluate must return RAGAS and TruLens scores."""
    res = requests.post(
        f"{BASE_URL}/evaluate",
        timeout=180
    )

    assert res.status_code == 200

    data = res.json()
    assert "ragas"   in data
    assert "trulens" in data

    ragas_scores   = data["ragas"]["scores"]
    trulens_scores = data["trulens"]["scores"]

    # All expected metrics present
    for metric in ["faithfulness", "answer_relevancy", "context_precision", "context_recall", "overall"]:
        assert metric in ragas_scores

    for metric in ["groundedness", "answer_relevance", "context_relevance", "overall"]:
        assert metric in trulens_scores

    # All scores between 0 and 1
    for score in ragas_scores.values():
        assert 0.0 <= score <= 1.0

    for score in trulens_scores.values():
        assert 0.0 <= score <= 1.0