"""
Sub-step 5.3, Error Propagation Across Multi-Agent Systems
Run: python subagent_errors.py
"""
import json


def format_subagent_error(tool_name, attempted_query, error_type, partial_results, message) -> dict:
    """
    THE KEY DISTINCTION:
    - access_failure, the service itself failed (timeout, down, auth error).
      the coordinator should consider retrying, or trying an alternative source.
    - valid_empty_result, the service worked fine, it just found nothing.
      retrying the exact same query won't produce new data.

    This structure is designed to prevent three real anti-patterns: silently
    returning an empty list as if it were a normal successful search (hides
    the real failure), reporting "search unavailable" with no context the
    coordinator can act on, and terminating the entire workflow just because
    one subagent had a partial failure.
    """
    return {
        "subagent_status": "error",
        "error_type": error_type,  # "access_failure" | "valid_empty_result"
        "tool": tool_name,
        "attempted_query": attempted_query,
        "partial_results": partial_results or [],
        "partial_results_count": len(partial_results) if partial_results else 0,
        "message": message,
        "coordinator_guidance": (
            "Consider retry with same or modified query; subagent could not reach service"
            if error_type == "access_failure"
            else "No retry needed, query succeeded, zero results; annotate gap and continue"
        ),
    }


def format_synthesis_with_coverage(findings: list, gaps: list) -> dict:
    """
    Structure synthesis output so the coordinator can tell which findings
    are well-supported versus which topics have coverage gaps, so it
    doesn't treat every finding with equal confidence when some came from
    subagents that partially failed.
    """
    return {
        "findings": findings,
        "coverage_annotations": {
            "well_supported": [f["topic"] for f in findings if not f.get("low_confidence")],
            "gaps": gaps,
            "gap_note": "Findings for these topics are absent or low-confidence due to subagent errors",
        },
    }


if __name__ == "__main__":
    err_access = format_subagent_error(
        tool_name="lookup_order", attempted_query={"customer_id": "C-1001", "order_id": "ORD-999"},
        error_type="access_failure", partial_results=None,
        message="Order service timed out after 5 seconds (attempt 1 of 1)",
    )
    print("Access failure:\n", json.dumps(err_access, indent=2))

    err_empty = format_subagent_error(
        tool_name="lookup_order", attempted_query={"customer_id": "C-1001", "order_id": "ORD-999"},
        error_type="valid_empty_result", partial_results=[],
        message="Query succeeded, no orders matching ORD-999 for customer C-1001",
    )
    print("\nValid empty result:\n", json.dumps(err_empty, indent=2))

    synthesis = format_synthesis_with_coverage(
        findings=[
            {"topic": "refund_policy", "content": "Standard 30-day return window applies"},
            {"topic": "order_status", "content": "Order ORD-555 delivered 2026-07-28"},
        ],
        gaps=["shipping_carrier_history", "payment_method_details"],
    )
    print("\nSynthesis with coverage:\n", json.dumps(synthesis, indent=2))
