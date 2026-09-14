import json
import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
from styles import inject_theme, brand_chip_html, force_scroll_top

st.set_page_config(page_title="Support Agent · Agentic Essentials", page_icon="🎧", layout="centered")
inject_theme()

force_scroll_top()


st.markdown(
    """
    <style>
    div[data-testid="stChatMessage"] { border-radius: 16px; padding: 2px 4px; margin-bottom: 2px; }
    div[data-testid="stChatMessageAvatarUser"] { background: #1d64ee !important; }
    div[data-testid="stChatMessageAvatarAssistant"] {
        background: linear-gradient(135deg, #1d64ee, #134fc4) !important;
    }
    div[data-testid="stChatInput"] {
        border-radius: 999px !important;
        background: #ffffff !important;
        border: 1.5px solid #d8def0 !important;
        box-shadow: 0 4px 18px rgba(29,100,238,0.10) !important;
    }
    .agent-frame {
        border: 1px solid #e8e6df;
        border-radius: 20px;
        background: #ffffff;
        box-shadow: 0 6px 28px rgba(16,12,9,0.06);
        overflow: hidden;
        margin-bottom: 14px;
    }
    .agent-frame-header {
        display: flex; align-items: center; gap: 12px;
        padding: 16px 22px;
        border-bottom: 1px solid #f0efe9;
        background: linear-gradient(180deg, #f9fbff, #ffffff);
    }
    .agent-frame-icon {
        width: 36px; height: 36px; border-radius: 10px;
        background: linear-gradient(135deg, #1d64ee, #134fc4);
        display: flex; align-items: center; justify-content: center;
        color: white; font-size: 17px;
    }
    .agent-frame-title { font-weight: 800; font-size: 15px; color: #100c09; }
    .agent-frame-sub { font-size: 12px; color: #9c9a94; }
    .status-online {
        margin-left: auto;
        display: inline-flex; align-items: center; gap: 6px;
        font-size: 12px; font-weight: 600; color: #1d8a4e;
        background: rgba(29,138,78,0.10); padding: 4px 12px; border-radius: 999px;
    }
    .status-dot { width: 7px; height: 7px; border-radius: 50%; background: #1d8a4e; }
    .agent-frame-body { padding: 18px 22px 10px; min-height: 120px; }
    .tool-trace-label { font-size: 12.5px; color: #1d64ee; font-weight: 600; }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown(brand_chip_html(), unsafe_allow_html=True)
    st.write("")
    st.page_link("Home.py", label="← Back to catalog")
    st.page_link("pages/1_Guide.py", label="📘 Guide")
    st.page_link("pages/3_Troubleshooting.py", label="🔧 Troubleshooting")
    st.page_link("pages/4_Summary.py", label="🎉 Summary")
    st.page_link("pages/5_References.py", label="📚 References")

# NOTE: verify this against https://platform.openai.com/docs/models before recording.
# model IDs change frequently. GPT-5.6 ("Sol"/"Terra"/"Luna" family) is current as of Aug 2026.
MODEL = "gpt-5.6"

# --- Security: no server-side key, no fallback. ---
# The developer's own key is NEVER read here (no OpenAI(), no os.environ lookup).
# Each visitor must supply their own key, held only in st.session_state for this
# session, never written to disk, never logged.
if "user_openai_key" not in st.session_state:
    st.session_state.user_openai_key = ""

# --- Mock backend functions (Sub-step 1.1 scenario) ---

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


verified_customers = set()

def dispatch_tool(name: str, args: dict) -> dict:
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
        if args.get("amount", 0) > 500:
            return {"error": "Refund amount exceeds $500 policy limit",
                     "errorCategory": "business", "isRetryable": False,
                     "action_required": "Use escalate_to_human with reason='amount_exceeded'"}
        return process_refund(**args)
    if name == "escalate_to_human":
        return escalate_to_human(**args)
    return {"error": f"Unknown tool: {name}"}


# --- Tool schema definitions (OpenAI function-calling format) ---

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

# --- Framed header, Joule-inspired but not copied ---
st.markdown(
    """
    <div class="agent-frame">
        <div class="agent-frame-header">
            <div class="agent-frame-icon">🎧</div>
            <div>
                <div class="agent-frame-title">Support Agent</div>
                <div class="agent-frame-sub">This is the same logic as the agent.py you built in the Guide, wired into a chat UI</div>
            </div>
            <span class="status-online"><span class="status-dot"></span>online</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]


# --- API key gate: nothing below this point runs without a session-scoped key ---
with st.container():
    key_input = st.text_input(
        "Your OpenAI API key",
        type="password",
        value=st.session_state.user_openai_key,
        placeholder="sk-...",
        key="api_key_input_field",
    )
    if key_input != st.session_state.user_openai_key:
        st.session_state.user_openai_key = key_input
    st.caption("🔒 Your key is used only for this session and is never stored or sent anywhere else.")

has_key = bool(st.session_state.user_openai_key.strip())


def render_tool_trace(pairs: list):
    """Render a group of tool calls from one turn as a single collapsible trace."""
    if not pairs:
        return
    with st.expander(f"🔧 Used {len(pairs)} tool{'s' if len(pairs) != 1 else ''}", expanded=False):
        for p in pairs:
            st.markdown(f'<span class="tool-trace-label">→ {p["name"]}({json.dumps(p["args"])})</span>',
                        unsafe_allow_html=True)
            st.code(json.dumps(p["result"], indent=2), language="json")


def render_history():
    """Walk the full message history and render it consistently, live turns and replayed
    history use this exact same function, so they always look identical."""
    pending_calls = {}
    trace_buffer = []
    for msg in st.session_state.messages:
        if msg["role"] == "system":
            continue
        if msg["role"] == "user":
            if trace_buffer:
                render_tool_trace(trace_buffer)
                trace_buffer = []
            with st.chat_message("user", avatar="🧑"):
                st.write(msg["content"])
        elif msg["role"] == "assistant" and msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                name = tc["function"]["name"] if isinstance(tc, dict) else tc.function.name
                args_raw = tc["function"]["arguments"] if isinstance(tc, dict) else tc.function.arguments
                call_id = tc["id"] if isinstance(tc, dict) else tc.id
                pending_calls[call_id] = {"name": name, "args": json.loads(args_raw)}
        elif msg["role"] == "tool":
            call = pending_calls.get(msg["tool_call_id"], {"name": "unknown", "args": {}})
            trace_buffer.append({"name": call["name"], "args": call["args"], "result": json.loads(msg["content"])})
        elif msg["role"] == "assistant" and msg.get("content"):
            if trace_buffer:
                render_tool_trace(trace_buffer)
                trace_buffer = []
            with st.chat_message("assistant", avatar="✨"):
                st.write(msg["content"])
    if trace_buffer:
        render_tool_trace(trace_buffer)


if not has_key:
    st.markdown(
        """
        <div class="glass-card" style="text-align:center;padding:34px 24px;margin-bottom:16px;">
            <div style="font-size:30px;margin-bottom:6px;">🔒</div>
            <div style="font-weight:800;font-size:17px;margin-bottom:6px;color:#100c09;">Enter your OpenAI API key above to try this live</div>
            <div style="color:#9c9a94;font-size:13.5px;">
                Don't have one? Get one at <a href="https://platform.openai.com/api-keys" target="_blank">platform.openai.com</a>.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    if len(st.session_state.messages) == 1:  # only the system prompt, nothing sent yet
        st.markdown(
            """
            <div class="glass-card" style="text-align:center;padding:34px 24px;margin-bottom:16px;">
                <div style="font-size:30px;margin-bottom:6px;">✨</div>
                <div style="font-weight:800;font-size:17px;margin-bottom:6px;color:#100c09;">How can I help you today?</div>
                <div style="color:#9c9a94;font-size:13.5px;">
                    Ask about an order, request a refund, or ask to speak to a human.
                    try: <em>"Where's my order #555, Jane Doe?"</em>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_history()

    user_input = st.chat_input("Message the support agent...")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.spinner("Thinking..."):
            # Client is created fresh, right here, from the session-scoped key only.
            # No fallback: if the key is empty or invalid, this call fails loudly.
            # it never silently uses any other credential.
            client = OpenAI(api_key=st.session_state.user_openai_key)
            while True:
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=st.session_state.messages,
                    tools=TOOLS,
                    reasoning_effort="none",  # required for function/tool calling on gpt-5.6
                )
                choice = response.choices[0]
                finish_reason = choice.finish_reason

                if finish_reason == "tool_calls":
                    st.session_state.messages.append(choice.message.model_dump())
                    for tool_call in choice.message.tool_calls:
                        name = tool_call.function.name
                        args = json.loads(tool_call.function.arguments)
                        result = dispatch_tool(name, args)
                        st.session_state.messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result),
                        })
                    continue  # loop again, finish_reason must reach "stop"

                elif finish_reason == "stop":
                    st.session_state.messages.append({"role": "assistant", "content": choice.message.content})
                    break

                else:
                    st.warning(f"Unhandled finish_reason: {finish_reason}")
                    break

        st.rerun()  # re-render from history, keeps live and replayed turns visually identical

st.caption("Agentic Essentials uses AI. Verify results before acting on them.")
