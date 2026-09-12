import json
import os
import sys
import re

# Project root
PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

sys.path.insert(0, PROJECT_ROOT)

from src.retrieval.search import SemanticSearch


QUERIES_FILE = os.path.join(
    PROJECT_ROOT,
    "data",
    "evaluation",
    "queries.json",
)

CHAT_FILE = os.path.join(
    PROJECT_ROOT,
    "data",
    "raw",
    "chat.json",
)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_words(text):
    """
    Convert text into lowercase word tokens.
    """
    return set(
        re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())
    )


def build_message_lookup(messages):
    return {
        message["id"]: message
        for message in messages
    }


def evaluate():

    queries = load_json(QUERIES_FILE)
    messages = load_json(CHAT_FILE)

    message_lookup = build_message_lookup(messages)

    print("=" * 70)
    print("CHATRECALL EVALUATION")
    print("=" * 70)

    print(f"\nTotal queries: {len(queries)}")

    print(
        f"Decision: {sum(q['type'] == 'decision' for q in queries)}"
    )

    print(
        f"Person:   {sum(q['type'] == 'person' for q in queries)}"
    )

    print(
        f"Time:     {sum(q['type'] == 'time' for q in queries)}"
    )

    print(
        f"Semantic: {sum(q['type'] == 'semantic' for q in queries)}"
    )

    print(
        f"Hard:     {sum(q.get('hard', False) for q in queries)}"
    )

    print("\nLoading retrieval engine...")

    search_engine = SemanticSearch()

    top1_correct = 0
    top3_correct = 0
    top5_correct = 0

    hard_total = 0
    hard_top1_correct = 0

    failures = []

    print("\nRunning evaluation...\n")

    for number, query_data in enumerate(queries, start=1):

        query = query_data["query"]
        expected_id = query_data["answer_message_id"]

        query_type = query_data["type"]
        is_hard = query_data.get("hard", False)

        expected_message = message_lookup.get(expected_id, {})

        expected_text = expected_message.get("text", "")

        results = search_engine.search(
            query,
            top_k=5,
        )

        result_ids = [
            result["id"]
            for result in results
        ]

        top1 = (
            len(result_ids) >= 1
            and result_ids[0] == expected_id
        )

        top3 = expected_id in result_ids[:3]
        top5 = expected_id in result_ids[:5]

        if top1:
            top1_correct += 1

        if top3:
            top3_correct += 1

        if top5:
            top5_correct += 1

        if is_hard:

            hard_total += 1

            if top1:
                hard_top1_correct += 1

        if not top1:

            predicted_id = (
                result_ids[0]
                if result_ids
                else "NONE"
            )

            predicted_text = (
                results[0].get("text", "")
                if results
                else ""
            )

            failures.append({
                "number": number,
                "query": query,
                "type": query_type,
                "hard": is_hard,
                "expected_id": expected_id,
                "expected_text": expected_text,
                "predicted_id": predicted_id,
                "predicted_text": predicted_text,
                "top5_ids": result_ids,
            })

    total = len(queries)

    print("=" * 70)
    print("RESULTS")
    print("=" * 70)

    print(
        f"\nRecall@1: {top1_correct}/{total} "
        f"= {top1_correct / total * 100:.2f}%"
    )

    print(
        f"Recall@3: {top3_correct}/{total} "
        f"= {top3_correct / total * 100:.2f}%"
    )

    print(
        f"Recall@5: {top5_correct}/{total} "
        f"= {top5_correct / total * 100:.2f}%"
    )

    if hard_total:

        print(
            f"\nHard-query Accuracy: "
            f"{hard_top1_correct}/{hard_total} "
            f"= {hard_top1_correct / hard_total * 100:.2f}%"
        )

    # ---------------------------------------------------------
    # Failed queries
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("FAILED TOP-1 QUERIES")
    print("=" * 70)

    if not failures:

        print(
            "\nAll queries retrieved the correct message at #1."
        )

    else:

        for failure in failures:

            print("\n" + "-" * 70)

            print(
                f"#{failure['number']} "
                f"[{failure['type']}]"
                f"{' [HARD]' if failure['hard'] else ''}"
            )

            print(
                f"Query:     {failure['query']}"
            )

            print(
                f"Expected:  {failure['expected_id']}"
            )

            print(
                f"           {failure['expected_text']}"
            )

            print(
                f"Predicted: {failure['predicted_id']}"
            )

            print(
                f"           {failure['predicted_text']}"
            )

            print(
                f"Top 5:     {failure['top5_ids']}"
            )

    # ---------------------------------------------------------
    # Zero-word-overlap validation
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("HARD QUERY ZERO-WORD-OVERLAP CHECK")
    print("=" * 70)

    valid_hard = 0

    for query_data in queries:

        if not query_data.get("hard", False):
            continue

        query = query_data["query"]
        expected_id = query_data["answer_message_id"]

        expected_message = message_lookup.get(
            expected_id,
            {}
        )

        answer_text = expected_message.get(
            "text",
            ""
        )

        query_words = normalize_words(query)
        answer_words = normalize_words(answer_text)

        overlap = query_words.intersection(
            answer_words
        )

        if not overlap:

            valid_hard += 1

            print("\nPASS")

        else:

            print(
                f"\nFAIL — overlapping words: "
                f"{sorted(overlap)}"
            )

        print(
            f"Query:  {query}"
        )

        print(
            f"Answer: {answer_text}"
        )

    print(
        f"\nValid zero-word-overlap hard queries: "
        f"{valid_hard}/{hard_total}"
    )

    print("\n" + "=" * 70)
    print("EVALUATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    evaluate()