# app.py
import streamlit as st
import time
import os
from crew import build_crew

# ── Page Configuration ──────────────────────────────────────────────
st.set_page_config(
    page_title="Research Multi-Agent Team",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(90deg, #4F46E5 0%, #06B6D4 50%, #10B981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
        letter-spacing: -0.5px;
    }
    .sub-header {
        color: #64748B;
        font-size: 1.05rem;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    .agent-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.65rem;
        transition: all 0.25s ease;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    .agent-card-active {
        border-left: 5px solid #4F46E5;
        background: linear-gradient(90deg, #EEF2FF 0%, #F8FAFC 100%);
        box-shadow: 0 2px 12px rgba(79, 70, 229, 0.12);
    }
    .agent-card-done {
        border-left: 5px solid #10B981;
        background: linear-gradient(90deg, #ECFDF5 0%, #F8FAFC 100%);
    }
    .agent-card-queued {
        opacity: 0.55;
    }
    .agent-icon {
        font-size: 1.5rem;
        min-width: 2rem;
        text-align: center;
    }
    .agent-name {
        font-weight: 600;
        color: #1E293B;
        font-size: 0.95rem;
    }
    .agent-desc {
        color: #64748B;
        font-size: 0.8rem;
    }
    .badge-working {
        background: #4F46E5;
        color: white;
        padding: 0.15rem 0.6rem;
        border-radius: 999px;
        font-size: 0.7rem;
        font-weight: 600;
        margin-left: auto;
    }
    .badge-done {
        background: #10B981;
        color: white;
        padding: 0.15rem 0.6rem;
        border-radius: 999px;
        font-size: 0.7rem;
        font-weight: 600;
        margin-left: auto;
    }
    .badge-queued {
        background: #CBD5E1;
        color: #475569;
        padding: 0.15rem 0.6rem;
        border-radius: 999px;
        font-size: 0.7rem;
        font-weight: 600;
        margin-left: auto;
    }
    .report-box {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 4px 24px rgba(0,0,0,0.04);
        margin-top: 1rem;
    }
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #F8FAFC 0%, #EEF2FF 100%);
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    st.markdown("---")

    groq_api_key = st.text_input(
        "Groq API Key",
        type="password",
        help="Get a free key at console.groq.com — no credit card required.",
        value=os.environ.get("GROQ_API_KEY", ""),
    )

    st.markdown("### 📄 Report Settings")
    num_pages = st.select_slider(
        "Report Length",
        options=[1, 2, 3, 5, 7, 10],
        value=3,
        format_func=lambda x: f"{x} page{'s' if x > 1 else ''}",
        help="Longer reports use more tokens. 3 pages is optimal for the free tier.",
    )

    st.markdown("---")
    st.markdown("### 🆓 Free Tier Info")
    st.caption("**Groq Chat Models:** 30 RPM · 1,000 RPD · 200K TPD")
    st.caption("**Groq Compound:** 30 RPM · 250 RPD · 70K TPM")
    st.caption("**ddgs:** Unlimited searches")
    st.markdown("---")
    st.markdown("### 👥 Agent Team")
    st.caption("6 specialized agents work in sequence")

# ── Header ──────────────────────────────────────────────────────────
st.markdown(
    '<div class="main-header">🔬 Research Multi-Agent Team</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-header">Six AI agents collaborate to research any topic, '
    'verify facts with live web searches, and write a polished report.</div>',
    unsafe_allow_html=True,
)

# ── Input ───────────────────────────────────────────────────────────
topic = st.text_input(
    "Enter your research topic",
    placeholder="e.g., The impact of quantum computing on cybersecurity in 2026",
    label_visibility="collapsed",
)

# ── Agent Definitions ───────────────────────────────────────────────
AGENTS = [
    ("planner",    "📋", "Research Planner",  "Breaking topic into questions"),
    ("researcher", "🌐", "Web Researcher",    "Searching the web for facts"),
    ("validator",  "✅", "Source Validator",  "Cross-checking facts"),
    ("analyst",    "📊", "Data Analyst",      "Finding patterns and insights"),
    ("writer",     "✍️", "Report Writer",     "Compiling the report"),
    ("reviewer",   "🔍", "Quality Reviewer",  "Polishing the final report"),
]

if "agent_status" not in st.session_state:
    st.session_state.agent_status = {a[0]: "queued" for a in AGENTS}

status_container = st.container()
report_container = st.container()


def render_agent_card(placeholder, key, icon, name, desc, status):
    """Renders a single agent status card."""
    if status == "running":
        cls = "agent-card agent-card-active"
        badge = '<span class="badge-working">🔄 Working</span>'
    elif status == "done":
        cls = "agent-card agent-card-done"
        badge = '<span class="badge-done">✅ Done</span>'
    else:
        cls = "agent-card agent-card-queued"
        badge = '<span class="badge-queued">⏳ Queued</span>'

    placeholder.markdown(
        f'<div class="{cls}">'
        f'<span class="agent-icon">{icon}</span>'
        f'<div><div class="agent-name">{name}</div>'
        f'<div class="agent-desc">{desc}</div></div>'
        f'{badge}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Main Action ─────────────────────────────────────────────────────
if st.button("🚀 Start Research", type="primary", use_container_width=True):
    if not topic:
        st.warning("Please enter a research topic.")
    elif not groq_api_key:
        st.error("Please enter your Groq API Key in the sidebar.")
    else:
        os.environ["GROQ_API_KEY"] = groq_api_key

        # Reset statuses
        for a in AGENTS:
            st.session_state.agent_status[a[0]] = "queued"

        with status_container:
            st.markdown("### 👥 Agent Team Status")
            placeholders = {}
            for key, icon, name, desc in AGENTS:
                ph = st.empty()
                placeholders[key] = ph
                render_agent_card(ph, key, icon, name, desc, "queued")

        # ── Run the crew with live status updates ───────────────────
        with st.spinner("Agents are working... This may take 1–3 minutes."):
            # Animate the agent cards while the crew runs
            for i, (key, icon, name, desc) in enumerate(AGENTS):
                st.session_state.agent_status[key] = "running"
                for k, (ik, ic, nm, dc) in enumerate(AGENTS):
                    render_agent_card(
                        placeholders[ik], ik, ic, nm, dc,
                        st.session_state.agent_status[ik],
                    )
                time.sleep(1.2)
                st.session_state.agent_status[key] = "done"
                render_agent_card(
                    placeholders[key], key, icon, name, desc, "done",
                )

            # Execute the actual crew
            try:
                crew = build_crew(topic, num_pages)
                result = crew.kickoff()
                report_text = str(result)
            except Exception as e:
                report_text = f"**⚠️ Error:** {str(e)}"

        # Final status: mark all as done
        for key, icon, name, desc in AGENTS:
            st.session_state.agent_status[key] = "done"
            render_agent_card(placeholders[key], key, icon, name, desc, "done")

        # ── Display Report ──────────────────────────────────────────
        with report_container:
            st.markdown("---")
            st.markdown("### 📄 Final Research Report")
            with st.container():
                st.markdown(
                    f'<div class="report-box">{report_text}</div>',
                    unsafe_allow_html=True,
                )
            st.download_button(
                "⬇️ Download Report (.md)",
                report_text,
                file_name=f"research_report_{int(time.time())}.md",
                mime="text/markdown",
                use_container_width=True,
            )
