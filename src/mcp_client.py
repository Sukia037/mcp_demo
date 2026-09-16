"""Minimal CLI client that verifies an MCP stdio round trip."""

import argparse
import sys
from pathlib import Path

import anyio
from mcp import Client, StdioServerParameters
from mcp.types import TextContent


DEFAULT_SERVER_PATH = Path(__file__).with_name("mcp_server.py").resolve()
PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXPECTED_RESPONSE = "MCP connection OK"


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
        print(search_result["message"])
        return

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
    print(f"\nAnswer:\n{response['answer']}")
    sources = response["sources"]
    if not sources:
        print("\nSources: none")
        return

    print("\nSources:")
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
        cwd=PROJECT_ROOT,
    )

    print("Starting MCP server...")
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

                print(EXPECTED_RESPONSE)
            elif answer_question is not None:
                await show_answer(client, answer_question)
            else:
                raise RuntimeError("no client action was selected")
    except Exception as error:
        print(f"MCP connection failed: {error}", file=sys.stderr)
        return 1

    print("Server closed cleanly")
    return 0


def main() -> int:
    args = parse_args()
    question = args.question
    if not (args.health or args.knowledge_status or args.search is not None):
        if question is None:
            question = input("Question: ")

    return anyio.run(
        check_connection,
        args.server,
        args.knowledge_status,
        args.search,
        question,
        args.health,
    )


if __name__ == "__main__":
    raise SystemExit(main())
