# 🔬 Research Multi-Agent Team

Six specialized AI agents collaborate to research any topic, verify facts with
live web searches, and write a polished report — all on Groq's free tier.

## Agents
1. **Research Planner** — breaks the topic into focused questions
2. **Web Researcher** — searches the web and extracts facts
3. **Source Validator** — cross-checks facts against additional sources
4. **Data Analyst** — finds patterns, contradictions, and gaps
5. **Report Writer** — compiles the final Markdown report
6. **Quality Reviewer** — polishes the report for clarity and accuracy

## Tech Stack
- **CrewAI** — multi-agent orchestration
- **Groq** — free LLM inference (GPT-OSS + Compound models)
- **ddgs** — free web search (no API key needed)
- **Streamlit** — modern web UI

## Setup
1. Get a free Groq API key at [console.groq.com](https://console.groq.com)
2. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
3. Paste your key inside
4. Run: `streamlit run app.py`

## Deploy
Push to GitHub, then deploy on [share.streamlit.io](https://share.streamlit.io)
with your `GROQ_API_KEY` in the secrets field.
