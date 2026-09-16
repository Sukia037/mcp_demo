"""Checks for the small, dependency-free terminal UI."""

import contextlib
import io
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mcp_client import (  # noqa: E402
    get_server_environment,
    print_banner,
    print_section,
    short_error_message,
)


class ClientUiTests(unittest.TestCase):
    def test_banner_and_section_are_readable_plain_text(self) -> None:
        output = io.StringIO()
        with patch.dict(os.environ, {"KNOWLEDGE_BASE": "yzu"}):
            with contextlib.redirect_stdout(output):
                print_banner()
                print_section("ANSWER")

        rendered = output.getvalue()
        self.assertIn("MCP + LOCAL RAG YZU DEMO", rendered)
        self.assertIn("--- ANSWER", rendered)
        self.assertNotIn("\x1b", rendered)

    def test_banner_shows_the_selected_knowledge_base(self) -> None:
        output = io.StringIO()
        with patch.dict(os.environ, {"KNOWLEDGE_BASE": "physics"}):
            with contextlib.redirect_stdout(output):
                print_banner()

        self.assertIn("MCP + LOCAL RAG PHYSICS DEMO", output.getvalue())

    def test_nested_error_is_shortened_to_its_readable_cause(self) -> None:
        nested = ExceptionGroup(
            "task group failed",
            [RuntimeError("server unavailable")],
        )

        self.assertEqual(short_error_message(nested), "server unavailable")

    def test_ollama_settings_are_forwarded_to_the_mcp_server(self) -> None:
        settings = {
            "KNOWLEDGE_BASE": "yzu",
            "OPENAI_API_KEY": "ollama",
            "OPENAI_BASE_URL": "http://localhost:11434/v1",
            "OPENAI_MODEL": "qwen3:8b",
        }
        with patch.dict(os.environ, settings):
            environment = get_server_environment()

        self.assertEqual(environment, settings)


if __name__ == "__main__":
    unittest.main()
