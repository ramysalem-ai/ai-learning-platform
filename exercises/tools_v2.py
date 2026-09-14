"""
Sub-steps 2.1 & 2.2, Effective Tool Interfaces + Structured Error Responses
Run: python tools_v2.py
"""
import json
import random

# --- Sub-step 2.1: tool descriptions with example triggers and explicit boundaries ---
# Compare these to Step 1's descriptions: each one now includes phrases a real customer
# might actually say, AND an explicit "do NOT use this for..." to prevent mix-ups with
# a similar-sounding tool.

TOOLS_V2 = [
    {
        "type": "function",
        "function": {
            "name": "get_customer",
            "description": (
                "Look up a customer's account record by their full name. "
                "Use this when a customer provides their name and you need their account details. "
                "Example triggers: 'I'm Jane Doe', 'look up account for John Smith', 'my name is...'. "
                "Returns: customer_id (required for all other tools), email, and account status. "
                "Do NOT use this to retrieve order details, use lookup_order for that. "
                "Do NOT pass an order number here. Must be called before lookup_order or process_refund."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Customer's full name as they stated it, e.g. 'Jane Doe'"}
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_order",
            "description": (
                "Retrieve details for a specific order using a verified customer_id and order_id. "
                "Use this when a customer references an order number or asks about order status. "
                "Example triggers: 'what happened to order ORD-555', 'check my order #12345', 'where is my package'. "
                "Returns: order status, item description, and amount. "
                "Do NOT use this to find a customer, use get_customer for that. "
                "Requires customer_id from get_customer, never pass a customer name here."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "Verified customer ID returned by get_customer, e.g. 'C-1001'"},
                    "order_id": {"type": "string", "description": "Order ID as stated by the customer, e.g. 'ORD-555'"},
                },
                "required": ["customer_id", "order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "process_refund",
            "description": (
                "Process a refund for a verified customer on a confirmed order. "
                "Use only after both get_customer and lookup_order have succeeded and returned valid data. "
                "Maximum refund: $500, for amounts over $500 use escalate_to_human instead. "
                "Example triggers: 'I want my money back', 'please refund me', 'issue a refund for...'. "
                "Returns: refund approval status and refund ID."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "order_id": {"type": "string"},
                    "amount": {"type": "number", "description": "Refund amount in USD. Must not exceed 500."},
                },
                "required": ["customer_id", "order_id", "amount"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_human",
            "description": (
                "Transfer this case to a human support agent. "
                "Use when: (1) customer explicitly asks for a human, "
                "(2) refund amount exceeds $500, "
                "(3) policy does not cover the customer's situation, "
                "(4) you cannot make meaningful progress after two attempts. "
                "Do NOT use just because a case is complex, always attempt resolution first. "
                "Do NOT use because you are uncertain, uncertainty alone is not an escalation trigger. "
                "Returns: escalation ticket ID."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "reason": {"type": "string", "description": "Exactly one of: customer_request, policy_gap, amount_exceeded, unable_to_progress"},
                    "summary": {"type": "string", "description": "Full case summary: customer name, issue, what was tried, what is needed next"},
                },
                "required": ["customer_id", "reason", "summary"],
            },
        },
    },
]


# --- Sub-step 2.2: structured errors instead of generic {"error": "..."} messages ---
# Each error tells the AI exactly what kind of problem it is, and whether trying again
# would help, so the AI can make a smart decision instead of guessing.

def get_customer_v2(name: str) -> dict:
    customers = {
        "jane doe": {"customer_id": "C-1001", "email": "jane.doe@example.com", "status": "active"},
        "john smith": {"customer_id": "C-1002", "email": "john.smith@example.com", "status": "active"},
    }
    result = customers.get(name.lower())
    if result:
        return result
    return {
        "isError": True,
        "errorCategory": "validation",  # the input was wrong, asking again won't help
        "isRetryable": False,
        "message": f"No customer found with name '{name}'. Ask the customer to confirm their full name.",
    }


def lookup_order_v2(customer_id: str, order_id: str) -> dict:
    orders = {
        ("C-1001", "ORD-555"): {"order_id": "ORD-555", "item": "Wireless Headphones", "status": "delivered", "amount": 89.99},
    }
    result = orders.get((customer_id, order_id))
    if result:
        return result
    # IMPORTANT DISTINCTION: this is a "valid_empty_result", the search worked fine,
    # nothing just matched. Don't mark this isRetryable, retrying won't find new data.
    return {
        "isError": True,
        "errorCategory": "validation",
        "isRetryable": False,
        "result_type": "valid_empty_result",
        "message": f"Order {order_id} not found for customer {customer_id}. Verify the order ID.",
    }


def process_refund_v2(customer_id: str, order_id: str, amount: float) -> dict:
    if amount > 500:
        return {
            "isError": True,
            "errorCategory": "business",  # a policy rule, not a bug, never retryable
            "isRetryable": False,
            "message": "Refund amount exceeds the $500 policy limit. Escalate to human with reason='amount_exceeded'.",
        }
    if random.random() < 0.2:  # simulate an occasional real service hiccup
        return {
            "isError": True,
            "errorCategory": "transient",  # temporary, safe to just try again
            "isRetryable": True,
            "message": "Payment service temporarily unavailable. Retry in a moment.",
        }
    return {"status": "approved", "refund_id": "REF-9001", "amount": amount}


def demo_error_categories():
    """All four error categories, and what each one means for what happens next."""
    examples = [
        {"errorCategory": "transient", "isRetryable": True, "example": "Payment service timeout, retry up to 2 times"},
        {"errorCategory": "validation", "isRetryable": False, "example": "Customer name not found, ask customer to confirm"},
        {"errorCategory": "business", "isRetryable": False, "example": "Refund > $500, escalate to human, never retry"},
        {"errorCategory": "permission", "isRetryable": False, "example": "Agent not authorized, escalate, do not retry"},
    ]
    for e in examples:
        print(f"  [{e['errorCategory']}] isRetryable={e['isRetryable']} -> {e['example']}")


if __name__ == "__main__":
    print("Error category reference:")
    demo_error_categories()

    print("\nTest get_customer_v2 (unknown name):")
    print(json.dumps(get_customer_v2("Alice Unknown"), indent=2))

    print("\nTest process_refund_v2 (transient failure is random ~20% of runs, try running this a few times):")
    print(json.dumps(process_refund_v2("C-1001", "ORD-555", 89.99), indent=2))
