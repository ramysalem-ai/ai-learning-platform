"""
Sub-step 4.6, Multi-Instance and Multi-Pass Review Architectures
Run: python multi_pass_review.py
"""
import json
from openai import OpenAI

MODEL = "gpt-5.6"  # verify against platform.openai.com/docs/models before recording
client = OpenAI()

LOCAL_REVIEW_SYSTEM = """You are a code reviewer analyzing a SINGLE FILE in isolation.
Focus only on issues local to this file:
- Missing error fields (isRetryable, errorCategory)
- Incorrect finish_reason handling in agentic loops
- Prerequisite gate missing before tool execution
- Hardcoded values that should be configurable
For each issue: file, line (estimate), severity (CRITICAL/WARNING/INFO), description.
Output as a JSON object with key "issues" (a list). Empty list if no issues."""

INTEGRATION_REVIEW_SYSTEM = """You are a code reviewer analyzing CROSS-FILE integration issues.
You have been given local review findings from individual files.
Focus only on integration-level issues that span multiple files:
- Tool referenced in agent.py that has no corresponding backend function
- Error category defined in tools_v2.py but not handled in the dispatcher
- Session state saved in one file but never loaded by another
- Inconsistent field names between files (e.g. "customer_id" vs "customerId")
Do NOT re-flag local issues already reported. Only cross-file integration gaps.
Output as a JSON object with key "issues" (a list), each with a "files_involved" field."""


def local_review_pass(filename: str, code: str) -> list:
    """First pass: review one file in isolation."""
    response = client.chat.completions.create(
        model=MODEL, max_tokens=512, reasoning_effort="none",
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": LOCAL_REVIEW_SYSTEM},
                   {"role": "user", "content": f"File: {filename}\n\n```python\n{code}\n```"}],
    )
    raw = response.choices[0].message.content
    try:
        return json.loads(raw).get("issues", [])
    except json.JSONDecodeError:
        return [{"file": filename, "raw_output": raw, "parse_error": True}]


def integration_pass(local_findings: dict) -> list:
    """
    Second pass: cross-file integration review, in a SEPARATE fresh call.
    not a continuation of the local review calls. Isolation prevents the
    reviewer from carrying assumptions from the generation or local phase.
    """
    summary = json.dumps(local_findings, indent=2)
    response = client.chat.completions.create(
        model=MODEL, max_tokens=512, reasoning_effort="none",
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": INTEGRATION_REVIEW_SYSTEM},
                   {"role": "user", "content": f"Local review findings:\n{summary}\n\nIdentify cross-file integration issues."}],
    )
    raw = response.choices[0].message.content
    try:
        return json.loads(raw).get("issues", [])
    except json.JSONDecodeError:
        return [{"integration_review": raw, "parse_error": True}]


def multi_pass_review(files: dict) -> dict:
    """
    1. Local pass, one call per file, focused scope
    2. Integration pass, separate fresh call, cross-file only
    Avoids attention dilution (reviewing 5 files at once degrades precision
    on each) and ensures the integration reviewer has no generation context.
    """
    print("Pass 1: Local per-file reviews")
    local_findings = {}
    for filename, code in files.items():
        findings = local_review_pass(filename, code)
        local_findings[filename] = findings
        print(f"  {filename}: {len(findings)} local finding(s)")

    print("\nPass 2: Cross-file integration review (fresh call)")
    integration_findings = integration_pass(local_findings)
    print(f"  Integration issues found: {len(integration_findings)}")

    return {"local_findings": local_findings, "integration_findings": integration_findings}


SAMPLE_FILES = {
    "exercises/agent.py": '''
def dispatch_tool(tool_name, tool_input):
    if tool_name == "get_customer":
        return get_customer(tool_input["name"])
    elif tool_name == "process_refund":
        # Missing prerequisite gate check
        return process_refund(tool_input["customer_id"], tool_input["order_id"], tool_input["amount"])
''',
    "exercises/tools_v2.py": '''
def get_customer_v2(name):
    customers = {"jane doe": {"customer_id": "C-1001", "status": "active"}}
    result = customers.get(name.lower())
    if result:
        return result
    return {"isError": True, "errorCategory": "validation", "isRetryable": False}
''',
}

if __name__ == "__main__":
    results = multi_pass_review(SAMPLE_FILES)
    print("\nFull results:")
    print(json.dumps(results, indent=2))
