"""
Sub-step 4.1, Explicit Criteria to Reduce False Positives
Run: python review_criteria.py
"""
from openai import OpenAI

MODEL = "gpt-5.6"  # verify against platform.openai.com/docs/models before recording
client = OpenAI()

# --- VAGUE criteria (produces false positives) ---
VAGUE_SYSTEM = "You are a code reviewer. Check that comments are accurate and flag any issues. Be conservative and thorough."

# --- EXPLICIT criteria (reduces false positives) ---
EXPLICIT_SYSTEM = """You are a code reviewer. Apply these exact criteria:

REPORT (bugs, security):
- Flag a comment ONLY when the claimed behavior directly contradicts what the code actually does
  Example to flag: comment says "returns None on error" but code raises an exception
- Flag missing isRetryable fields in error return dicts
- Flag agentic loops that check text content instead of finish_reason for termination

DO NOT REPORT (style, patterns):
- Do NOT flag comments that describe intent rather than exact behavior
- Do NOT flag local variable naming conventions even if they differ from PEP8
- Do NOT flag working code patterns just because a different approach exists

Severity definitions:
- CRITICAL: bug that will cause incorrect behavior in production
- WARNING: missing field that degrades reliability but doesn't break the system
- INFO: inconsistency that is unlikely to cause runtime issues

Output ONLY issues that meet the criteria above. If nothing meets the criteria, output an empty list."""

SAMPLE_CODE = '''
def get_customer(name: str) -> dict:
    # Returns None if customer not found
    customers = {"jane doe": {"id": "C-1001"}}
    result = customers.get(name.lower())
    if result:
        return result
    return {"error": "not found"}  # Missing isRetryable field
'''


def compare_criteria(code: str):
    prompt = f"Review this code:\n\n```python\n{code}\n```"

    print("--- VAGUE criteria output ---")
    r_vague = client.chat.completions.create(
        model=MODEL, max_tokens=256, reasoning_effort="none",
        messages=[{"role": "system", "content": VAGUE_SYSTEM}, {"role": "user", "content": prompt}],
    )
    print(r_vague.choices[0].message.content)

    print("\n--- EXPLICIT criteria output ---")
    r_explicit = client.chat.completions.create(
        model=MODEL, max_tokens=256, reasoning_effort="none",
        messages=[{"role": "system", "content": EXPLICIT_SYSTEM}, {"role": "user", "content": prompt}],
    )
    print(r_explicit.choices[0].message.content)


if __name__ == "__main__":
    compare_criteria(SAMPLE_CODE)
