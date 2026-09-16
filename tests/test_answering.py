"""Checks for retrieval-grounded LLM answers and the safe fallback."""

import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from answering import (  # noqa: E402
    NO_ANSWER_MESSAGE,
    answer_question,
    generate_grounded_answer,
)
from retrieval import search_documents  # noqa: E402


class AnsweringTests(unittest.TestCase):
    def test_answer_uses_the_top_retrieved_chunk_and_reports_sources(self) -> None:
        question = "資訊工程學系畢業需要多少學分？"
        retrieved = search_documents(question)

        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            response = answer_question(question)

        self.assertIn(retrieved["matches"][0]["content"], response["answer"])
        self.assertEqual(
            response["sources"][0]["name"],
            retrieved["matches"][0]["source"],
        )
        self.assertEqual(len(response["sources"]), 3)
        self.assertEqual(response["generation"]["mode"], "template_fallback")

    def test_llm_receives_all_retrieved_context_and_returns_grounded_answer(self) -> None:
        captured = {}

        def fake_generator(question, matches, model):
            captured["question"] = question
            captured["matches"] = matches
            captured["model"] = model
            return "畢業至少須修滿128學分 [元智大學資訊工程學系必修科目表.txt]。"

        response = answer_question(
            "程式能力檢定要答對幾題？",
            llm_generator=fake_generator,
        )

        self.assertEqual(response["generation"]["mode"], "llm")
        self.assertEqual(len(captured["matches"]), 3)
        self.assertIn("元智大學資訊工程學系必修科目表.txt", response["answer"])
        self.assertEqual(response["warning"], None)

    def test_responses_api_request_contains_question_context_and_safety_rules(self) -> None:
        class FakeResponses:
            def __init__(self):
                self.arguments = None

            def create(self, **kwargs):
                self.arguments = kwargs
                return SimpleNamespace(output_text="A grounded answer.")

        fake_responses = FakeResponses()
        fake_client = SimpleNamespace(responses=fake_responses)
        matches = search_documents("程式能力檢定要答對幾題？")["matches"]

        with patch.dict(os.environ, {"OPENAI_BASE_URL": ""}):
            answer = generate_grounded_answer(
                "程式能力檢定要答對幾題？",
                matches,
                "test-model",
                client=fake_client,
            )

        self.assertEqual(answer, "A grounded answer.")
        self.assertEqual(fake_responses.arguments["model"], "test-model")
        self.assertFalse(fake_responses.arguments["store"])
        self.assertIn("程式能力檢定要答對幾題？", fake_responses.arguments["input"])
        self.assertIn(matches[0]["content"], fake_responses.arguments["input"])
        self.assertIn("only the supplied", fake_responses.arguments["instructions"])

    def test_ollama_uses_chat_without_hidden_reasoning(self) -> None:
        class FakeCompletions:
            def __init__(self):
                self.arguments = None

            def create(self, **kwargs):
                self.arguments = kwargs
                message = SimpleNamespace(content="A local grounded answer.")
                return SimpleNamespace(choices=[SimpleNamespace(message=message)])

        fake_completions = FakeCompletions()
        fake_client = SimpleNamespace(
            chat=SimpleNamespace(completions=fake_completions),
        )
        matches = search_documents("程式能力檢定要答對幾題？")["matches"]

        with patch.dict(
            os.environ,
            {"OPENAI_BASE_URL": "http://localhost:11434/v1"},
        ):
            answer = generate_grounded_answer(
                "程式能力檢定要答對幾題？",
                matches,
                "qwen3:8b",
                client=fake_client,
            )

        self.assertEqual(answer, "A local grounded answer.")
        self.assertEqual(fake_completions.arguments["model"], "qwen3:8b")
        self.assertEqual(fake_completions.arguments["reasoning_effort"], "none")
        self.assertEqual(fake_completions.arguments["temperature"], 0.2)
        self.assertIn("Retrieved local context", fake_completions.arguments["messages"][1]["content"])

    def test_ollama_retries_one_empty_response(self) -> None:
        class FakeCompletions:
            def __init__(self):
                self.calls = 0

            def create(self, **kwargs):
                self.calls += 1
                text = "" if self.calls == 1 else "Recovered local answer."
                message = SimpleNamespace(content=text)
                return SimpleNamespace(choices=[SimpleNamespace(message=message)])

        fake_completions = FakeCompletions()
        fake_client = SimpleNamespace(
            chat=SimpleNamespace(completions=fake_completions),
        )
        matches = search_documents("程式能力檢定要答對幾題？")["matches"]

        with patch.dict(
            os.environ,
            {"OPENAI_BASE_URL": "http://localhost:11434/v1"},
        ):
            answer = generate_grounded_answer(
                "程式能力檢定要答對幾題？",
                matches,
                "qwen3:8b",
                client=fake_client,
            )

        self.assertEqual(answer, "Recovered local answer.")
        self.assertEqual(fake_completions.calls, 2)

    def test_llm_error_falls_back_without_losing_sources(self) -> None:
        def failing_generator(question, matches, model):
            raise RuntimeError("simulated API failure")

        response = answer_question(
            "申請專業實習需要符合哪些條件？",
            llm_generator=failing_generator,
        )

        self.assertEqual(response["generation"]["mode"], "template_fallback")
        self.assertTrue(response["sources"])
        self.assertIn("LLM generation is unavailable", response["warning"])

    def test_unrelated_question_does_not_invent_an_answer(self) -> None:
        called = False

        def generator_should_not_run(question, matches, model):
            nonlocal called
            called = True
            return "This should not be returned."

        response = answer_question(
            "How do I bake a chocolate cake?",
            llm_generator=generator_should_not_run,
        )

        self.assertEqual(response["answer"], NO_ANSWER_MESSAGE)
        self.assertEqual(response["sources"], [])
        self.assertEqual(response["generation"]["mode"], "not_used")
        self.assertFalse(called)


if __name__ == "__main__":
    unittest.main()
