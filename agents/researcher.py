# agents/researcher.py
from crewai import Agent
from crewai.llm import LLM
from tools.web_search import WebSearchTool


def create_researcher(llm: LLM, config: dict) -> Agent:
    return Agent(
        role=config["role"],
        goal=config["goal"],
        backstory=config["backstory"],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        tools=[WebSearchTool()],
        max_iter=1,
    )
