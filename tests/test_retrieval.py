"""Milestone 3 checks for deterministic local retrieval."""

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from retrieval import search_documents  # noqa: E402


class RetrievalTests(unittest.TestCase):
    def assert_top_source(self, question: str, expected_source: str) -> None:
        result = search_documents(question)
        self.assertTrue(result["matches"], result["message"])
        self.assertEqual(result["matches"][0]["source"], expected_source)

    def test_straight_line_motion_question_finds_chapter_2(self) -> None:
        self.assert_top_source(
            "How are position, velocity, and acceleration related in straight-line motion?",
            "02_lecture_outline.txt",
        )

    def test_projectile_motion_question_finds_chapter_3(self) -> None:
        self.assert_top_source(
            "How do vector components describe projectile motion?",
            "03_lecture_outline.txt",
        )

    def test_newtons_laws_question_finds_chapter_4(self) -> None:
        self.assert_top_source(
            "What does Newton's first law say about uniform motion and net force?",
            "04_lecture_outline.txt",
        )

    def test_unrelated_question_has_no_matches(self) -> None:
        result = search_documents("How do I bake a chocolate cake?")
        self.assertEqual(result["matches"], [])
        self.assertEqual(result["message"], "No sufficiently relevant content was found.")

    def test_empty_question_has_no_matches(self) -> None:
        result = search_documents("   ")
        self.assertEqual(result["matches"], [])
        self.assertIn("Please enter", result["message"])


if __name__ == "__main__":
    unittest.main()
