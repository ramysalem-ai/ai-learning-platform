"""
Sub-steps 3.1 & 3.3, Project Instructions Hierarchy + Path-Specific Rules
Run: python project_config_demo.py

Note: the original workshop used Claude Code's CLAUDE.md / .claude/rules/
system, which is a specific Anthropic product feature. This version teaches
the same underlying ideas with plain files any project can use, regardless
of which AI tool (or none at all) is reading them.
"""
import fnmatch
from pathlib import Path

# --- 3.1: a layered project-instructions file, cascading like CLAUDE.md did ---
# Shared conventions (checked into git, everyone gets them) live in one file.
# Personal preferences (not shared) would live in a separate, un-committed file.

PROJECT_CONVENTIONS = """
# Project Conventions (shared with the whole team via git)

- All Python files use type hints for function signatures
- Functions that call the OpenAI API must handle both "tool_calls" and "stop" finish reasons
- Never hardcode API keys, always use environment variables
- Tool dispatcher functions must check the prerequisite gate before executing order/refund tools

## API Conventions
- Always set max_tokens, never omit it
- Agentic loops must check finish_reason before inspecting response content
- Tool schemas must include a "required" list, never omit it, even for single-field tools

## Error Handling
- Tool errors must return isError, errorCategory, and isRetryable fields
- Transient errors may be retried up to 2 times
- Business errors must never be retried, escalate instead
"""


def load_project_instructions() -> str:
    """
    In a real project, this might read PROJECT.md from disk and prepend it
    to every system prompt your agent uses, the same idea as CLAUDE.md
    loading automatically, just done explicitly in your own code.
    """
    return PROJECT_CONVENTIONS.strip()


# --- 3.3: rules that apply based on which file is being touched, not which folder ---
# The original used YAML frontmatter with glob patterns; here's the same idea
# as a plain Python lookup, still works across any directory structure.

PATH_RULES = [
    {
        "patterns": ["**/test_*.py", "**/*_test.py"],
        "rule": (
            "Testing conventions: mock external API calls (never call OpenAI for real in "
            "tests), name tests to describe the scenario, test both success and error paths, "
            "use deterministic values, never random() in a test."
        ),
    },
    {
        "patterns": ["terraform/**/*", "infra/**/*.tf"],
        "rule": (
            "Infrastructure conventions: never hardcode account IDs or regions, use "
            "variables. Every resource needs a tags block with environment, owner, project."
        ),
    },
]


def rules_for_path(filepath: str) -> list[str]:
    """Return every rule whose glob pattern matches this file, regardless of folder."""
    matches = []
    for entry in PATH_RULES:
        if any(fnmatch.fnmatch(filepath, pat) for pat in entry["patterns"]):
            matches.append(entry["rule"])
    return matches


if __name__ == "__main__":
    print("--- Project instructions (would prefix every system prompt) ---")
    print(load_project_instructions())

    print("\n--- Path-specific rules ---")
    for f in ["tests/test_agent.py", "terraform/modules/vpc/main.tf", "exercises/coordinator.py"]:
        rules = rules_for_path(f)
        if rules:
            print(f"\n{f}:")
            for r in rules:
                print(f"  - {r}")
        else:
            print(f"\n{f}: no special rules apply")
