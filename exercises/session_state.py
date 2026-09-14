"""
Sub-step 1.7, Session Resumption and Forking
Run: python session_state.py
(Simplified as saved conversation state, not the Claude Code CLI's --resume/--fork
flags, since this workshop runs on the OpenAI API directly.)
"""
import json
from pathlib import Path
from openai import OpenAI

MODEL = "gpt-5.6"  # verify against platform.openai.com/docs/models before recording
client = OpenAI()
STATE_FILE = Path(".sessions/session_state.json")


def save_session_state(session_id: str, findings: dict):
    """Persist session findings for resumption or forking."""
    STATE_FILE.parent.mkdir(exist_ok=True)
    data = {}
    if STATE_FILE.exists():
        data = json.loads(STATE_FILE.read_text())
    data[session_id] = findings
    STATE_FILE.write_text(json.dumps(data, indent=2))
    print(f"[Session] State saved for {session_id}")


def load_session_state(session_id: str):
    """Load prior session findings for context injection on resume."""
    if not STATE_FILE.exists():
        return None
    return json.loads(STATE_FILE.read_text()).get(session_id)


def resume_with_injected_summary(session_id: str, new_user_message: str):
    """
    When resuming: inject prior findings as context rather than replaying tool calls.
    Use this when prior tool results may be stale, fresh calls get current data,
    but prior analysis findings are still valid.
    """
    prior = load_session_state(session_id)
    if prior:
        injected_context = (
            f"PRIOR SESSION FINDINGS (session {session_id}):\n"
            f"{json.dumps(prior, indent=2)}\n\n"
            f"NEW REQUEST: {new_user_message}"
        )
    else:
        injected_context = new_user_message

    response = client.chat.completions.create(
        model=MODEL, max_tokens=256, reasoning_effort="none",
        messages=[{"role": "user", "content": injected_context}],
    )
    print(f"[Resumed Agent] {response.choices[0].message.content}")


def fork_session(base_session_id: str, approach_a: str, approach_b: str):
    """
    Fork: both branches start from the same prior findings but take different
    approaches. Use to compare two strategies (e.g. conservative vs aggressive refund
    policy) without disturbing the original session.
    """
    base_findings = load_session_state(base_session_id) or {}
    context = f"BASE FINDINGS:\n{json.dumps(base_findings, indent=2)}\n\n"

    print("\n[Fork A]")
    r_a = client.chat.completions.create(
        model=MODEL, max_tokens=128, reasoning_effort="none",
        messages=[{"role": "user", "content": context + f"Approach A: {approach_a}"}],
    )
    print(f"  {r_a.choices[0].message.content}")

    print("\n[Fork B]")
    r_b = client.chat.completions.create(
        model=MODEL, max_tokens=128, reasoning_effort="none",
        messages=[{"role": "user", "content": context + f"Approach B: {approach_b}"}],
    )
    print(f"  {r_b.choices[0].message.content}")


if __name__ == "__main__":
    save_session_state("session-001", {
        "customer_id": "C-1001", "customer_name": "Jane Doe", "order_id": "ORD-555",
        "issue": "Product stopped working", "verified": True,
    })

    resume_with_injected_summary(
        "session-001",
        "The customer followed up, they would now like an exchange instead of a refund.",
    )

    fork_session(
        "session-001",
        approach_a="Approve refund immediately given verified account and valid order.",
        approach_b="Offer exchange first; only refund if customer declines the exchange.",
    )
