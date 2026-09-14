import streamlit as st
import streamlit.components.v1 as components
from styles import inject_theme, brand_chip_html, force_scroll_top

st.set_page_config(page_title="References · Agentic Essentials", page_icon="📚", layout="wide")
inject_theme()

force_scroll_top()


with st.sidebar:
    st.markdown(brand_chip_html(), unsafe_allow_html=True)
    st.write("")
    st.page_link("Home.py", label="← Back to catalog")
    st.page_link("pages/1_Guide.py", label="📘 Guide")
    st.page_link("pages/2_Support_Agent.py", label="🎧 Support Agent 🟢")
    st.page_link("pages/3_Troubleshooting.py", label="🔧 Troubleshooting")
    st.page_link("pages/4_Summary.py", label="🎉 Summary")

st.markdown('## <span class="gradient-text">Quick Reference</span>', unsafe_allow_html=True)
st.caption("Every rule from the workshop, in one place, for when you're building your own agent later and just need the reminder.")

reference_rows = [
    ("Loop termination", "Always based on finish_reason, never on parsing the model's text."),
    ("Prerequisite enforcement", "Programmatic gates, not prompt instructions, instructions alone have a non-zero failure rate."),
    ("Tool descriptions", "Include: what it does, example trigger phrases, what it returns, and when NOT to use it."),
    ("Error responses", "Always include errorCategory and isRetryable, never a bare {\"error\": \"...\"}."),
    ("Config scoping", "A shared project file (in git) for team conventions; a personal file (not shared) for your own preferences."),
    ("Plan-first triggers", "Large-scale changes, multiple valid approaches, architectural decisions, not small well-scoped fixes."),
    ("Structured output", "A forced tool call with a JSON schema eliminates syntax errors, it does NOT prevent semantically wrong values."),
    ("Batch API", "~50% cost savings, up to a 24-hour window, no latency guarantee, never for a workflow a person is waiting on."),
    ("Escalation triggers", "Explicit human request, policy gap, amount exceeded, unable to progress, ambiguous identity, never sentiment, never \"complexity.\""),
    ("Error propagation", "Distinguish access_failure (worth retrying) from valid_empty_result (retrying won't help)."),
]

for concept, rule in reference_rows:
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown(f"**{concept}**")
    with col2:
        st.write(rule)
    st.divider()

st.markdown("### Where to go next")
st.write(
    "- Try changing the Support Agent's mock functions to call a real API or database.\n"
    "- Look into the Model Context Protocol (MCP) if you want to connect real external "
    "tools, it's an open standard now supported by multiple AI providers, not just one.\n"
    "- Split the extraction work (Domain 4) and the resolution work (Domain 1) into "
    "separate coordinator and subagent roles, using the pattern from Domain 1."
)
