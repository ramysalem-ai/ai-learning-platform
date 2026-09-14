"""
Sub-steps 4.2, 4.3, 4.4, Few-Shot Prompting + Structured Output + Validation/Retry
Run: python extractor.py
"""
import json
from openai import OpenAI

MODEL = "gpt-5.6"  # verify against platform.openai.com/docs/models before recording
client = OpenAI()

# --- 4.2: few-shot examples that show the REASONING, not just the final answer ---
FEW_SHOT_EXAMPLES = """
Here are examples of correctly classified support messages:

Message: "Hi, I'm Sarah Connor. I need a full refund for order ORD-12345. The headphones stopped working after one day."
Classification: issue_type=refund, urgency=medium, sentiment=negative
Reasoning: Clear refund request, product defect, standard case, medium urgency.

Message: "THIS IS UNACCEPTABLE. I've been charged twice for the same order ORD-99001. I'm disputing this with my credit card company."
Classification: issue_type=billing_dispute, urgency=high, sentiment=very_negative
Reasoning: Double charge + credit card dispute threat = high urgency. Billing dispute, not refund request.

Message: "Could I swap my blue jacket for a red one? Order ORD-44200."
Classification: issue_type=exchange, urgency=low, sentiment=positive
Reasoning: Polite exchange request, no problem with the order, low urgency, positive tone.

Message: "I'm frustrated that my order is late but I understand these things happen."
Classification: issue_type=other, issue_type_detail="late delivery inquiry", urgency=low, sentiment=negative
Reasoning: Negative sentiment but low urgency, customer is expressing frustration, not demanding action.
IMPORTANT: Do NOT classify frustrated-but-not-demanding as high urgency. Sentiment alone does not determine urgency.

Message: "I want to talk to a manager right now."
Classification: issue_type=other, issue_type_detail="escalation request", urgency=high, sentiment=very_negative
Reasoning: Explicit human escalation request, always high urgency regardless of the underlying issue.
"""

# --- 4.3: structured output via a forced tool call, with nullable fields to prevent hallucination ---
EXTRACTION_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_support_request",
        "description": "Extract structured information from a customer support message.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {"type": ["string", "null"], "description": "Customer's full name if stated, otherwise null. Never invent a name."},
                "order_id": {"type": ["string", "null"], "description": "Order ID if mentioned (format: ORD-XXXXX), otherwise null."},
                "issue_type": {"type": "string", "enum": ["refund", "exchange", "billing_dispute", "account_issue", "other"],
                                "description": "Primary issue category. Use 'other' when none of the specific types fit, do not force-fit."},
                "issue_type_detail": {"type": ["string", "null"], "description": "Required when issue_type is 'other': describe the issue in one sentence. Otherwise null."},
                "requested_amount": {"type": ["number", "null"], "description": "Dollar amount requested, if explicitly stated. Do not infer amounts not stated. Otherwise null."},
                "urgency": {"type": "string", "enum": ["low", "medium", "high"],
                            "description": "Urgency: high = explicit human escalation request OR mentions legal action. NOT just frustrated tone."},
                "sentiment": {"type": "string", "enum": ["positive", "neutral", "negative", "very_negative"]},
                "detected_pattern": {"type": ["string", "null"], "description": "If this message matches a known pattern (e.g. 'credit_card_dispute', 'late_delivery'), name it. Otherwise null."},
            },
            "required": ["issue_type", "urgency", "sentiment"],
        },
    },
}


# --- 4.4: semantic validation, catches wrong VALUES, not just wrong TYPES ---
def validate_extraction(data: dict) -> list:
    """Schema enforcement catches syntax errors. This catches semantic errors."""
    errors = []
    if data.get("issue_type") == "other" and not data.get("issue_type_detail"):
        errors.append(
            "issue_type is 'other' but issue_type_detail is null. "
            "When issue_type='other', you MUST describe the issue in issue_type_detail."
        )
    if data.get("requested_amount") is not None and data["requested_amount"] < 0:
        errors.append("requested_amount cannot be negative.")
    if data.get("urgency") == "high" and data.get("sentiment") == "negative" and not data.get("detected_pattern"):
        errors.append(
            "urgency='high' requires an explicit escalation trigger (human request or legal "
            "threat), not just negative sentiment. Re-evaluate urgency, it is likely 'medium'."
        )
    return errors


def extract_with_retry(message: str, max_retries: int = 2) -> dict:
    """
    Key insight: retries only help when the error is CORRECTABLE (a misclassification).
    Retries are useless when the information simply isn't in the source message.
    no amount of retrying invents a name that was never stated.
    """
    prompt = f"{FEW_SHOT_EXAMPLES}\n\nNow extract from this message:\n{message}"
    messages = [{"role": "user", "content": prompt}]

    for attempt in range(max_retries + 1):
        response = client.chat.completions.create(
            model=MODEL, max_tokens=512, reasoning_effort="none",
            tools=[EXTRACTION_TOOL],
            tool_choice={"type": "function", "function": {"name": "extract_support_request"}},
            messages=messages,
        )
        choice = response.choices[0]
        tool_call = choice.message.tool_calls[0] if choice.message.tool_calls else None
        if not tool_call:
            return {"error": "No extraction returned"}

        extracted = json.loads(tool_call.function.arguments)
        errors = validate_extraction(extracted)
        if not errors:
            return extracted

        if attempt < max_retries:
            print(f"  [Retry {attempt + 1}] Semantic errors: {errors}")
            messages.append(choice.message.model_dump())
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps({
                    "validation_errors": errors,
                    "your_extraction": extracted,
                    "instruction": "Correct ONLY the fields mentioned in validation_errors. Do not change other fields.",
                }),
            })

    return extracted  # best effort after retries


if __name__ == "__main__":
    test_messages = [
        "Hi I'm Jane Doe, I'd like a refund on order ORD-555. The headphones broke.",
        "I was charged $200 twice!! Order ORD-888. Fix this NOW or I'm going to my bank.",
        "Just wondering if you sell gift cards or something like that.",
        "This is ridiculous!",  # frustrated but no specific request, tests urgency logic
    ]
    for msg in test_messages:
        print(f"\nMessage: {msg}")
        result = extract_with_retry(msg)
        print(f"Extracted: {json.dumps(result, indent=2)}")
