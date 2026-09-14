"""
Sub-step 1.3, Explicit Context Passing to Subagents (parallel spawning)
Run: python parallel_subagents.py
"""
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI

MODEL = "gpt-5.6"  # verify against platform.openai.com/docs/models before recording
client = OpenAI()


def spawn_subagent(agent_id: str, role: str, task: str, prior_findings: dict) -> dict:
    """
    Spawn a subagent with explicit context injection.

    Key principle: prior_findings from other agents must be passed directly in the
    prompt, subagents have isolated context and cannot access coordinator history.
    Use structured data formats to separate content from metadata (source, date, confidence).
    """
    context_block = json.dumps(prior_findings, indent=2) if prior_findings else "{}"
    prompt = (
        f"PRIOR FINDINGS FROM COORDINATOR:\n{context_block}\n\n"
        f"YOUR TASK ({role}):\n{task}\n\n"
        "Return a JSON object with keys: 'findings' (string), 'confidence' (low/medium/high), "
        "'source' (what you used to determine this), 'requires_followup' (boolean)."
    )

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=256,
        reasoning_effort="none",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": f"You are agent {agent_id}, role: {role}. Respond with valid JSON only."},
            {"role": "user", "content": prompt},
        ],
    )

    raw = response.choices[0].message.content
    try:
        return {"agent_id": agent_id, "result": json.loads(raw)}
    except json.JSONDecodeError:
        return {"agent_id": agent_id, "result": {"findings": raw, "confidence": "low"}}


def spawn_parallel_subagents(customer_message: str, customer_id: str):
    """
    Spawn multiple subagents in parallel by submitting them concurrently.
    Each receives complete context, no agent depends on another's output here.
    """
    shared_context = {
        "customer_message": customer_message,
        "customer_id": customer_id,
        "timestamp": "2026-08-12T10:00:00Z",  # in production: pass real timestamps
    }

    # These three run concurrently, not sequentially.
    tasks = [
        ("agent-sentiment", "Sentiment Analyst",
         "Analyze the sentiment and urgency of the customer message. Is the customer frustrated?"),
        ("agent-intent", "Intent Classifier",
         "Classify the primary intent: refund_request, exchange_request, billing_dispute, or other."),
        ("agent-policy", "Policy Checker",
         "Based on the message, what policy rules apply? Consider: refund window, amount limits, product condition."),
    ]

    results = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(spawn_subagent, agent_id, role, task, shared_context): agent_id
            for agent_id, role, task in tasks
        }
        for future in as_completed(futures):
            agent_id = futures[future]
            results[agent_id] = future.result()
            print(f"  [Parallel] {agent_id} completed")

    print("\n[Coordinator] All parallel subagents completed. Aggregating results:")
    for agent_id, output in results.items():
        print(f"  {agent_id}: {json.dumps(output['result'], indent=4)}")

    return results


if __name__ == "__main__":
    spawn_parallel_subagents(
        customer_message="I'm Jane Doe. This is ridiculous, I need a refund for ORD-555 immediately.",
        customer_id="C-1001",
    )
