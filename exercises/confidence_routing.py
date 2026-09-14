"""
Sub-step 5.5, Human Review Workflows and Confidence Calibration
Run: python confidence_routing.py
"""
import json
from openai import OpenAI

MODEL = "gpt-5.6"  # verify against platform.openai.com/docs/models before recording
client = OpenAI()

EXTRACTION_WITH_CONFIDENCE = {
    "type": "function",
    "function": {
        "name": "extract_with_confidence",
        "description": "Extract structured data and report per-field confidence.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {"type": ["string", "null"]},
                "order_id": {"type": ["string", "null"]},
                "issue_type": {"type": "string", "enum": ["refund", "exchange", "billing_dispute", "account_issue", "other"]},
                "requested_amount": {"type": ["number", "null"]},
                "confidence": {
                    "type": "object",
                    "description": "Per-field confidence: 0.0-1.0. Low = source was ambiguous or contradictory.",
                    "properties": {
                        "customer_name": {"type": "number"},
                        "order_id": {"type": "number"},
                        "issue_type": {"type": "number"},
                        "requested_amount": {"type": "number"},
                    },
                    "required": ["customer_name", "order_id", "issue_type", "requested_amount"],
                },
            },
            "required": ["issue_type", "confidence"],
        },
    },
}

# Illustrative thresholds, in production, calibrate these against a labeled validation set.
CONFIDENCE_THRESHOLDS = {
    "auto_approve": 0.90,  # every field above this -> no human review needed
    "human_review": 0.70,  # any field below this -> route to human review
    # between 0.70 and 0.90 -> optional spot-check via stratified sampling
}


def route_extraction(extraction: dict) -> str:
    """
    Route based on the WEAKEST field, not the average.
    A 97% overall accuracy rate can hide a 40% error rate on one specific
    field or document type, field-level routing catches that where an
    aggregate score would miss it entirely.
    """
    confidence = extraction.get("confidence", {})
    min_confidence = min(confidence.values()) if confidence else 0.0
    if min_confidence >= CONFIDENCE_THRESHOLDS["auto_approve"]:
        return "auto_approve"
    elif min_confidence < CONFIDENCE_THRESHOLDS["human_review"]:
        return "human_review"
    return "stratified_sample"  # included in ongoing accuracy measurement


def extract_and_route(message: str) -> dict:
    response = client.chat.completions.create(
        model=MODEL, max_tokens=512, reasoning_effort="none",
        tools=[EXTRACTION_WITH_CONFIDENCE],
        tool_choice={"type": "function", "function": {"name": "extract_with_confidence"}},
        messages=[{"role": "user", "content": message}],
    )
    tool_call = response.choices[0].message.tool_calls[0] if response.choices[0].message.tool_calls else None
    if not tool_call:
        return {"error": "No extraction"}
    extraction = json.loads(tool_call.function.arguments)
    route = route_extraction(extraction)
    return {**extraction, "routing_decision": route}


if __name__ == "__main__":
    test_cases = [
        "Hi I'm Jane Doe, please refund order ORD-555 for $89.99. It broke.",  # high confidence
        "I need help with my order, I think it was something with headphones maybe last week?",  # low confidence
        "Charge me back $200, order ORD-888, it was a duplicate charge.",  # medium confidence
    ]
    for msg in test_cases:
        result = extract_and_route(msg)
        print(f"\nMessage: {msg[:60]}...")
        print(f"Route: {result.get('routing_decision')}")
        print(f"Confidence: {json.dumps(result.get('confidence'), indent=2)}")
