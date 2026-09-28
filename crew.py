# crew.py
# ── GROQ COMPATIBILITY FIX ──────────────────────────────────────────
import litellm
litellm.drop_params = True  # Drops unsupported params like cache_breakpoint
# ────────────────────────────────────────────────────────────────────

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
    """Loads agent role/goal/backstory definitions from YAML."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_crew(topic: str, num_pages: int = 3) -> Crew:
    """
    Assembles the 6-agent research crew.
    LLM Strategy (Groq Free Tier — September 2026):
    - Cheap reasoning: gpt-oss-20b
    - Strong writing: gpt-oss-120b
    - Tool-calling: compound-mini
    """
    config = load_config()

    # --- LLM Instances ---
    cheap_llm = LLM(
        model="groq/openai/gpt-oss-20b",
        temperature=0.5,
    )
    strong_llm = LLM(
        model="groq/openai/gpt-oss-120b",
        temperature=0.7,
    )
    tool_llm = LLM(
        model="groq/compound-mini",
        temperature=0.4,
    )

    # --- Agents ---
    planner    = create_planner(cheap_llm, config["planner"])
    researcher = create_researcher(tool_llm, config["researcher"])
    validator  = create_validator(tool_llm, config["validator"])
    analyst    = create_analyst(cheap_llm, config["analyst"])
    writer     = create_writer(strong_llm, config["writer"])
    reviewer   = create_reviewer(cheap_llm, config["reviewer"])

    # --- Tasks ---
    plan_task = Task(
        description=(
            f"Break the following topic into 3-5 focused research questions: "
            f"'{topic}'. Each question should be specific enough to answer "
            f"with a single web search."
        ),
        expected_output="A numbered list of 3-5 clear research questions.",
        agent=planner,
    )

    research_task = Task(
        description=(
            "For each research question from the plan, perform a web search "
            "and gather key facts. Cite every source with its URL. "
            "Be thorough but concise — aim for quality over quantity."
        ),
        expected_output=(
            "A detailed Markdown document with answers to each research "
            "question, including source URLs for every claim."
        ),
        agent=researcher,
        context=[plan_task],
    )

    validation_task = Task(
        description=(
            "Cross-check each factual claim from the research. For any claim "
            "that seems uncertain or surprising, perform an additional web "
            "search to verify it. Flag claims that could not be corroborated "
            "by a second independent source."
        ),
        expected_output=(
            "A validation report listing: (1) confirmed facts with sources, "
            "(2) unverified claims that need caution, (3) corrections needed."
        ),
        agent=validator,
        context=[research_task],
    )

    analysis_task = Task(
        description=(
            "Review the validated research findings. Identify the 3 most "
            "important insights, any contradictions between sources, and "
            "knowledge gaps. Keep your output concise and actionable."
        ),
        expected_output=(
            "A concise bullet-point summary of insights, contradictions, "
            "and gaps."
        ),
        agent=analyst,
        context=[research_task, validation_task],
    )

    report_task = Task(
        description=(
            f"Compile a professional research report of approximately "
            f"{num_pages} pages about '{topic}'. Structure it with: "
            f"Executive Summary, Key Findings, Analysis, Conclusion, and "
            f"References. Use the validated research and analysis provided. "
            f"Write in clear, professional prose."
        ),
        expected_output=(
            "A complete Markdown report with clear headings, subheadings, "
            "and a references section with URLs."
        ),
        agent=writer,
        context=[research_task, validation_task, analysis_task],
    )

    review_task = Task(
        description=(
            "Review the draft report for clarity, logical flow, factual "
            "accuracy, and completeness. Suggest specific improvements and "
            "produce the final polished version incorporating your corrections."
        ),
        expected_output=(
            "The final, polished Markdown report with all corrections applied."
        ),
        agent=reviewer,
        context=[report_task],
    )

    # --- Crew Assembly ---
    crew = Crew(
        agents=[planner, researcher, validator, analyst, writer, reviewer],
        tasks=[
            plan_task,
            research_task,
            validation_task,
            analysis_task,
            report_task,
            review_task,
        ],
        process=Process.sequential,
        verbose=True,
        max_rpm=10,
    )
    return crew
