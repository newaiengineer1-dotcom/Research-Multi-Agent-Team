# tools/web_search.py
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from ddgs import DDGS
from typing import Type


class WebSearchInput(BaseModel):
    """Input schema for WebSearchTool."""
    query: str = Field(..., description="The search query to look up on the web.")


class WebSearchTool(BaseTool):
    name: str = "Web Search"
    description: str = (
        "Search the web for current information on a given query. "
        "Returns the top 5 results with titles, snippets, and URLs. "
        "Use this tool whenever you need factual, up-to-date information."
    )
    args_schema: Type[BaseModel] = WebSearchInput

    def _run(self, query: str) -> str:
        try:
            results = DDGS().text(query, max_results=5)
            if not results:
                return "No results found for this query."
            output = []
            for r in results:
                output.append(
                    f"**{r.get('title', 'N/A')}**\n"
                    f"{r.get('body', 'N/A')}\n"
                    f"Source: {r.get('href', 'N/A')}"
                )
            return "\n\n---\n\n".join(output)
        except Exception as e:
            return f"Search failed: {str(e)}. Try rephrasing the query."
