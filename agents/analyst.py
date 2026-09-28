# agents/analyst.py
from crewai import Agent
from crewai.llm import LLM


def create_analyst(llm: LLM, config: dict) -> Agent:
    """Creates the Data Analyst agent."""
    return Agent(
        role=config["role"],
        goal=config["goal"],
        backstory=config["backstory"],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        tools=[],
    )
