"""Minimal CLI client that verifies an MCP stdio round trip."""

import argparse
import os
import sys
from pathlib import Path

import anyio
from mcp import Client, StdioServerParameters
from mcp.types import TextContent


DEFAULT_SERVER_PATH = Path(__file__).with_name("mcp_server.py").resolve()
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_KNOWLEDGE_BASE = "yzu"
EXPECTED_RESPONSE = "MCP connection OK"
UI_WIDTH = 64


def configure_terminal_encoding() -> None:
    """Keep Unicode document text readable on Windows terminals."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def print_banner() -> None:
    knowledge_base = (
        os.getenv("KNOWLEDGE_BASE", DEFAULT_KNOWLEDGE_BASE).strip()
        or DEFAULT_KNOWLEDGE_BASE
    )
    print("=" * UI_WIDTH)
    print(f" MCP + LOCAL RAG {knowledge_base.upper()} DEMO")
    print("=" * UI_WIDTH)


def print_section(title: str) -> None:
    print(f"\n--- {title} " + "-" * max(UI_WIDTH - len(title) - 5, 0))


def short_error_message(error: BaseException) -> str:
    """Return one readable cause instead of a nested task-group message."""
    current = error
    while nested := getattr(current, "exceptions", None):
        current = nested[0]

    message = str(current).strip() or type(current).__name__
    return message if len(message) <= 240 else f"{message[:237]}..."


def get_server_environment() -> dict[str, str]:
    """Forward the knowledge-base and LLM settings needed by the server."""
    return {
        name: value
        for name in (
            "KNOWLEDGE_BASE",
            "OPENAI_API_KEY",
            "OPENAI_BASE_URL",
            "OPENAI_MODEL",
        )
        if (value := os.environ.get(name))
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ask questions through the local MCP document server."
    )
    parser.add_argument(
        "question",
        nargs="?",
        help="Question to answer. If omitted, the client prompts for one.",
    )
    parser.add_argument(
        "--server",
        type=Path,
        default=DEFAULT_SERVER_PATH,
        help="Path to the MCP server script (used to test startup errors).",
    )
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument(
        "--health",
        action="store_true",
        help="Run only the Milestone 1 connection check.",
    )
    actions.add_argument(
        "--knowledge-status",
        action="store_true",
        help="Show the local documents loaded by the MCP server.",
    )
    actions.add_argument(
        "--search",
        metavar="QUESTION",
        help="Search the local documents and show the top matching chunks.",
    )
    return parser.parse_args()


async def show_knowledge_status(client: Client) -> None:
    result = await client.call_tool("knowledge_status", {})
    if result.is_error or not isinstance(result.structured_content, dict):
        raise RuntimeError("knowledge_status returned an invalid MCP result")

    status = result.structured_content
    print_section("LOCAL KNOWLEDGE")
    print(
        f"Loaded {status['document_count']} documents "
        f"into {status['chunk_count']} chunks"
    )
    for document in status["documents"]:
        print(f"- {document['name']}: {document['chunks']} chunks")


async def show_search_results(client: Client, question: str) -> None:
    result = await client.call_tool(
        "search_documents",
        {"question": question, "limit": 3},
    )
    if result.is_error or not isinstance(result.structured_content, dict):
        raise RuntimeError("search_documents returned an invalid MCP result")

    search_result = result.structured_content
    matches = search_result["matches"]
    if not matches:
        print_section("RETRIEVAL")
        print(search_result["message"])
        return

    print_section("RETRIEVAL RESULTS")
    for position, match in enumerate(matches, start=1):
        preview = match["content"].replace("\n", " ")[:500]
        print(
            f"\n{position}. {match['source']} "
            f"(chunk {match['chunk']}, score {match['score']})"
        )
        print(preview)


async def show_answer(client: Client, question: str) -> None:
    result = await client.call_tool("answer_question", {"question": question})
    if result.is_error or not isinstance(result.structured_content, dict):
        raise RuntimeError("answer_question returned an invalid MCP result")

    response = result.structured_content
    print_section("ANSWER")
    print(response["answer"])
    generation = response.get("generation", {})
    print_section("GENERATION")
    if generation.get("mode") == "llm":
        provider = generation.get("provider", "llm")
        print(f"LLM ({provider} / {generation['model']})")
    elif generation.get("mode") == "template_fallback":
        print("Template fallback")
    else:
        print("LLM not used")
    if response.get("warning"):
        print(f"Note: {response['warning']}")

    sources = response["sources"]
    print_section("SOURCES")
    if not sources:
        print("None")
        return

    for source in sources:
        print(
            f"- {source['name']} "
            f"(chunk {source['chunk']}, score {source['score']})"
        )


async def check_connection(
    server_path: Path,
    show_status: bool = False,
    search_question: str | None = None,
    answer_question: str | None = None,
    health_only: bool = False,
) -> int:
    server_path = server_path.resolve()
    if not server_path.is_file():
        print(
            f"MCP connection failed: server file not found: {server_path}",
            file=sys.stderr,
        )
        return 1

    server = StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)],
        env=get_server_environment(),
        cwd=PROJECT_ROOT,
    )

    print_banner()
    print("Status: starting MCP server...")
    try:
        async with Client(server) as client:
            if search_question is not None:
                await show_search_results(client, search_question)
            elif show_status:
                await show_knowledge_status(client)
            elif health_only:
                result = await client.call_tool("health_check", {})
                if result.is_error:
                    raise RuntimeError("health_check returned an MCP tool error")

                messages = [
                    block.text
                    for block in result.content
                    if isinstance(block, TextContent)
                ]
                if EXPECTED_RESPONSE not in messages:
                    raise RuntimeError(
                        f"unexpected health_check response: {messages or '[no text]'}"
                    )

                print_section("HEALTH")
                print(EXPECTED_RESPONSE)
            elif answer_question is not None:
                await show_answer(client, answer_question)
            else:
                raise RuntimeError("no client action was selected")
    except Exception as error:
        print(
            f"MCP connection failed: {short_error_message(error)}",
            file=sys.stderr,
        )
        return 1

    print("\nStatus: server closed cleanly")
    return 0


def main() -> int:
    configure_terminal_encoding()
    try:
        args = parse_args()
        question = args.question
        if not (args.health or args.knowledge_status or args.search is not None):
            if question is None:
                question = input("Question: ")
            if not question.strip():
                print("Please enter a non-empty question.", file=sys.stderr)
                return 1

        return anyio.run(
            check_connection,
            args.server,
            args.knowledge_status,
            args.search,
            question,
            args.health,
        )
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
