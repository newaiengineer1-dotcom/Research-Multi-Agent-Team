# agents/validator.py
from crewai import Agent
from crewai.llm import LLM
from tools.web_search import WebSearchTool


def create_validator(llm: LLM, config: dict) -> Agent:
    """
    Creates the Source Validator agent (uses web search for fact-checking).

    max_iter=1 is CRITICAL: same GPT-OSS multi-turn tool loop bug applies.
    """
    return Agent(
        role=config["role"],
        goal=config["goal"],
        backstory=config["backstory"],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        tools=[WebSearchTool()],
        max_iter=1,   # ← same fix as researcher
    )
