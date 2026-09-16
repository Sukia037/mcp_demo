"""Minimal MCP server used to verify the stdio connection."""

from mcp.server import MCPServer

from answering import answer_question as build_answer
from knowledge import get_knowledge_status
from retrieval import search_documents as retrieve_documents


mcp = MCPServer("mcp-rag-demo", log_level="WARNING")


@mcp.tool()
def health_check() -> str:
    """Confirm that the MCP server can receive and answer a tool call."""
    return "MCP connection OK"


@mcp.tool()
def knowledge_status() -> dict[str, object]:
    """Report which local documents were loaded and how many chunks they contain."""
    return get_knowledge_status()


@mcp.tool()
def search_documents(question: str, limit: int = 3) -> dict[str, object]:
    """Find the most relevant local document chunks for a question."""
    return retrieve_documents(question, limit)


@mcp.tool()
def answer_question(question: str) -> dict[str, object]:
    """Answer a question from retrieved local context and include its sources."""
    return build_answer(question)


if __name__ == "__main__":
    mcp.run()
