import streamlit as st
import streamlit.components.v1 as components
from styles import inject_theme, brand_chip_html, force_scroll_top

st.set_page_config(page_title="Troubleshooting · Agentic Essentials", page_icon="🔧", layout="wide")
inject_theme()

force_scroll_top()


with st.sidebar:
    st.markdown(brand_chip_html(), unsafe_allow_html=True)
    st.write("")
    st.page_link("Home.py", label="← Back to catalog")
    st.page_link("pages/1_Guide.py", label="📘 Guide")
    st.page_link("pages/2_Support_Agent.py", label="🎧 Support Agent 🟢")

st.markdown('## <span class="gradient-text">Troubleshooting</span>', unsafe_allow_html=True)
st.caption("Real problems, real fixes, including several we actually hit building this workshop.")

st.info(
    "💡 **Not sure your agent.py matches?** A complete, verified copy is included in this "
    "download at `reference/agent_complete.py`, open it side-by-side with your own file "
    "at any point to check."
)

st.markdown("### From the original workshop, updated for OpenAI")

original_issues = [
    {
        "problem": "AuthenticationError",
        "solution": (
            "Set your key again in the terminal you're running from: "
            "`$env:OPENAI_API_KEY=\"your-key\"` (Windows) or `export OPENAI_API_KEY=\"your-key\"` "
            "(Mac/Linux). This only lasts for that one terminal window, closing it clears the "
            "key, and you'll need to set it again next time."
        ),
    },
    {
        "problem": "Loop runs forever",
        "solution": (
            "Check that your `finish_reason == \"stop\"` condition is actually the one that "
            "breaks the loop, it's easy to accidentally check the wrong branch, or check "
            "`finish_reason == \"tool_calls\"` for both cases by mistake."
        ),
    },
    {
        "problem": "The agent skips get_customer",
        "solution": (
            "Your tool descriptions may not clearly state the dependency, make it explicit, "
            "e.g. \"Requires customer_id from get_customer, never pass a customer name here.\" "
            "If that still doesn't work, force it with `tool_choice={\"type\": \"function\", "
            "\"function\": {\"name\": \"get_customer\"}}` for the first turn."
        ),
    },
    {
        "problem": "Extraction returns fabricated values",
        "solution": (
            "Make the fields nullable in your schema so the model can return null instead of "
            "inventing data to fill a field it thinks is required."
        ),
    },
    {
        "problem": "Project instructions don't seem to be applied",
        "solution": (
            "If you're using the layered project-instructions pattern from Domain 3, double "
            "check the shared file is actually being loaded and prepended to your system "
            "prompt, a common mistake is editing a personal/local copy instead of the one "
            "your code actually reads from."
        ),
    },
]
for item in original_issues:
    with st.expander(f"❗ {item['problem']}"):
        st.write(item["solution"])

st.markdown("### From actually setting this up (new, worth reading)")

new_issues = [
    {
        "problem": "\"Function tools with reasoning_effort are not supported...\" error",
        "solution": (
            "Add `reasoning_effort=\"none\"` to your `client.chat.completions.create(...)` call "
            "whenever you're also passing `tools=`. Some models reject tool calls unless this "
            "is explicitly set."
        ),
    },
    {
        "problem": "\"Missing credentials\" / OpenAIError even though you set the key",
        "solution": (
            "You probably set the key in a *different* terminal window than the one you're "
            "running the app from. The key only exists in the exact terminal session where "
            "you typed it, re-set it in the same window you're about to run "
            "`python -m streamlit run Home.py` from."
        ),
    },
    {
        "problem": "\"This site can't be reached\" / localhost refused to connect",
        "solution": (
            "The app probably hadn't finished starting yet when you tried to open it. Go back "
            "to your terminal, if it's stuck asking for an email, just press Enter to skip. "
            "Wait until you see a line that says `Local URL: http://localhost:8501` by itself, "
            "*then* open that address."
        ),
    },
    {
        "problem": "`dir` doesn't show Home.py after extracting the zip",
        "solution": (
            "Unzipping sometimes creates a folder inside another folder with the same name. "
            "Run `cd` followed by the folder name again to go one level deeper, then check "
            "`dir` again, repeat until you see `Home.py` listed directly."
        ),
    },
    {
        "problem": "\"streamlit is not recognized as a command\"",
        "solution": (
            "Use `python -m streamlit run Home.py` instead of `streamlit run Home.py`, this "
            "asks Python to find and run Streamlit directly, which works even when Streamlit "
            "isn't on your system's PATH."
        ),
    },
    {
        "problem": "A command seems to run something completely different than what you typed",
        "solution": (
            "Two commands probably got pasted together and merged into one. Only type or "
            "paste **one command at a time**, and press Enter after each one, before typing "
            "the next."
        ),
    },
]
for item in new_issues:
    with st.expander(f"❗ {item['problem']}"):
        st.write(item["solution"])
