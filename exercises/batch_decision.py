"""
Sub-step 4.5, Batch Processing
Run: python batch_decision.py

Decision guide: OpenAI's Batch API vs synchronous client.chat.completions.create

SYNCHRONOUS (client.chat.completions.create):
  Use when: developers or users are waiting for the result
  Examples: pre-merge CI review (blocks the merge), real-time customer-facing
  agent responses, interactive sessions

BATCH API (client.batches.create):
  Use when: the result is needed eventually, not immediately
  Properties: roughly 50% cost savings, up to 24-hour completion window,
  no guaranteed latency
  Examples: nightly extraction of the day's support tickets, weekly technical
  debt analysis, overnight test generation for a large codebase

CRITICAL LIMITATIONS:
  - Requests go in as a JSONL file, each line needs a unique custom_id
  - No guaranteed processing time, plan for the full 24 hours
  - Note: verify current exact limitations against OpenAI's batch docs before
    relying on this for a real deadline, API details can shift over time

SLA CALCULATION EXAMPLE:
  Goal: guarantee results within 30 hours
  Batch window: up to 24 hours
  Resubmission window needed: 30 - 24 = 6 hours
  Therefore: submit batches at most every 6 hours
  (if a batch takes the full 24h, there's still 6h left to resubmit failures)
"""
import json
from openai import OpenAI

MODEL = "gpt-5.6"  # verify against platform.openai.com/docs/models before recording
client = OpenAI()


def build_batch_requests(messages: list[str]) -> list[dict]:
    """
    Build the JSONL-line-shaped request objects OpenAI's Batch API expects.
    Each custom_id must be unique within the batch, used to match results
    back to requests once the batch completes.
    """
    return [
        {
            "custom_id": f"ticket-{i:04d}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {"model": MODEL, "max_tokens": 512, "messages": [{"role": "user", "content": msg}]},
        }
        for i, msg in enumerate(messages)
    ]


def submit_batch(requests: list[dict]):
    """
    Real submission (not run automatically here, needs a funded API key
    and produces real, billed usage): write requests as JSONL, upload the
    file, then create the batch job.
    """
    with open("batch_input.jsonl", "w") as f:
        for req in requests:
            f.write(json.dumps(req) + "\n")

    uploaded = client.files.create(file=open("batch_input.jsonl", "rb"), purpose="batch")
    batch = client.batches.create(
        input_file_id=uploaded.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )
    print(f"Batch submitted: {batch.id} (status: {batch.status})")
    return batch


def process_batch_results(results) -> dict:
    """Match results back to requests by custom_id; collect failures for targeted resubmission."""
    succeeded, failed = {}, []
    for result in results:
        if result.get("error") is None:
            succeeded[result["custom_id"]] = result["response"]["body"]["choices"][0]["message"]["content"]
        else:
            failed.append(result["custom_id"])  # only resubmit failed items, not the whole batch
    return {"succeeded": succeeded, "failed_ids": failed}


if __name__ == "__main__":
    print("Batch API decision reference loaded.")
    print("Key rule: synchronous for blocking workflows, batch for overnight/latency-tolerant workloads.")

    sample_messages = [
        "Customer Jane Doe wants a refund for ORD-555.",
        "Customer John Smith has a billing dispute on order ORD-888.",
    ]
    requests = build_batch_requests(sample_messages)
    print("\nSample batch request structure:")
    print(json.dumps(requests[0], indent=2))
    print(f"\nTotal requests: {len(requests)}")
    print("Note: this demo builds the request structure only, it does NOT call submit_batch(),")
    print("since that requires a funded API key and produces real, billed usage.")
