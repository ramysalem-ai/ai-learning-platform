"""
Sub-step 2.3, Tool Distribution and tool_choice
Run: python tool_choice_demo.py
"""
from openai import OpenAI

MODEL = "gpt-5.6"  # verify against platform.openai.com/docs/models before recording
client = OpenAI()

# --- Scoped tool sets: each role gets only the tools it actually needs ---

ACCOUNT_AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_customer",
            "description": "Look up a customer record by full name. Example triggers: 'I'm Jane Doe', 'find my account'. Returns customer_id, email, status.",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        },
    },
    # Deliberately excludes lookup_order, process_refund, escalate_to_human.
    # this agent only ever does account lookups, so it can't misuse tools outside its role.
]

REFUND_AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "process_refund",
            "description": "Process a refund. Requires verified customer_id and order_id. Max $500.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "order_id": {"type": "string"},
                    "amount": {"type": "number"},
                },
                "required": ["customer_id", "order_id", "amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_human",
            "description": "Escalate when refund > $500 or policy does not apply.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "reason": {"type": "string"},
                    "summary": {"type": "string"},
                },
                "required": ["customer_id", "reason", "summary"],
            },
        },
    },
]


def demo_tool_choice():
    """
    The three tool_choice modes on OpenAI's API:
    - "auto": the model may call a tool OR just reply with text
    - "required": the model must call some tool (guaranteed tool call)
    - {"type": "function", "function": {"name": "..."}}: must call this exact tool
    """
    # Mode 1: auto, model decides for itself
    r1 = client.chat.completions.create(
        model=MODEL, max_tokens=128, reasoning_effort="none",
        tools=ACCOUNT_AGENT_TOOLS, tool_choice="auto",
        messages=[{"role": "user", "content": "Hello, how are you today?"}],
    )
    print(f"tool_choice=auto, finish_reason: {r1.choices[0].finish_reason}")
    # Likely "stop", the model just replied with text, no tool needed

    # Mode 2: required, model must call at least one tool
    r2 = client.chat.completions.create(
        model=MODEL, max_tokens=128, reasoning_effort="none",
        tools=ACCOUNT_AGENT_TOOLS, tool_choice="required",
        messages=[{"role": "user", "content": "I'm Jane Doe, please look me up."}],
    )
    print(f"tool_choice=required, finish_reason: {r2.choices[0].finish_reason}")
    # Always "tool_calls", the model must call a tool even if it would have preferred text

    # Mode 3: forced, model must call this one exact tool
    # Use this to guarantee a specific step runs first (e.g. identity verification
    # before anything else can happen).
    r3 = client.chat.completions.create(
        model=MODEL, max_tokens=128, reasoning_effort="none",
        tools=ACCOUNT_AGENT_TOOLS,
        tool_choice={"type": "function", "function": {"name": "get_customer"}},
        messages=[{"role": "user", "content": "I'd like to check my refund status. I'm Jane Doe."}],
    )
    print(f"tool_choice=forced get_customer, finish_reason: {r3.choices[0].finish_reason}")
    # Always calls get_customer, even if the model might have preferred to ask a
    # clarifying question first.


if __name__ == "__main__":
    print("--- tool_choice demonstration ---")
    demo_tool_choice()
    print("\nAccount agent tools:", [t["function"]["name"] for t in ACCOUNT_AGENT_TOOLS])
    print("Refund agent tools:", [t["function"]["name"] for t in REFUND_AGENT_TOOLS])
    print("Each agent sees only the tools relevant to its role, the account agent")
    print("physically cannot call process_refund, because it was never given that tool.")
