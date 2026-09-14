"""
Sub-steps 5.1 & 5.2, Conversation Context Management + Escalation Criteria
Run: python context_manager.py
"""
import json

# --- 5.1: trim tool results before they accumulate in context ---
# A real order lookup might return 40+ fields; we keep only what actually
# affects the resolution, discarding the rest before it ever gets added
# to the conversation.

def trim_order_result(order_result: dict) -> dict:
    return {
        "order_id": order_result.get("order_id"),
        "item": order_result.get("item"),
        "status": order_result.get("status"),
        "amount": order_result.get("amount"),
        "delivery_date": order_result.get("delivery_date"),
        # Discarded: warehouse_id, tracking_carrier_internal_code,
        # payment_processor_ref, fulfillment_center, packaging_type, etc.
    }


def trim_customer_result(customer_result: dict) -> dict:
    return {
        "customer_id": customer_result.get("customer_id"),
        "name": customer_result.get("name"),
        "status": customer_result.get("status"),
        # Discarded: internal_segment, acquisition_channel, lifetime_value_bucket, etc.
    }


TRIMMERS = {"lookup_order": trim_order_result, "get_customer": trim_customer_result}


def trim_tool_result(tool_name: str, result: dict) -> dict:
    trimmer = TRIMMERS.get(tool_name)
    if trimmer and not result.get("isError"):
        return trimmer(result)
    return result


def build_case_facts_block(facts: dict) -> str:
    """
    Render case facts as a clearly labeled block placed at the START of
    the prompt. Models pay more reliable attention to the beginning and
    end of long inputs than the middle, the "lost in the middle" effect
   , so putting the authoritative facts up front, verbatim, protects
    them from getting summarized away or misremembered.
    """
    lines = ["=== CASE FACTS (authoritative, do not summarize) ==="]
    for key, value in facts.items():
        lines.append(f"  {key}: {value}")
    lines.append("=== END CASE FACTS ===")
    return "\n".join(lines)


# --- 5.2: explicit escalation criteria, no sentiment guessing ---

def should_escalate(
    customer_requested_human: bool,
    refund_amount,
    policy_gap_detected: bool,
    attempts_without_progress: int,
    multiple_customer_matches: bool = False,
) -> tuple[bool, str]:
    """
    Every criterion here is explicit and checkable, no sentiment
    analysis, no self-reported confidence scores, no vague "complexity"
    judgment. Those are unreliable proxies for whether a case genuinely
    needs a human.
    """
    if customer_requested_human:  # honor this immediately, no resolution attempt first
        return True, "customer_request"
    if policy_gap_detected:  # don't improvise coverage for a gap, escalate for a policy decision
        return True, "policy_gap"
    if refund_amount is not None and refund_amount > 500:
        return True, "amount_exceeded"
    if attempts_without_progress >= 2:
        return True, "unable_to_progress"
    if multiple_customer_matches:  # ask for more identifiers first; if that fails, escalate
        return True, "ambiguous_identity"
    return False, ""


if __name__ == "__main__":
    verbose_order = {
        "order_id": "ORD-555", "item": "Wireless Headphones", "status": "delivered",
        "amount": 89.99, "delivery_date": "2026-07-28", "warehouse_id": "WH-NE-04",
        "tracking_carrier_internal_code": "UPS-0xA3F9", "payment_processor_ref": "PPR-99182",
        "fulfillment_center": "FC-BOSTON-2", "packaging_type": "poly_bag",
    }
    trimmed = trim_tool_result("lookup_order", verbose_order)
    print("Original fields:", len(verbose_order))
    print("Trimmed fields: ", len({k: v for k, v in trimmed.items() if v is not None}))
    print("Trimmed result: ", json.dumps(trimmed, indent=2))

    facts = {
        "customer_id": "C-1001", "customer_name": "Jane Doe", "order_id": "ORD-555",
        "order_amount": 89.99, "issue": "Product stopped working after one day",
        "customer_verified": True,
    }
    print("\n" + build_case_facts_block(facts))

    print("\n--- Escalation examples ---")
    print(should_escalate(True, None, False, 0))          # customer_request
    print(should_escalate(False, 800, False, 0))           # amount_exceeded
    print(should_escalate(False, None, False, 0, True))    # ambiguous_identity
