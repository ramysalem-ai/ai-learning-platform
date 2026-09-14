"""
Shared visual theme for Agentic Essentials, a single confident blue,
warm off-white canvas, near-black text, and clean white gradient buttons.
Import and call inject_theme() near the top of every page.
"""
import streamlit as st

PRIMARY = "#1d64ee"
PRIMARY_DARK = "#134fc4"
BG = "#fbfaf6"
HEADLINE = "#100c09"
MUTED = "#9c9a94"


def inject_theme():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

        html, body, [class*="css"] {{ font-family: 'Inter', -apple-system, sans-serif; }}

        .stApp {{ background: {BG}; }}

        h1, h2, h3, h4 {{
            font-weight: 800 !important;
            letter-spacing: -0.02em;
            color: {HEADLINE};
        }}

        p, span, div, li {{ color: {HEADLINE}; }}

        /* ---- Accent text utility (replaces old gradient-text) ---- */
        .gradient-text {{
            color: {PRIMARY};
            font-weight: 800;
        }}

        /* ---- Brand chip (logo mark) ---- */
        .brand-chip {{
            display: inline-flex; align-items: center; gap: 10px;
            padding: 6px 14px 6px 6px;
            background: #ffffff;
            border: 1px solid #e8e6df;
            border-radius: 999px;
            box-shadow: 0 2px 8px rgba(29,100,238,0.08);
        }}
        .brand-chip .mark {{
            width: 30px; height: 30px; border-radius: 50%;
            background: linear-gradient(135deg, {PRIMARY}, {PRIMARY_DARK});
            display: flex; align-items: center; justify-content: center;
            color: white; font-weight: 800; font-size: 15px;
        }}
        .brand-chip .word {{ font-weight: 700; font-size: 14px; color: {HEADLINE}; }}

        /* ---- Cards ---- */
        .glass-card {{
            background: #ffffff;
            border: 1px solid #e8e6df;
            border-radius: 18px;
            padding: 26px 30px;
            box-shadow: 0 4px 20px rgba(16,12,9,0.05);
            transition: all 250ms ease;
        }}
        .glass-card:hover {{
            box-shadow: 0 8px 28px rgba(29,100,238,0.10);
            transform: translateY(-2px);
        }}

        /* ---- Buttons: white fill, subtle blue gradient border/hover ---- */
        div[data-testid="stButton"] button,
        div[data-testid="stFormSubmitButton"] button {{
            background: linear-gradient(180deg, #ffffff, #f4f7ff) !important;
            color: {PRIMARY} !important;
            border: 1.5px solid rgba(29,100,238,0.35) !important;
            border-radius: 999px !important;
            padding: 0.55em 1.5em !important;
            font-weight: 600 !important;
            transition: all 220ms ease !important;
            box-shadow: 0 2px 8px rgba(29,100,238,0.08) !important;
        }}
        div[data-testid="stButton"] button:hover,
        div[data-testid="stFormSubmitButton"] button:hover {{
            border-color: {PRIMARY} !important;
            box-shadow: 0 6px 18px rgba(29,100,238,0.18) !important;
            transform: translateY(-1px);
        }}
        /* primary buttons: solid blue gradient fill */
        div[data-testid="stButton"] button[kind="primary"],
        div[data-testid="stFormSubmitButton"] button[kind="primary"] {{
            background: linear-gradient(135deg, #4a82f2, {PRIMARY} 55%, {PRIMARY_DARK}) !important;
            color: white !important;
            border: none !important;
            box-shadow: 0 4px 16px rgba(29,100,238,0.30) !important;
        }}
        div[data-testid="stButton"] button[kind="primary"]:hover {{
            box-shadow: 0 8px 22px rgba(29,100,238,0.40) !important;
        }}

        /* ---- Sidebar ---- */
        section[data-testid="stSidebar"] {{
            background: #ffffff;
            border-right: 1px solid #e8e6df;
        }}

        /* Hide Streamlit's automatic multipage nav list, every workshop builds its own
           manual navigation instead, so pages from other workshops never bleed into a
           workshop's sidebar. */
        div[data-testid="stSidebarNav"] {{
            display: none;
        }}

        /* ---- Nav pill helper classes (used via raw HTML in the sidebar) ---- */
        .nav-pill {{
            display: block; width: 100%; text-align: left;
            padding: 8px 16px; border-radius: 999px; margin-bottom: 4px;
            font-size: 14px; font-weight: 600; text-decoration: none !important;
            border: 1.5px solid transparent;
        }}
        .nav-pill.inactive {{ color: {HEADLINE}; background: transparent; }}
        .nav-pill.inactive:hover {{ background: #f4f7ff; }}
        .nav-pill.active {{
            color: white;
            background: linear-gradient(135deg, {PRIMARY}, {PRIMARY_DARK});
            box-shadow: 0 3px 10px rgba(29,100,238,0.30);
        }}

        /* ---- Alerts ---- */
        div[data-testid="stAlert"] {{
            border-radius: 14px !important;
            border: 1px solid #e8e6df !important;
        }}

        /* ---- Code blocks ---- */
        code {{ font-family: 'JetBrains Mono', monospace !important; }}
        div[data-testid="stCodeBlock"] pre {{
            border-radius: 14px !important;
            box-shadow: 0 4px 16px rgba(16,12,9,0.08);
        }}

        /* ---- Bordered containers ---- */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 16px !important;
            border: 1px solid #e8e6df !important;
            background: #ffffff;
        }}

        /* ---- Progress bar ---- */
        div[data-testid="stProgress"] > div > div > div {{
            background: linear-gradient(90deg, {PRIMARY}, {PRIMARY_DARK}) !important;
        }}

        /* ---- Expanders ---- */
        details {{
            border-radius: 14px !important;
            border: 1px solid #e8e6df !important;
            background: #ffffff;
        }}

        hr {{
            border: none !important;
            height: 1px !important;
            background: #e8e6df !important;
        }}

        /* ---- Muted caption text ---- */
        [data-testid="stCaptionContainer"] {{ color: {MUTED} !important; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def force_scroll_top():
    """
    Scroll the page back to the top on every navigation (Next/Back/domain switch).
    Streamlit doesn't do this on rerun.

    Two real bugs in the earlier version, now fixed:
    1. All scroll attempts shared one try/except, if the first line threw, every
       later fallback was silently skipped too. Each attempt now has its own
       try/except so one failure can't block the rest.
    2. Streamlit can reuse/cache an unchanged components.html() call across
       reruns and skip re-executing its script. A unique value per render
       (a counter in session_state) is now embedded in the HTML so each
       navigation is seen as a genuinely new component and actually runs.
    """
    import streamlit.components.v1 as components
    if "_scroll_nonce" not in st.session_state:
        st.session_state._scroll_nonce = 0
    st.session_state._scroll_nonce += 1
    nonce = st.session_state._scroll_nonce

    components.html(
        f"""<script>
        // nonce: {nonce}, forces this component to be treated as new each render
        function tryScroll(fn) {{
            try {{ fn(); }} catch (e) {{}}
        }}
        function scrollAllToTop() {{
            tryScroll(function() {{ window.parent.scrollTo(0, 0); }});
            tryScroll(function() {{ window.parent.document.documentElement.scrollTop = 0; }});
            tryScroll(function() {{ window.parent.document.body.scrollTop = 0; }});
            tryScroll(function() {{ window.top.scrollTo(0, 0); }});
            var selectors = ['section.main', '[data-testid="stAppViewContainer"]',
                              '[data-testid="stMain"]', '.main'];
            selectors.forEach(function(sel) {{
                tryScroll(function() {{
                    var els = window.parent.document.querySelectorAll(sel);
                    els.forEach(function(el) {{ el.scrollTo(0, 0); el.scrollTop = 0; }});
                }});
            }});
        }}
        scrollAllToTop();
        setTimeout(scrollAllToTop, 60);
        setTimeout(scrollAllToTop, 200);
        setTimeout(scrollAllToTop, 500);
        </script>""",
        height=0,
    )


def brand_chip_html(label: str = "Agentic Essentials") -> str:
    return f"""
    <div class="brand-chip">
        <div class="mark">∞</div>
        <div class="word">{label}</div>
    </div>
    """


def nav_pill_html(label: str, active: bool = False) -> str:
    """A styled pill for use where a real st.page_link isn't feasible (e.g. the active item)."""
    cls = "active" if active else "inactive"
    return f'<div class="nav-pill {cls}">{label}</div>'
