# agents/planner.py
from crewai import Agent
from crewai.llm import LLM


def create_planner(llm: LLM, config: dict) -> Agent:
    return Agent(
        role=config["role"],
        goal=config["goal"],
        backstory=config["backstory"],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        tools=[],
    )
