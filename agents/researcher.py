# agents/researcher.py
from crewai import Agent
from crewai.llm import LLM
from tools.web_search import WebSearchTool


def create_researcher(llm: LLM, config: dict) -> Agent:
    """
    Creates the Web Researcher agent (uses web search tool).

    max_iter=1 is CRITICAL: openai/gpt-oss-120b on Groq fails on the second
    request of a multi-turn tool loop (tool_call_id serialized as null).
    Limiting to 1 iteration avoids this bug entirely.
    """
    return Agent(
        role=config["role"],
        goal=config["goal"],
        backstory=config["backstory"],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        tools=[WebSearchTool()],
        max_iter=1,   # ← prevents the GPT-OSS multi-turn tool loop bug
    )
