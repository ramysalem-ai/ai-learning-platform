import streamlit as st
import streamlit.components.v1 as components
from styles import inject_theme, brand_chip_html, force_scroll_top

st.set_page_config(page_title="Summary · Agentic Essentials", page_icon="🎉", layout="wide")
inject_theme()

force_scroll_top()


with st.sidebar:
    st.markdown(brand_chip_html(), unsafe_allow_html=True)
    st.write("")
    st.page_link("Home.py", label="← Back to catalog")
    st.page_link("pages/1_Guide.py", label="📘 Guide")
    st.page_link("pages/2_Support_Agent.py", label="🎧 Support Agent 🟢")
    st.page_link("pages/3_Troubleshooting.py", label="🔧 Troubleshooting")
    st.page_link("pages/5_References.py", label="📚 References")

st.markdown('## 🎉 <span class="gradient-text">Congratulations, you\'ve completed the Agentic Essentials Workshop!</span>', unsafe_allow_html=True)
st.write(
    "You've built a working customer support agent from scratch, covering all five "
    "Agentic Essentials domains with real, hands-on code, not just reading about it."
)

st.markdown("### What you built")

rows = [
    ("1", "Agentic Architecture & Orchestration",
     "An agentic loop controlled by finish_reason, a manager-and-specialists pattern, "
     "and a programmatic prerequisite gate."),
    ("2", "Tool Design & MCP Integration",
     "Sharper tool descriptions with explicit boundaries, and structured errors with "
     "errorCategory and isRetryable."),
    ("3", "Project Setup & Configuration",
     "Shared project conventions, file-pattern rules, a plan-first-when-risky pattern, "
     "and non-interactive review scripts."),
    ("4", "Prompt Engineering & Structured Output",
     "Forced structured output with nullable fields, a validation-retry loop, few-shot "
     "examples, and a sync-vs-batch decision guide."),
    ("5", "Context Management & Reliability",
     "Result trimming, explicit escalation criteria, labeled subagent errors, "
     "crash-recovery scratchpads, and source provenance."),
]
for num, title, desc in rows:
    with st.container(border=True):
        st.markdown(f"**Domain {num}, {title}**")
        st.caption(desc)

st.write("")
st.markdown("### Where to go from here")
st.write(
    "- Try changing the Support Agent's scenario to a domain closer to your own work, "
    "the same 5 domains of patterns apply regardless of what the agent actually does.\n"
    "- Add a real external tool or database instead of the mock functions used here.\n"
    "- Build a second, independent agent and connect them using the coordinator-subagent "
    "pattern from Domain 1, that's the natural next step once one agent alone isn't enough."
)

st.write("")
col1, col2 = st.columns(2)
with col1:
    if st.button("🎧 Try the finished agent again", use_container_width=True):
        st.switch_page("pages/2_Support_Agent.py")
with col2:
    if st.button("📚 Browse the quick reference", use_container_width=True, type="primary"):
        st.switch_page("pages/5_References.py")
