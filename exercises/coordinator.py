"""
Sub-step 1.2, Coordinator–Subagent Pattern
Run: python coordinator.py
"""
from openai import OpenAI

MODEL = "gpt-5.6"  # verify against platform.openai.com/docs/models before recording
client = OpenAI()  # reads OPENAI_API_KEY from environment


def run_subagent(role: str, task_prompt: str) -> str:
    """
    Runs an isolated subagent with its own fresh context.
    The coordinator passes all required context explicitly in task_prompt.
    subagents have NO access to the coordinator's conversation history.
    """
    print(f"\n  [Subagent: {role}] Starting task...")
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=512,
        reasoning_effort="none",
        messages=[
            {"role": "system", "content": f"You are a specialist agent: {role}. Complete only the task provided."},
            {"role": "user", "content": task_prompt},
        ],
    )
    result = response.choices[0].message.content or ""
    print(f"  [Subagent: {role}] Done. Result snippet: {result[:80]}...")
    return result


def coordinator(customer_message: str):
    """
    Hub-and-spoke coordinator:
    1. Analyzes the request
    2. Dynamically selects which subagents are needed (not always the full pipeline)
    3. Passes complete context to each subagent explicitly
    4. Aggregates results into a unified response
    """
    print(f"\n[Coordinator] Received: {customer_message}")

    # Step 1: Coordinator analyzes the request and decides which specialists are needed
    analysis_response = client.chat.completions.create(
        model=MODEL,
        max_tokens=256,
        reasoning_effort="none",
        messages=[
            {"role": "system", "content": (
                "You are a support coordinator. Analyze the customer message and list which "
                "specialists are needed: 'account_lookup', 'order_lookup', 'refund_processor'. "
                "Respond with a JSON list."
            )},
            {"role": "user", "content": customer_message},
        ],
    )
    raw = analysis_response.choices[0].message.content
    print(f"[Coordinator] Specialists needed: {raw}")

    # Step 2: Route to relevant subagents with full context injected.
    # NOTE: Each subagent gets the original message AND the coordinator's analysis.
    # no automatic inheritance, context must be passed explicitly.
    if "account_lookup" in raw:
        account_result = run_subagent(
            role="Account Lookup Specialist",
            task_prompt=(
                f"Original customer message: {customer_message}\n\n"
                "Task: Identify the customer name from the message and confirm it exists in "
                "our system. For this exercise, treat 'Jane Doe' as a valid customer with ID C-1001."
            ),
        )
    else:
        account_result = "Account lookup not required for this request."

    if "order_lookup" in raw:
        order_result = run_subagent(
            role="Order Lookup Specialist",
            task_prompt=(
                f"Original customer message: {customer_message}\n"
                f"Account lookup result: {account_result}\n\n"
                "Task: Identify the order ID mentioned and retrieve its status. "
                "For this exercise, treat ORD-555 as delivered, $89.99, Wireless Headphones."
            ),
        )
    else:
        order_result = "Order lookup not required for this request."

    # Step 3: Coordinator synthesizes all results, all inter-subagent communication
    # routes through here, never subagent-to-subagent directly.
    synthesis_prompt = (
        f"Customer message: {customer_message}\n"
        f"Account result: {account_result}\n"
        f"Order result: {order_result}\n\n"
        "Synthesize a helpful, concise response to the customer."
    )
    final_response = client.chat.completions.create(
        model=MODEL, max_tokens=256, reasoning_effort="none",
        messages=[{"role": "user", "content": synthesis_prompt}],
    )
    print(f"\n[Coordinator] Final response: {final_response.choices[0].message.content}")


if __name__ == "__main__":
    coordinator("Hi, I'm Jane Doe. I'd like a refund for my order ORD-555.")
