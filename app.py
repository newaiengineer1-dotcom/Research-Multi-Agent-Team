# app.py
import streamlit as st
import traceback
import time
import os

# ── Diagnostic import of crew ────────────────────────────────────────
try:
    from crew import build_crew
except Exception:
    st.set_page_config(page_title="Import Error", page_icon="⚠️")
    st.error("Import failed. Full traceback below:")
    st.code(traceback.format_exc(), language="python")
    st.stop()
# ─────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Research Multi-Agent Team",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(90deg, #4F46E5 0%, #06B6D4 50%, #10B981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
    }
    .sub-header { color: #64748B; font-size: 1.05rem; margin-bottom: 2rem; }
    .agent-card {
        background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 14px;
        padding: 1rem 1.25rem; margin-bottom: 0.65rem;
    }
    .agent-card-active { border-left: 5px solid #4F46E5; background: #EEF2FF; }
    .agent-card-done { border-left: 5px solid #10B981; background: #ECFDF5; }
    .agent-card-queued { opacity: 0.55; }
    .agent-name { font-weight: 600; color: #1E293B; font-size: 0.95rem; }
    .agent-desc { color: #64748B; font-size: 0.8rem; }
    .badge-working { background: #4F46E5; color: white; padding: 0.15rem 0.6rem;
        border-radius: 999px; font-size: 0.7rem; font-weight: 600; }
    .badge-done { background: #10B981; color: white; padding: 0.15rem 0.6rem;
        border-radius: 999px; font-size: 0.7rem; font-weight: 600; }
    .badge-queued { background: #CBD5E1; color: #475569; padding: 0.15rem 0.6rem;
        border-radius: 999px; font-size: 0.7rem; font-weight: 600; }
    .report-box {
        background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px;
        padding: 2rem; box-shadow: 0 4px 24px rgba(0,0,0,0.04); margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    st.markdown("---")
    groq_api_key = st.text_input(
        "Groq API Key",
        type="password",
        help="Get a free key at console.groq.com",
        value=os.environ.get("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", "")),
    )
    st.markdown("### 📄 Report Settings")
    num_pages = st.select_slider(
        "Report Length",
        options=[1, 2, 3, 5, 7, 10],
        value=1,
        format_func=lambda x: f"{x} page{'s' if x > 1 else ''}",
    )
    st.markdown("---")
    st.caption("Groq free tier: 200K tokens/day")

st.markdown('<div class="main-header">🔬 Research Multi-Agent Team</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Six AI agents research any topic and write a report.</div>', unsafe_allow_html=True)

topic = st.text_input(
    "Enter your research topic",
    placeholder="e.g., The impact of quantum computing on cybersecurity in 2026",
    label_visibility="collapsed",
)

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


def render_card(ph, icon, name, desc, status):
    if status == "running":
        cls, badge = "agent-card agent-card-active", '<span class="badge-working">🔄 Working</span>'
    elif status == "done":
        cls, badge = "agent-card agent-card-done", '<span class="badge-done">✅ Done</span>'
    else:
        cls, badge = "agent-card agent-card-queued", '<span class="badge-queued">⏳ Queued</span>'
    ph.markdown(
        f'<div class="{cls}"><span style="font-size:1.5rem;">{icon}</span>'
        f'<div><div class="agent-name">{name}</div>'
        f'<div class="agent-desc">{desc}</div></div>{badge}</div>',
        unsafe_allow_html=True,
    )


if st.button("🚀 Start Research", type="primary", use_container_width=True):
    if not topic:
        st.warning("Please enter a research topic.")
    elif not groq_api_key:
        st.error("Please enter your Groq API Key in the sidebar.")
    else:
        os.environ["GROQ_API_KEY"] = groq_api_key

        for a in AGENTS:
            st.session_state.agent_status[a[0]] = "queued"

        st.markdown("### 👥 Agent Team Status")
        placeholders = {}
        for key, icon, name, desc in AGENTS:
            ph = st.empty()
            placeholders[key] = ph
            render_card(ph, icon, name, desc, "queued")

        with st.spinner("Agents are working..."):
            for key, icon, name, desc in AGENTS:
                st.session_state.agent_status[key] = "running"
                for ik, ic, nm, dc in AGENTS:
                    render_card(placeholders[ik], ic, nm, dc, st.session_state.agent_status[ik])
                time.sleep(1.0)
                st.session_state.agent_status[key] = "done"
                render_card(placeholders[key], icon, name, desc, "done")

            try:
                crew = build_crew(topic, num_pages)
                result = crew.kickoff()
                report_text = str(result)
            except Exception as e:
                err = str(e).lower()
                if "rate_limit" in err:
                    report_text = "**⏳ Daily token limit reached.** Wait until midnight UTC."
                elif "tool_use_failed" in err:
                    report_text = "**⚠️ Tool call failed.** Try a simpler topic or shorter report."
                else:
                    report_text = f"**⚠️ Error:** {str(e)}"

        for key, icon, name, desc in AGENTS:
            st.session_state.agent_status[key] = "done"
            render_card(placeholders[key], icon, name, desc, "done")

        st.markdown("---")
        st.markdown("### 📄 Final Research Report")
        st.markdown(f'<div class="report-box">{report_text}</div>', unsafe_allow_html=True)
        st.download_button(
            "⬇️ Download Report (.md)",
            report_text,
            file_name=f"research_report_{int(time.time())}.md",
            mime="text/markdown",
            use_container_width=True,
        )
