"""
agent.py, the customer support agent, built step by step across the
Agentic Essentials workshop. Every domain adds to this same file.
"""
import json
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI

# STEP:1.1:START
MODEL = "gpt-5.6"  # verify against platform.openai.com/docs/models before recording
client = OpenAI()  # reads OPENAI_API_KEY from your environment

# --- Mock backend functions (stand in for a real database/API) ---

def get_customer(name: str) -> dict:
    customers = {
        "jane doe": {"customer_id": "C-1001", "email": "jane.doe@example.com", "status": "active"},
        "john smith": {"customer_id": "C-1002", "email": "john.smith@example.com", "status": "active"},
    }
    result = customers.get(name.lower())
    if result:
        return result
    return {"error": "Customer not found", "errorCategory": "validation", "isRetryable": False}


def lookup_order(customer_id: str, order_id: str) -> dict:
    orders = {
        ("C-1001", "ORD-555"): {"order_id": "ORD-555", "item": "Wireless Headphones",
                                 "status": "delivered", "amount": 89.99},
    }
    result = orders.get((customer_id, order_id))
    if result:
        return result
    return {"error": "Order not found", "errorCategory": "validation", "isRetryable": False}


def process_refund(customer_id: str, order_id: str, amount: float) -> dict:
    return {"status": "approved", "refund_id": "REF-9001", "amount": amount, "customer_id": customer_id}


def escalate_to_human(customer_id: str, reason: str, summary: str) -> dict:
    return {"escalated": True, "ticket_id": "TKT-7777", "reason": reason}


# --- Tool schema definitions (tells the AI what tools exist and how to call them) ---

TOOLS = [
    {"type": "function", "function": {
        "name": "get_customer",
        "description": "Look up a customer record by full name. Returns customer_id, email, and "
                        "account status. Must be called first before any order or refund operations.",
        "parameters": {"type": "object",
                        "properties": {"name": {"type": "string", "description": "Customer's full name"}},
                        "required": ["name"]}}},
    {"type": "function", "function": {
        "name": "lookup_order",
        "description": "Retrieve order details. Requires a verified customer_id from get_customer.",
        "parameters": {"type": "object",
                        "properties": {"customer_id": {"type": "string"}, "order_id": {"type": "string"}},
                        "required": ["customer_id", "order_id"]}}},
    {"type": "function", "function": {
        "name": "process_refund",
        "description": "Process a refund for a verified customer and order. Max $500, escalate above that.",
        "parameters": {"type": "object",
                        "properties": {"customer_id": {"type": "string"}, "order_id": {"type": "string"},
                                        "amount": {"type": "number"}},
                        "required": ["customer_id", "order_id", "amount"]}}},
    {"type": "function", "function": {
        "name": "escalate_to_human",
        "description": "Escalate to a human agent when the customer asks for one, policy doesn't "
                        "cover the case, or a refund exceeds $500.",
        "parameters": {"type": "object",
                        "properties": {"customer_id": {"type": "string"}, "reason": {"type": "string"},
                                        "summary": {"type": "string"}},
                        "required": ["customer_id", "reason", "summary"]}}},
]

SYSTEM_PROMPT = (
    "You are a customer support agent. Always call get_customer before looking up orders or "
    "processing refunds. Never process a refund over $500 yourself, escalate it instead."
)


def dispatch_tool_stub(name: str, args: dict) -> dict:
    """Temporary stand-in, Sub-step 1.4 replaces this with the real dispatcher."""
    return {"status": "stub", "note": "real dispatch_tool arrives in Sub-step 1.4"}


def run_agent(user_message: str) -> str:
    """The agentic loop: send request -> inspect finish_reason -> act -> repeat until done."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_message}]
    while True:
        response = client.chat.completions.create(
            model=MODEL, messages=messages, tools=TOOLS, reasoning_effort="none",
        )
        choice = response.choices[0]
        if choice.finish_reason == "tool_calls":
            messages.append(choice.message.model_dump())
            for tool_call in choice.message.tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                result = dispatch_tool(name, args)  # upgraded from the Sub-step 1.1 stub, in Sub-step 1.4
                messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": json.dumps(result)})
        elif choice.finish_reason == "stop":
            return choice.message.content
        else:
            return f"Unhandled finish_reason: {choice.finish_reason}"
# STEP:1.1:END

# STEP:1.2:START
def run_subagent(role: str, task_prompt: str) -> str:
    """An isolated subagent with its own fresh context, no access to the coordinator's history."""
    response = client.chat.completions.create(
        model=MODEL, max_tokens=512, reasoning_effort="none",
        messages=[
            {"role": "system", "content": f"You are a specialist agent: {role}. Complete only the task provided."},
            {"role": "user", "content": task_prompt},
        ],
    )
    return response.choices[0].message.content or ""


def coordinator(customer_message: str) -> str:
    """Hub-and-spoke coordinator: analyzes the request, delegates to only the needed
    specialists, then synthesizes their results into one final answer."""
    analysis = client.chat.completions.create(
        model=MODEL, max_tokens=256, reasoning_effort="none",
        messages=[{"role": "system", "content": (
            "You are a support coordinator. List which specialists are needed: "
            "'account_lookup', 'order_lookup', 'refund_processor'. Respond as JSON.")},
            {"role": "user", "content": customer_message}],
    )
    needed = analysis.choices[0].message.content

    account_result = "Not needed for this request."
    if "account_lookup" in needed:
        account_result = run_subagent(
            "Account Lookup Specialist",
            f"Original customer message: {customer_message}\n\nTask: Identify the customer "
            "name and confirm it exists. Treat 'Jane Doe' as valid, ID C-1001.",
        )

    order_result = "Not needed for this request."
    if "order_lookup" in needed:
        order_result = run_subagent(
            "Order Lookup Specialist",
            f"Original customer message: {customer_message}\nAccount result: {account_result}\n\n"
            "Task: Identify the order ID and retrieve its status. Treat ORD-555 as delivered, "
            "$89.99, Wireless Headphones.",
        )

    final = client.chat.completions.create(
        model=MODEL, max_tokens=256, reasoning_effort="none",
        messages=[{"role": "user", "content": (
            f"Customer message: {customer_message}\nAccount result: {account_result}\n"
            f"Order result: {order_result}\n\nSynthesize a helpful, concise response.")}],
    )
    return final.choices[0].message.content
# STEP:1.2:END

# STEP:1.3:START
def spawn_subagent(agent_id: str, role: str, task: str, prior_findings: dict) -> dict:
    """Spawn a subagent with EXPLICIT context, prior_findings must be passed directly,
    since subagents cannot access the coordinator's history automatically."""
    context_block = json.dumps(prior_findings, indent=2) if prior_findings else "{}"
    response = client.chat.completions.create(
        model=MODEL, max_tokens=256, reasoning_effort="none",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": f"You are agent {agent_id}, role: {role}. Respond with valid JSON only."},
            {"role": "user", "content": (
                f"PRIOR FINDINGS FROM COORDINATOR:\n{context_block}\n\nYOUR TASK ({role}):\n{task}\n\n"
                "Return JSON with keys: 'findings' (string), 'confidence' (low/medium/high).")},
        ],
    )
    raw = response.choices[0].message.content
    try:
        return {"agent_id": agent_id, "result": json.loads(raw)}
    except json.JSONDecodeError:
        return {"agent_id": agent_id, "result": {"findings": raw, "confidence": "low"}}


def spawn_parallel_subagents(customer_message: str, customer_id: str) -> dict:
    """Spawn multiple subagents CONCURRENTLY, not one after another."""
    shared_context = {"customer_message": customer_message, "customer_id": customer_id}
    tasks = [
        ("agent-sentiment", "Sentiment Analyst", "Analyze urgency/frustration in the message."),
        ("agent-intent", "Intent Classifier", "Classify: refund_request, exchange_request, or other."),
        ("agent-policy", "Policy Checker", "What policy rules apply based on the message?"),
    ]
    results = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(spawn_subagent, aid, role, task, shared_context): aid
                   for aid, role, task in tasks}
        for future in as_completed(futures):
            results[futures[future]] = future.result()
    return results
# STEP:1.3:END

# STEP:1.4:START
verified_customers = set()  # tracks who's been identity-checked this session


def dispatch_tool(name: str, args: dict) -> dict:
    """The REAL dispatcher, replaces dispatch_tool_stub from Sub-step 1.1.
    Update run_agent() below to call dispatch_tool(name, args) instead of
    dispatch_tool_stub(name, args)."""
    if name == "get_customer":
        result = get_customer(**args)
        if "customer_id" in result:
            verified_customers.add(result["customer_id"])
        return result
    if name in ("lookup_order", "process_refund"):
        if args.get("customer_id") not in verified_customers:
            return {"error": "Customer not verified. Call get_customer first.",
                     "errorCategory": "business", "isRetryable": False}
        if name == "lookup_order":
            return lookup_order(**args)
        return process_refund(**args)
    if name == "escalate_to_human":
        return escalate_to_human(**args)
    return {"error": f"Unknown tool: {name}"}
# STEP:1.4:END

# STEP:1.5:START
def dispatch_tool_with_hooks(name: str, args: dict) -> dict:
    """Same as dispatch_tool, plus a PostToolUse-style hook: block any refund
    over $500 BEFORE the AI ever sees a result, instead of trusting it to
    notice and self-correct."""
    if name == "get_customer":
        result = get_customer(**args)
        if "customer_id" in result:
            verified_customers.add(result["customer_id"])
        return result
    if name in ("lookup_order", "process_refund"):
        if args.get("customer_id") not in verified_customers:
            return {"error": "Customer not verified. Call get_customer first.",
                     "errorCategory": "business", "isRetryable": False}
        if name == "lookup_order":
            return lookup_order(**args)
        if args.get("amount", 0) > 500:  # the new hook
            return {"error": "Refund amount exceeds $500 policy limit",
                     "errorCategory": "business", "isRetryable": False,
                     "action_required": "Use escalate_to_human with reason='amount_exceeded'"}
        return process_refund(**args)
    if name == "escalate_to_human":
        return escalate_to_human(**args)
    return {"error": f"Unknown tool: {name}"}
# STEP:1.5:END

# STEP:1.6:START
def prompt_chaining_review(case: str) -> str:
    """Way one, fixed, predictable steps, always in this order."""
    r1 = client.chat.completions.create(model=MODEL, max_tokens=128, reasoning_effort="none",
        messages=[{"role": "user", "content": f"Classify: refund/exchange/billing/other. Case: {case}"}])
    classification = r1.choices[0].message.content.strip()

    r2 = client.chat.completions.create(model=MODEL, max_tokens=128, reasoning_effort="none",
        messages=[{"role": "user", "content": f"Classification: {classification}. What policy applies?"}])
    policy = r2.choices[0].message.content.strip()

    r3 = client.chat.completions.create(model=MODEL, max_tokens=200, reasoning_effort="none",
        messages=[{"role": "user", "content": f"Classification: {classification}. Policy: {policy}. Draft a reply."}])
    return r3.choices[0].message.content.strip()


def dynamic_investigation(case: str) -> str:
    """Way two, the AI plans its own steps; different cases get different plans."""
    r1 = client.chat.completions.create(model=MODEL, max_tokens=256, reasoning_effort="none",
        messages=[{"role": "user", "content":
            f"Case: {case}. Generate a JSON investigation plan, only steps actually needed."}])
    return r1.choices[0].message.content
# STEP:1.6:END

# STEP:1.7:START
SESSION_FILE = Path(".sessions/session_state.json")


def save_session_state(session_id: str, findings: dict):
    SESSION_FILE.parent.mkdir(exist_ok=True)
    data = json.loads(SESSION_FILE.read_text()) if SESSION_FILE.exists() else {}
    data[session_id] = findings
    SESSION_FILE.write_text(json.dumps(data, indent=2))


def load_session_state(session_id: str):
    if not SESSION_FILE.exists():
        return None
    return json.loads(SESSION_FILE.read_text()).get(session_id)


def resume_with_injected_summary(session_id: str, new_message: str) -> str:
    prior = load_session_state(session_id)
    context = f"PRIOR FINDINGS: {prior}\n\nNEW REQUEST: {new_message}" if prior else new_message
    r = client.chat.completions.create(model=MODEL, max_tokens=256, reasoning_effort="none",
        messages=[{"role": "user", "content": context}])
    return r.choices[0].message.content


def fork_session(base_session_id: str, approach_a: str, approach_b: str) -> tuple:
    base = load_session_state(base_session_id) or {}
    ra = client.chat.completions.create(model=MODEL, max_tokens=128, reasoning_effort="none",
        messages=[{"role": "user", "content": f"BASE: {base}\nApproach A: {approach_a}"}])
    rb = client.chat.completions.create(model=MODEL, max_tokens=128, reasoning_effort="none",
        messages=[{"role": "user", "content": f"BASE: {base}\nApproach B: {approach_b}"}])
    return ra.choices[0].message.content, rb.choices[0].message.content
# STEP:1.7:END

# STEP:2.1:START
# Sub-step 2.1 upgrades TOOLS with example trigger phrases and explicit boundaries.
# This REPLACES the TOOLS list from Sub-step 1.1, same tools, sharper descriptions.
TOOLS_V2 = [
    {"type": "function", "function": {
        "name": "get_customer",
        "description": (
            "Look up a customer's account record by their full name. "
            "Use this when a customer provides their name and you need their account details. "
            "Example triggers: 'I'm Jane Doe', 'look up account for John Smith'. "
            "Returns customer_id (required for all other tools), email, and account status. "
            "Do NOT use this to retrieve order details, use lookup_order for that."),
        "parameters": {"type": "object",
                        "properties": {"name": {"type": "string"}},
                        "required": ["name"]}}},
    {"type": "function", "function": {
        "name": "lookup_order",
        "description": (
            "Retrieve order details using a verified customer_id and order_id. "
            "Example triggers: 'what happened to order ORD-555', 'check my order #12345'. "
            "Do NOT use this to find a customer, use get_customer for that."),
        "parameters": {"type": "object",
                        "properties": {"customer_id": {"type": "string"}, "order_id": {"type": "string"}},
                        "required": ["customer_id", "order_id"]}}},
]
# STEP:2.1:END

# STEP:2.2:START
def get_customer_v2(name: str) -> dict:
    """Same lookup as get_customer, with a structured error instead of a bare message."""
    customers = {"jane doe": {"customer_id": "C-1001", "email": "jane.doe@example.com", "status": "active"}}
    result = customers.get(name.lower())
    if result:
        return result
    return {
        "isError": True,
        "errorCategory": "validation",  # the input was wrong, retrying won't help
        "isRetryable": False,
        "message": f"No customer found with name '{name}'.",
    }
# STEP:2.2:END

# STEP:2.3:START
ACCOUNT_AGENT_TOOLS = [t for t in TOOLS_V2 if t["function"]["name"] == "get_customer"]
# Deliberately scoped: this agent CANNOT call process_refund, because it was never given that tool.
# STEP:2.3:END

# STEP:2.4:START
# Sub-step 2.4 is a config file, not Python code, .mcp.json, see the Guide for its content.
# STEP:2.4:END

# STEP:2.5:START
# Sub-step 2.5 is a terminal-commands skill (grep/find), not code added to this file.
# STEP:2.5:END

# STEP:3.1:START
PROJECT_CONVENTIONS = """
# Project Conventions (shared with the whole team via git)
- Functions calling the OpenAI API must handle both "tool_calls" and "stop" finish reasons
- Never hardcode API keys, always use environment variables
"""


def load_project_instructions() -> str:
    return PROJECT_CONVENTIONS.strip()
# STEP:3.1:END

# STEP:3.2:START
REVIEW_TOOL_TEMPLATE = (
    "Review this tool's code for: missing error fields, unclear descriptions, "
    "and missing 'do NOT use this for...' boundaries. List only genuine issues."
)


def review_tool(code: str) -> str:
    r = client.chat.completions.create(model=MODEL, max_tokens=256, reasoning_effort="none",
        messages=[{"role": "user", "content": f"{REVIEW_TOOL_TEMPLATE}\n\nCode:\n{code}"}])
    return r.choices[0].message.content
# STEP:3.2:END

# STEP:3.3:START
import fnmatch

PATH_RULES = [
    {"patterns": ["**/test_*.py", "**/*_test.py"],
     "rule": "Mock external API calls, never call OpenAI for real in tests."},
]


def rules_for_path(filepath: str) -> list:
    return [r["rule"] for r in PATH_RULES if any(fnmatch.fnmatch(filepath, p) for p in r["patterns"])]
# STEP:3.3:END

# STEP:3.4:START
def plan_mode(request: str) -> str:
    """Propose an approach WITHOUT making changes, for large/ambiguous requests."""
    r = client.chat.completions.create(model=MODEL, max_tokens=400, reasoning_effort="none",
        messages=[{"role": "system", "content":
            "Propose a step-by-step approach. Do NOT write final code, just the plan."},
            {"role": "user", "content": request}])
    return r.choices[0].message.content
# STEP:3.4:END

# STEP:3.5:START
def should_escalate_v1(customer_requested_human, refund_amount, policy_gap_detected,
                        attempts_without_progress) -> tuple:
    """Built to satisfy concrete test examples, see exercises for the full test suite."""
    if customer_requested_human:
        return True, "customer_request"
    if refund_amount is not None and refund_amount > 500:
        return True, "amount_exceeded"
    if policy_gap_detected:
        return True, "policy_gap"
    if attempts_without_progress >= 2:
        return True, "unable_to_progress"
    return False, ""
# STEP:3.5:END

# STEP:3.6:START
def review_files_non_interactive(filepaths: list) -> dict:
    """A plain script is naturally non-interactive, safe to run in CI with no changes needed."""
    contents = {}
    for fp in filepaths:
        try:
            contents[fp] = open(fp).read()
        except FileNotFoundError:
            contents[fp] = "(file not found)"
    prompt = "Review for: missing isRetryable fields, bad finish_reason checks.\n\n" + \
             "\n\n".join(f"--- {fp} ---\n{c}" for fp, c in contents.items())
    r = client.chat.completions.create(model=MODEL, max_tokens=800, reasoning_effort="none",
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": "Respond with JSON: {'issues': [...]}"},
                   {"role": "user", "content": prompt}])
    try:
        return json.loads(r.choices[0].message.content)
    except json.JSONDecodeError:
        return {"issues": []}
# STEP:3.6:END

# STEP:4.1:START
EXPLICIT_REVIEW_SYSTEM = """Apply these exact criteria:
REPORT: Flag a comment ONLY when it directly contradicts what the code does.
DO NOT REPORT: comments describing intent, naming style, working alternatives.
Output ONLY issues meeting the criteria above. Empty list if nothing qualifies."""
# STEP:4.1:END

# STEP:4.2:START
FEW_SHOT_EXAMPLES = """
Message: "I'm frustrated my order is late but I understand these things happen."
Classification: urgency=low, sentiment=negative
Reasoning: Negative sentiment but low urgency, frustration isn't a demand for action.
"""
# STEP:4.2:END

# STEP:4.3:START
EXTRACTION_TOOL = {"type": "function", "function": {
    "name": "extract_support_request",
    "description": "Extract structured information from a support message.",
    "parameters": {"type": "object", "properties": {
        "customer_name": {"type": ["string", "null"], "description": "Never invent a name."},
        "issue_type": {"type": "string", "enum": ["refund", "exchange", "billing_dispute", "other"]},
        "urgency": {"type": "string", "enum": ["low", "medium", "high"]},
    }, "required": ["issue_type", "urgency"]}}}
# STEP:4.3:END

# STEP:4.4:START
def validate_extraction(data: dict) -> list:
    """Catches wrong VALUES that a schema alone can't, semantic checks, not just types."""
    errors = []
    if data.get("urgency") == "high" and not data.get("customer_name"):
        errors.append("urgency='high' needs a concrete trigger, not just tone, re-evaluate.")
    return errors
# STEP:4.4:END

# STEP:4.5:START
def build_batch_requests(messages: list) -> list:
    """Batch API request structure, for overnight/latency-tolerant work, never for live chat."""
    return [{"custom_id": f"ticket-{i:04d}", "method": "POST", "url": "/v1/chat/completions",
              "body": {"model": MODEL, "messages": [{"role": "user", "content": m}]}}
             for i, m in enumerate(messages)]
# STEP:4.5:END

# STEP:4.6:START
def local_review_pass(filename: str, code: str) -> list:
    """Pass 1: review one file in isolation."""
    r = client.chat.completions.create(model=MODEL, max_tokens=512, reasoning_effort="none",
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": "Find local issues. JSON: {'issues': [...]}"},
                   {"role": "user", "content": f"File: {filename}\n{code}"}])
    try:
        return json.loads(r.choices[0].message.content).get("issues", [])
    except json.JSONDecodeError:
        return []
# STEP:4.6:END

# STEP:5.1:START
def trim_order_result(order_result: dict) -> dict:
    """Keep only what matters before adding a tool result to the conversation."""
    return {"order_id": order_result.get("order_id"), "item": order_result.get("item"),
            "status": order_result.get("status"), "amount": order_result.get("amount")}


def build_case_facts_block(facts: dict) -> str:
    lines = ["=== CASE FACTS (authoritative, do not summarize) ==="]
    for k, v in facts.items():
        lines.append(f"  {k}: {v}")
    lines.append("=== END CASE FACTS ===")
    return "\n".join(lines)
# STEP:5.1:END

# STEP:5.2:START
def should_escalate(customer_requested_human, refund_amount, policy_gap_detected,
                     attempts_without_progress, multiple_customer_matches=False) -> tuple:
    """The COMPLETE version, replaces should_escalate_v1 from Sub-step 3.5."""
    if customer_requested_human:
        return True, "customer_request"
    if policy_gap_detected:
        return True, "policy_gap"
    if refund_amount is not None and refund_amount > 500:
        return True, "amount_exceeded"
    if attempts_without_progress >= 2:
        return True, "unable_to_progress"
    if multiple_customer_matches:
        return True, "ambiguous_identity"
    return False, ""
# STEP:5.2:END

# STEP:5.3:START
def format_subagent_error(tool_name, error_type, message) -> dict:
    """Distinguish access_failure (worth retrying) from valid_empty_result (it isn't)."""
    return {
        "subagent_status": "error", "error_type": error_type, "tool": tool_name, "message": message,
        "coordinator_guidance": ("Consider retry" if error_type == "access_failure"
                                  else "No retry needed, query succeeded, zero results"),
    }
# STEP:5.3:END

# STEP:5.4:START
MANIFEST_FILE = Path(".sessions/agent_manifest.json")


def export_agent_state(agent_id: str, status: str):
    MANIFEST_FILE.parent.mkdir(exist_ok=True)
    manifest = json.loads(MANIFEST_FILE.read_text()) if MANIFEST_FILE.exists() else {}
    manifest[agent_id] = {"status": status, "completed_at": datetime.now().isoformat()}
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=2))


def get_incomplete_agents(all_agent_ids: list) -> list:
    manifest = json.loads(MANIFEST_FILE.read_text()) if MANIFEST_FILE.exists() else {}
    return [aid for aid in all_agent_ids if manifest.get(aid, {}).get("status") != "completed"]
# STEP:5.4:END

# STEP:5.5:START
def route_extraction(extraction: dict) -> str:
    """Route by the WEAKEST field's confidence, not the average, an average can hide a real gap."""
    confidence = extraction.get("confidence", {})
    min_confidence = min(confidence.values()) if confidence else 0.0
    if min_confidence >= 0.90:
        return "auto_approve"
    elif min_confidence < 0.70:
        return "human_review"
    return "stratified_sample"
# STEP:5.5:END

# STEP:5.6:START
def merge_claims_with_conflict_detection(claim_sets: list) -> dict:
    """Never silently pick one source when two disagree, flag the conflict instead."""
    by_topic = {}
    for claims in claim_sets:
        for claim in claims:
            by_topic.setdefault(claim.get("topic_key", claim["content"][:40]), []).append(claim)
    well_established, contested = [], []
    for topic, claims in by_topic.items():
        values = {c["content"] for c in claims}
        if len(values) == 1:
            well_established.append(claims[0])
        else:
            contested.append({"topic": topic, "conflicting_claims": claims})
    return {"well_established": well_established, "contested": contested}
# STEP:5.6:END

if __name__ == "__main__":
    # A quick smoke test of the pieces that don't need a live API call.
    print("dispatch_tool_with_hooks (>$500 refund):",
          dispatch_tool_with_hooks("process_refund", {"customer_id": "C-1001", "order_id": "ORD-555", "amount": 600}))
    print("rules_for_path (test file):", rules_for_path("tests/test_agent.py"))
    print("should_escalate (explicit request):", should_escalate(True, None, False, 0))
    print("route_extraction (low confidence):", route_extraction({"confidence": {"a": 0.5, "b": 0.95}}))
    print("\nFor a real conversation, call: run_agent(\"Hi, I'm Jane Doe...\")")
