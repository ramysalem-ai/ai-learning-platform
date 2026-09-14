"""
Sub-step 5.4, Scratchpad Persistence and Crash Recovery
Run: python scratchpad.py

Note: the original workshop mentions Claude Code's /compact command for
long interactive sessions. That's a specific Claude Code feature, the
scratchpad pattern below is the programmatic equivalent for our own
OpenAI-powered agent, and works the same way regardless of which tool
you're using.
"""
import json
from pathlib import Path
from datetime import datetime

SCRATCHPAD_PATH = Path(".sessions/session_scratchpad.json")
MANIFEST_PATH = Path(".sessions/agent_manifest.json")


def save_case_facts(session_id: str, facts: dict):
    """
    WHY: in long-running sessions, an agent can start giving inconsistent
    answers or referencing "typical patterns" instead of the specific
    details it actually discovered earlier. Saving the authoritative facts
    to disk means they can be re-injected at the start of every later
    prompt, protecting them from being lost or blurred over time.
    """
    SCRATCHPAD_PATH.parent.mkdir(exist_ok=True)
    data = {}
    if SCRATCHPAD_PATH.exists():
        data = json.loads(SCRATCHPAD_PATH.read_text())
    data[session_id] = {"updated_at": datetime.now().isoformat(), "facts": facts}
    SCRATCHPAD_PATH.write_text(json.dumps(data, indent=2))
    print(f"[Scratchpad] Saved: {session_id}")


def load_case_facts(session_id: str):
    if not SCRATCHPAD_PATH.exists():
        return None
    return json.loads(SCRATCHPAD_PATH.read_text()).get(session_id, {}).get("facts")


# --- Crash recovery via a state manifest ---
# Each agent records its own completion state to a shared, known location.
# On resume, the coordinator checks this manifest instead of blindly
# re-running everything, completed work stays completed.

def export_agent_state(agent_id: str, status: str, output_summary: str, output_path=None):
    MANIFEST_PATH.parent.mkdir(exist_ok=True)
    manifest = {}
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text())
    manifest[agent_id] = {
        "status": status,  # "completed" | "failed" | "in_progress"
        "completed_at": datetime.now().isoformat(),
        "output_summary": output_summary,
        "output_path": output_path,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
    print(f"[Manifest] Agent {agent_id}: {status}")


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {}
    return json.loads(MANIFEST_PATH.read_text())


def get_incomplete_agents(all_agent_ids: list) -> list:
    """On crash recovery: only re-run agents that never finished. Completed ones' cached results stand."""
    manifest = load_manifest()
    return [aid for aid in all_agent_ids if manifest.get(aid, {}).get("status") != "completed"]


if __name__ == "__main__":
    save_case_facts("session-001", {
        "customer_id": "C-1001", "customer_name": "Jane Doe", "order_id": "ORD-555",
        "order_amount": 89.99, "issue": "Product stopped working after one day", "verified": True,
    })
    print("Loaded:", json.dumps(load_case_facts("session-001"), indent=2))

    export_agent_state("search-agent-1", "completed", "Found 3 relevant policy docs", ".sessions/search_agent_1_output.json")
    export_agent_state("analysis-agent-1", "failed", "Timed out during analysis", None)

    all_agents = ["search-agent-1", "analysis-agent-1", "synthesis-agent-1"]
    incomplete = get_incomplete_agents(all_agents)
    print(f"\nAgents to re-run on resume: {incomplete}")
