"""
Sub-step 5.6, Information Provenance in Multi-Source Synthesis
Run: python provenance.py
"""
import json


def make_claim(content, source_url, source_name, relevant_excerpt, publication_date, confidence=1.0) -> dict:
    """
    WHY: when a coordinator combines findings from multiple subagents,
    source attribution has to survive the trip. If it gets lost during
    summarization, conflicting values from different sources can't be
    reconciled, the coordinator would have to just arbitrarily pick one,
    which is exactly the wrong move.
    """
    return {
        "content": content,
        "source": {
            "url": source_url, "name": source_name, "excerpt": relevant_excerpt,
            "publication_date": publication_date,  # ISO 8601; None if unknown, never omit the field
        },
        "confidence": confidence,
    }


def merge_claims_with_conflict_detection(claim_sets: list) -> dict:
    """
    Merge claims from multiple subagents. When two sources disagree about
    the same topic, annotate BOTH, never silently pick one. Let a human
    or the coordinator decide how to reconcile it.
    """
    by_topic = {}
    for claim_set in claim_sets:
        for claim in claim_set:
            topic_key = claim.get("topic_key", claim["content"][:40])
            by_topic.setdefault(topic_key, []).append(claim)

    well_established, contested = [], []
    for topic, claims in by_topic.items():
        if len(claims) == 1:
            well_established.append(claims[0])
        else:
            values = {c["content"] for c in claims}
            if len(values) == 1:
                well_established.append(claims[0])  # multiple sources, same value = strong signal
            else:
                contested.append({
                    "topic": topic, "conflicting_claims": claims,
                    "note": "Sources disagree, do not synthesize arbitrarily; surface conflict to reviewer",
                })

    return {"well_established": well_established, "contested": contested}


if __name__ == "__main__":
    subagent_1_claims = [{**make_claim(
        content="Standard return window is 30 days",
        source_url="https://example-co.com/policy/returns", source_name="Returns Policy Page",
        relevant_excerpt="Items may be returned within 30 days of delivery.",
        publication_date="2026-01-15",
    ), "topic_key": "return_window"}]

    subagent_2_claims = [{**make_claim(
        content="Standard return window is 45 days (updated Feb 2026)",
        source_url="https://example-co.com/policy/returns-v2", source_name="Returns Policy Page (v2)",
        relevant_excerpt="Effective February 2026, the return window is extended to 45 days.",
        publication_date="2026-02-01", confidence=0.95,
    ), "topic_key": "return_window"}]

    merged = merge_claims_with_conflict_detection([subagent_1_claims, subagent_2_claims])
    print("Merged synthesis:")
    print(json.dumps(merged, indent=2))
    print("\nNote: return_window is contested, v2 doc (Feb 2026) supersedes v1 (Jan 2026)")
    print("Correct action: surface both sources with dates; let coordinator/human resolve")
