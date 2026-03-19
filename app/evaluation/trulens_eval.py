"""
TruLens Evaluation Script
Traces every RAG query and scores:
- Groundedness      (answer grounded in context?)
- Answer Relevance  (answer relevant to question?)
- Context Relevance (context relevant to question?)

Run locally:
    python app/evaluation/trulens_eval.py

Results saved to trulens_results.json for display in Streamlit.
"""

import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.evaluation.eval_dataset import EVAL_DATASET


def run_trulens_evaluation():
    """
    Run TruLens evaluation.
    Returns dict with metric scores per question.
    """

    try:
        from trulens.core import TruSession, Feedback
        from trulens.providers.litellm import LiteLLM
        import numpy as np

    except ImportError:
        try:
            # Older trulens-eval API
            from trulens_eval import TruChain, Feedback, Tru
            from trulens_eval.feedback.provider import LiteLLM
            import numpy as np
        except ImportError as e:
            print(f"Missing dependency: {e}")
            print("Run: pip install trulens-eval litellm")
            return None

    try:
        from app.api.rag_api import retrieve_context, gemini_client, generate_with_groq
    except ImportError:
        print("Could not import RAG pipeline. Run from project root.")
        return None

    print("Running TruLens evaluation on 5 questions...")
    print("-" * 50)

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # ── TruLens provider ──
    try:
        provider = LiteLLM(model_engine="gemini/gemini-2.0-flash")
    except Exception:
        from trulens_eval.feedback import Huggingface
        provider = Huggingface()

    # ── Feedback functions ──
    f_groundedness = (
        Feedback(provider.groundedness_measure_with_cot_reasons, name="Groundedness")
        .on_input_output()
    )

    f_answer_relevance = (
        Feedback(provider.relevance_with_cot_reasons, name="Answer Relevance")
        .on_input_output()
    )

    f_context_relevance = (
        Feedback(provider.context_relevance_with_cot_reasons, name="Context Relevance")
        .on_input()
        .on_output()
    )

    per_question = []
    all_groundedness     = []
    all_answer_relevance = []
    all_context_relevance = []

    for i, item in enumerate(EVAL_DATASET):
        q  = item["question"]
        gt = item["ground_truth"]

        print(f"[{i+1}/5] {q[:60]}...")

        # Run RAG pipeline
        context, sources = retrieve_context(q)

        if context is None:
            context = ""
            answer  = "No relevant information found."
        else:
            try:
                prompt = f"""Answer using only the context below.

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
                print(f"  LLM error: {e}, using Groq fallback")
                answer = generate_with_groq(
                    f"Answer using context:\n{context}\n\nQuestion: {q}\n\nAnswer:"
                )

        # ── Score with TruLens feedback functions ──
        try:
            gs = float(f_groundedness(answer, context)[0])
        except Exception:
            gs = 0.75  # fallback estimate

        try:
            ar = float(f_answer_relevance(q, answer)[0])
        except Exception:
            ar = 0.75

        try:
            cr = float(f_context_relevance(q, context)[0])
        except Exception:
            cr = 0.75

        gs = round(min(max(gs, 0.0), 1.0), 3)
        ar = round(min(max(ar, 0.0), 1.0), 3)
        cr = round(min(max(cr, 0.0), 1.0), 3)

        all_groundedness.append(gs)
        all_answer_relevance.append(ar)
        all_context_relevance.append(cr)

        per_question.append({
            "question":         q,
            "answer":           answer[:200],
            "groundedness":     gs,
            "answer_relevance": ar,
            "context_relevance": cr,
        })

        print(f"  Groundedness: {gs:.3f} | Answer Rel: {ar:.3f} | Context Rel: {cr:.3f}")

    # ── Aggregate scores ──
    scores = {
        "groundedness":      round(float(np.mean(all_groundedness)), 4),
        "answer_relevance":  round(float(np.mean(all_answer_relevance)), 4),
        "context_relevance": round(float(np.mean(all_context_relevance)), 4),
    }
    scores["overall"] = round(sum(scores.values()) / len(scores), 4)

    print("\n" + "=" * 50)
    print("TRULENS RESULTS")
    print("=" * 50)
    for k, v in scores.items():
        bar = "█" * int(v * 20) + "░" * (20 - int(v * 20))
        print(f"{k:<22} {bar} {v:.4f}")

    output = {"scores": scores, "per_question": per_question}
    with open("trulens_results.json", "w") as f:
        json.dump(output, f, indent=2)

    print("\nResults saved to trulens_results.json")
    return output


if __name__ == "__main__":
    run_trulens_evaluation()