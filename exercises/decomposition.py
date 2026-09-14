"""
Sub-step 1.6, Decomposition Strategies (prompt chaining vs dynamic decomposition)
Run: python decomposition.py
"""
from openai import OpenAI

MODEL = "gpt-5.6"  # verify against platform.openai.com/docs/models before recording
client = OpenAI()


# --- Strategy 1: Prompt Chaining (fixed sequential pipeline) ---
# Each step produces output that feeds the next. Best for predictable, multi-aspect
# workflows (code review, support triage) where the steps are known in advance.

def prompt_chaining_review(support_case: str):
    """Fixed pipeline: classify -> check policy -> draft response. No branching."""
    print("\n--- Prompt Chaining ---")

    r1 = client.chat.completions.create(
        model=MODEL, max_tokens=128, reasoning_effort="none",
        messages=[{"role": "user", "content":
            f"Classify this support case as: refund / exchange / billing / other.\nCase: {support_case}"}],
    )
    classification = r1.choices[0].message.content.strip()
    print(f"  Step 1, Classification: {classification}")

    r2 = client.chat.completions.create(
        model=MODEL, max_tokens=128, reasoning_effort="none",
        messages=[{"role": "user", "content":
            f"Classification: {classification}\nCase: {support_case}\n\n"
            "What policy applies? State the rule in one sentence."}],
    )
    policy = r2.choices[0].message.content.strip()
    print(f"  Step 2, Policy: {policy}")

    r3 = client.chat.completions.create(
        model=MODEL, max_tokens=200, reasoning_effort="none",
        messages=[{"role": "user", "content":
            f"Classification: {classification}\nPolicy: {policy}\nCase: {support_case}\n\n"
            "Draft a brief customer-facing response."}],
    )
    print(f"  Step 3, Draft: {r3.choices[0].message.content.strip()}")


# --- Strategy 2: Dynamic Adaptive Decomposition ---
# The coordinator decides next steps based on what it discovers. Best for open-ended
# investigation tasks where findings determine the path, steps aren't known upfront.

def dynamic_investigation(support_case: str):
    """Adaptive pipeline: the agent generates its own investigation plan."""
    print("\n--- Dynamic Decomposition ---")

    r1 = client.chat.completions.create(
        model=MODEL, max_tokens=256, reasoning_effort="none",
        messages=[{"role": "user", "content":
            f"Case: {support_case}\n\n"
            "Generate an investigation plan as a JSON list of steps. "
            "Each step: {'step': int, 'action': str, 'reason': str}. "
            "Only include steps actually needed for this specific case."}],
    )
    raw_plan = r1.choices[0].message.content
    print(f"  Generated plan:\n{raw_plan}\n")
    print("  (In production: iterate plan steps, spawn subagents per step, generate new steps on discovery)")


if __name__ == "__main__":
    case = "Hi, I'm Jane Doe. I want a refund for ORD-555. The headphones stopped working after one day."
    prompt_chaining_review(case)
    dynamic_investigation(case)
