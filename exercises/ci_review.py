"""
Sub-step 3.6, Running Your Agent Non-Interactively (e.g. in CI/CD)
Run: python ci_review.py <file1.py> [file2.py ...]

Note: the original workshop used Claude Code's `-p` (non-interactive)
flag. A plain Python script is already non-interactive by nature, so
this version gets the same CI-friendly behavior for free, using the
OpenAI API directly, no special flag needed.
"""
import json
import sys
from openai import OpenAI

MODEL = "gpt-5.6"  # verify against platform.openai.com/docs/models before recording
client = OpenAI()


def review_files(filepaths: list[str]) -> dict:
    """
    Reviews the given files for the same specific issues the workshop's
    own conventions call out, not generic style nitpicks.
    """
    contents = {}
    for fp in filepaths:
        try:
            contents[fp] = open(fp).read()
        except FileNotFoundError:
            contents[fp] = "(file not found)"

    review_prompt = (
        "Review these Python files for exactly these issues: missing isRetryable fields "
        "in error returns, agentic loops that don't check finish_reason, and tool "
        "dispatchers missing the prerequisite gate. Report only genuine issues, not style "
        "preferences. Respond as JSON: a list of objects with file, line_hint, severity "
        "(critical/warning), and fix.\n\n"
        + "\n\n".join(f"--- {fp} ---\n{content}" for fp, content in contents.items())
    )

    response = client.chat.completions.create(
        model=MODEL, max_tokens=800, reasoning_effort="none",
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": "Respond with a JSON object with key 'issues' (a list)."},
                   {"role": "user", "content": review_prompt}],
    )
    try:
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        return {"issues": [], "raw": response.choices[0].message.content}


if __name__ == "__main__":
    files = sys.argv[1:]
    if not files:
        print("Usage: python ci_review.py <file1.py> [file2.py ...]")
        sys.exit(1)

    print(f"Reviewing: {', '.join(files)}")
    result = review_files(files)
    output_path = "review_output.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Review complete. Output written to {output_path}")
    print(json.dumps(result, indent=2))
