import streamlit as st
import streamlit.components.v1 as components
from styles import inject_theme, brand_chip_html, force_scroll_top

st.set_page_config(page_title="Agentic Essentials", page_icon="📘", layout="wide")
inject_theme()

force_scroll_top()


# --- Data-driven guide catalog. Add a new workshop by appending one entry here. ---
GRADIENTS = [
    "linear-gradient(135deg, #4a82f2, #1d64ee 55%, #134fc4)",
]

GUIDES = [
    {
        "avatar_letter": "A",
        "kind": "GUIDE",
        "title": "Agentic Essentials Workshop: Build Production GPT Applications",
        "description": "A five-part workshop for new engineers. Each exercise maps to an "
                        "Agentic Essentials domain and builds on the previous one, ending with "
                        "a working customer support agent pipeline.",
        "author": "Ramy Salem, AI Success Architect, Deployment &amp; Adoption",
        "date": "Aug 9, 2026",
        "duration": "4-5 hours",
        "steps": "8 steps",
        "difficulty": "beginner",
        "category": "AI/ML",
        "hearts": 0,
        "rating": None,  # None = not yet rated, shown as "—"
        "page": "pages/1_Guide.py",
    },
]


def render_card(guide: dict, gradient: str):
    rating_display = f'★ {guide["rating"]}' if guide["rating"] is not None else "★ —"
    st.markdown(
        f"""
        <div class="glass-card" style="padding:0;overflow:hidden;">
            <div style="background:{gradient};padding:22px 22px 16px;position:relative;">
                <div style="position:absolute;top:14px;right:14px;display:flex;gap:6px;">
                    <span style="background:rgba(255,255,255,0.85);border-radius:999px;padding:3px 10px;
                        font-size:11.5px;font-weight:700;color:#1a1a2e;">♡ {guide['hearts']}</span>
                    <span style="background:rgba(255,255,255,0.85);border-radius:999px;padding:3px 10px;
                        font-size:11.5px;font-weight:700;color:#1a1a2e;">{rating_display}</span>
                </div>
                <div style="width:46px;height:46px;border-radius:50%;background:rgba(255,255,255,0.25);
                    backdrop-filter:blur(6px);display:flex;align-items:center;justify-content:center;
                    color:white;font-weight:800;font-size:19px;margin-bottom:12px;
                    border:1.5px solid rgba(255,255,255,0.4);">{guide['avatar_letter']}</div>
                <div style="color:rgba(255,255,255,0.9);font-size:11.5px;font-weight:700;
                    letter-spacing:0.06em;margin-bottom:2px;">📖 {guide['kind']}</div>
            </div>
            <div style="padding:18px 22px 22px;">
                <div style="display:flex;gap:8px;margin-bottom:12px;">
                    <span style="background:rgba(76,175,120,0.15);color:#2f8a5c;border-radius:999px;
                        padding:3px 12px;font-size:11.5px;font-weight:700;">{guide['difficulty']}</span>
                    <span style="background:rgba(29,100,238,0.10);color:#1d64ee;border-radius:999px;
                        padding:3px 12px;font-size:11.5px;font-weight:700;">{guide['category']}</span>
                </div>
                <div style="font-size:17px;font-weight:800;color:#1a1a2e;line-height:1.35;
                    margin-bottom:10px;min-height:46px;">{guide['title']}</div>
                <div style="color:#6b7280;font-size:13px;line-height:1.6;margin-bottom:14px;
                    min-height:82px;">{guide['description']}</div>
                <div style="color:#9aa0b4;font-size:12px;margin-bottom:4px;">{guide['author']} · {guide['date']}</div>
                <div style="color:#9aa0b4;font-size:12px;">🕐 {guide['duration']} &nbsp;&nbsp; 📊 {guide['steps']}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    if st.button("Start Learning →", key=f"start_{guide['title']}", use_container_width=True, type="primary"):
        st.switch_page(guide["page"])


with st.sidebar:
    st.markdown(brand_chip_html(), unsafe_allow_html=True)
    st.write("")
    st.caption("Jump straight to a workshop")
    for guide in GUIDES:
        short_title = guide["title"].split(":")[0].split(", ")[0]
        if st.button(f"{guide['avatar_letter']} {short_title}", key=f"sidebar_{guide['title']}", use_container_width=True):
            st.switch_page(guide["page"])

st.markdown(brand_chip_html(), unsafe_allow_html=True)
st.write("")
st.markdown('<h2 class="gradient-text">Explore Guides</h2>', unsafe_allow_html=True)
st.caption(f"{len(GUIDES)} of {len(GUIDES)} guide{'s' if len(GUIDES) != 1 else ''}")
st.write("")

cols = st.columns(3)
for i, guide in enumerate(GUIDES):
    with cols[i % 3]:
        render_card(guide, GRADIENTS[i % len(GRADIENTS)])

st.write("")
st.divider()
st.page_link("pages/2_Support_Agent.py", label="Jump straight to the finished support agent → 🟢 online", icon="🎧")
