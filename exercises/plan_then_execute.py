"""
Sub-step 3.4, Plan First vs Just Do It
Run: python plan_then_execute.py

Note: the original workshop used Claude Code's built-in /plan mode. This
version builds the same two-phase pattern directly with the OpenAI API.
propose a plan, let a human approve it, then execute, so it works with
any tool, not just one specific CLI.
"""
from openai import OpenAI

MODEL = "gpt-5.6"  # verify against platform.openai.com/docs/models before recording
client = OpenAI()


def is_simple_change(request: str) -> bool:
    """
    A rough rule of thumb for when planning first is worth the extra step.
    Simple, well-scoped, single-file changes: just do it.
    Multi-file, architectural, or ambiguous changes: plan first.
    """
    simple_signals = ["add a docstring", "fix typo", "rename variable", "add comment"]
    return any(signal in request.lower() for signal in simple_signals)


def direct_execution(request: str):
    """For clear, small, well-scoped changes, no planning overhead needed."""
    print(f"[Direct] Executing immediately: {request}")
    response = client.chat.completions.create(
        model=MODEL, max_tokens=256, reasoning_effort="none",
        messages=[{"role": "user", "content": f"Make this change and show the result: {request}"}],
    )
    print(response.choices[0].message.content)


def plan_mode(request: str):
    """
    For architectural or multi-file decisions, propose an approach FIRST,
    without making any changes, so a human can redirect before anything happens.
    """
    print(f"[Plan] Proposing an approach before touching anything: {request}")
    response = client.chat.completions.create(
        model=MODEL, max_tokens=400, reasoning_effort="none",
        messages=[{"role": "system", "content":
            "Propose a step-by-step approach to this request. Do NOT write final code, "
            "just the plan, so a human can review it before anything is built."},
            {"role": "user", "content": request}],
    )
    print(response.choices[0].message.content)
    print("\n[Waiting for human approval before executing, nothing has been built yet.]")


def handle_request(request: str):
    if is_simple_change(request):
        direct_execution(request)
    else:
        plan_mode(request)


if __name__ == "__main__":
    print("=== Exercise A: simple, well-scoped change ===")
    handle_request("Add a docstring to the dispatch_tool function describing what it does.")

    print("\n=== Exercise B: architectural decision ===")
    handle_request(
        "I want to add support for a new 'exchange_item' workflow that lets customers "
        "swap a delivered item for a different size or color. This needs new tools, new "
        "prerequisite logic, and possibly new tests. How should we approach this?"
    )
