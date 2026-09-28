# crew.py
from litellm_patch import apply_patch
apply_patch()

import yaml
from crewai import Crew, Task, Process
from crewai.llm import LLM
from agents import (
    create_planner,
    create_researcher,
    create_validator,
    create_analyst,
    create_writer,
    create_reviewer,
)


def load_config(path: str = "config/agents.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_crew(topic: str, num_pages: int = 1) -> Crew:
    config = load_config()

    cheap_llm = LLM(
        model="groq/openai/gpt-oss-20b",
        temperature=0.5,
        additional_drop_params=["cache_breakpoint", "is_litellm"],
        max_tokens=800,
    )
    strong_llm = LLM(
        model="groq/openai/gpt-oss-20b",
        temperature=0.7,
        additional_drop_params=["cache_breakpoint", "is_litellm"],
        max_tokens=2000,
    )
    tool_llm = LLM(
        model="groq/openai/gpt-oss-20b",
        temperature=0.4,
        additional_drop_params=["cache_breakpoint", "is_litellm"],
        max_tokens=1000,
    )

    planner = create_planner(cheap_llm, config["planner"])
    researcher = create_researcher(tool_llm, config["researcher"])
    validator = create_validator(tool_llm, config["validator"])
    analyst = create_analyst(cheap_llm, config["analyst"])
    writer = create_writer(strong_llm, config["writer"])
    reviewer = create_reviewer(cheap_llm, config["reviewer"])

    plan_task = Task(
        description=(
            f"Break the following topic into 3 focused research questions: "
            f"'{topic}'. Each question should be answerable with one web search."
        ),
        expected_output="A numbered list of 3 clear research questions.",
        agent=planner,
    )

    research_task = Task(
        description=(
            "For each research question, perform a web search and gather key "
            "facts. Cite every source with its URL."
        ),
        expected_output="A Markdown document with answers and source URLs.",
        agent=researcher,
        context=[plan_task],
    )

    validation_task = Task(
        description=(
            "Cross-check each factual claim. Perform additional web searches "
            "to verify uncertain claims. Flag unverified claims."
        ),
        expected_output="A validation report listing confirmed and unverified claims.",
        agent=validator,
        context=[research_task],
    )

    analysis_task = Task(
        description=(
            "Identify the 3 most important insights, contradictions, and gaps."
        ),
        expected_output="A concise bullet-point summary.",
        agent=analyst,
        context=[research_task, validation_task],
    )

    report_task = Task(
        description=(
            f"Compile a {num_pages}-page research report about '{topic}'. "
            f"Include Executive Summary, Key Findings, Analysis, Conclusion, "
            f"and References."
        ),
        expected_output="A complete Markdown report with headings and URLs.",
        agent=writer,
        context=[research_task, validation_task, analysis_task],
    )

    review_task = Task(
        description=(
            "Review the draft for clarity and accuracy. Produce the final "
            "polished version incorporating your corrections."
        ),
        expected_output="The final polished Markdown report.",
        agent=reviewer,
        context=[report_task],
    )

    crew = Crew(
        agents=[planner, researcher, validator, analyst, writer, reviewer],
        tasks=[plan_task, research_task, validation_task, analysis_task, report_task, review_task],
        process=Process.sequential,
        verbose=True,
        max_rpm=10,
    )
    return crew
