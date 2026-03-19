"""
RAGAS Evaluation Script
Measures RAG pipeline quality using 4 core metrics:
- Faithfulness
- Answer Relevancy
- Context Precision
- Context Recall

Run locally:
    python app/evaluation/ragas_eval.py
"""

import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.evaluation.eval_dataset import EVAL_DATASET


def run_ragas_evaluation():
    """
    Run RAGAS evaluation against the RAG pipeline.
    Returns dict with metric scores.
    """

    try:
        from ragas import evaluate
        from ragas.metrics import (
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        )
        from datasets import Dataset
        from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Run: pip install ragas datasets langchain-google-genai")
        return None

    # ── Import RAG pipeline ──
    try:
        from app.api.rag_api import retrieve_context, gemini_client
    except ImportError:
        print("Could not import RAG pipeline. Run from project root.")
        return None

    print("Running RAGAS evaluation on 5 questions...")
    print("-" * 50)

    questions    = []
    answers      = []
    contexts     = []
    ground_truths = []

    for i, item in enumerate(EVAL_DATASET):
        q  = item["question"]
        gt = item["ground_truth"]

        print(f"[{i+1}/5] {q[:60]}...")

        # Get RAG answer and context
        context, sources = retrieve_context(q)

        if context is None:
            context = ""
            answer  = "No relevant information found."
        else:
            try:
                prompt = f"""Answer this question using only the provided context.

Context:
{context}

Question: {q}

Answer:"""
                response = gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                answer = response.text
            except Exception as e:
                print(f"  LLM error: {e}")
                answer = "Error generating answer."

        questions.append(q)
        answers.append(answer)
        contexts.append([context] if context else [""])
        ground_truths.append(gt)

        print(f"  Answer: {answer[:80]}...")

    # ── Build RAGAS dataset ──
    eval_data = {
        "question":     questions,
        "answer":       answers,
        "contexts":     contexts,
        "ground_truth": ground_truths,
    }

    dataset = Dataset.from_dict(eval_data)

    # ── Configure LLM for RAGAS judge ──
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=GEMINI_API_KEY,
        temperature=0
    )

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=GEMINI_API_KEY
    )

    # ── Run RAGAS ──
    print("\nRunning RAGAS metrics...")

    result = evaluate(
        dataset=dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        ],
        llm=llm,
        embeddings=embeddings,
        raise_exceptions=False
    )

    scores = {
        "faithfulness":       round(float(result["faithfulness"]), 4),
        "answer_relevancy":   round(float(result["answer_relevancy"]), 4),
        "context_precision":  round(float(result["context_precision"]), 4),
        "context_recall":     round(float(result["context_recall"]), 4),
    }

    scores["overall"] = round(
        sum(scores.values()) / len(scores), 4
    )

    # Per-question scores
    per_question = []
    df = result.to_pandas()
    for i, row in df.iterrows():
        per_question.append({
            "question":          EVAL_DATASET[i]["question"],
            "faithfulness":      round(float(row.get("faithfulness", 0)), 3),
            "answer_relevancy":  round(float(row.get("answer_relevancy", 0)), 3),
            "context_precision": round(float(row.get("context_precision", 0)), 3),
            "context_recall":    round(float(row.get("context_recall", 0)), 3),
        })

    print("\n" + "=" * 50)
    print("RAGAS RESULTS")
    print("=" * 50)
    for k, v in scores.items():
        bar = "█" * int(v * 20) + "░" * (20 - int(v * 20))
        print(f"{k:<22} {bar} {v:.4f}")

    # Save results
    output = {"scores": scores, "per_question": per_question}
    with open("ragas_results.json", "w") as f:
        json.dump(output, f, indent=2)

    print("\nResults saved to ragas_results.json")
    return output


if __name__ == "__main__":
    run_ragas_evaluation()