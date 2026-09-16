"""Milestone 4 checks for retrieval-grounded template answers."""

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from answering import NO_ANSWER_MESSAGE, answer_question  # noqa: E402
from retrieval import search_documents  # noqa: E402


class AnsweringTests(unittest.TestCase):
    def test_answer_uses_the_top_retrieved_chunk_and_reports_sources(self) -> None:
        question = (
            "How are position, velocity, and acceleration related "
            "in straight-line motion?"
        )
        retrieved = search_documents(question)

        response = answer_question(question)

        self.assertIn(retrieved["matches"][0]["content"], response["answer"])
        self.assertEqual(
            response["sources"][0]["name"],
            retrieved["matches"][0]["source"],
        )
        self.assertEqual(len(response["sources"]), 3)

    def test_unrelated_question_does_not_invent_an_answer(self) -> None:
        response = answer_question("How do I bake a chocolate cake?")

        self.assertEqual(response["answer"], NO_ANSWER_MESSAGE)
        self.assertEqual(response["sources"], [])


if __name__ == "__main__":
    unittest.main()

