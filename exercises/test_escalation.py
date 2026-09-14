"""
Sub-step 3.5, Concrete Examples and Test-Driven Iteration
Run: python test_escalation.py

This tests a should_escalate() function against concrete input/output
examples, the same "write the examples first" pattern the original
workshop taught, just framed as plain pytest-style tests rather than a
Claude Code-specific workflow. Works with any AI assistant, or none.
"""


def should_escalate(customer_requested_human: bool, refund_amount, policy_gap_detected: bool,
                     attempts_without_progress: int) -> tuple[bool, str]:
    """
    Decide whether a case needs a human. Written to satisfy the concrete
    examples below, not from a vague instruction like "be more conservative".
    """
    if customer_requested_human:
        return True, "customer_request"
    if refund_amount is not None and refund_amount > 500:
        return True, "amount_exceeded"
    if policy_gap_detected:
        return True, "policy_gap"
    if attempts_without_progress >= 2:
        return True, "unable_to_progress"
    return False, ""


def test_no_escalation_for_frustrated_customer():
    # Frustration alone is NOT an escalation trigger
    result, reason = should_escalate(False, None, False, 0)
    assert result is False
    assert reason == ""


def test_escalate_on_explicit_human_request():
    result, reason = should_escalate(True, 10, False, 0)
    assert result is True
    assert reason == "customer_request"


def test_no_escalation_under_limit():
    result, reason = should_escalate(False, 450, False, 0)
    assert result is False
    assert reason == ""


def test_escalate_over_amount_limit():
    result, reason = should_escalate(False, 550, False, 0)
    assert result is True
    assert reason == "amount_exceeded"


def test_escalate_on_policy_gap():
    result, reason = should_escalate(False, 10, True, 0)
    assert result is True
    assert reason == "policy_gap"


def test_escalate_after_two_failed_attempts():
    result, reason = should_escalate(False, None, False, 2)
    assert result is True
    assert reason == "unable_to_progress"


if __name__ == "__main__":
    tests = [
        test_no_escalation_for_frustrated_customer,
        test_escalate_on_explicit_human_request,
        test_no_escalation_under_limit,
        test_escalate_over_amount_limit,
        test_escalate_on_policy_gap,
        test_escalate_after_two_failed_attempts,
    ]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"  PASS: {t.__name__}")
    print(f"\n{passed}/{len(tests)} tests passed.")
