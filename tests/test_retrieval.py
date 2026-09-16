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

    def test_graduation_credit_question_finds_required_courses(self) -> None:
        self.assert_top_source(
            "資訊工程學系畢業需要多少學分？",
            "元智大學資訊工程學系必修科目表.txt",
        )

    def test_elective_course_question_finds_elective_courses(self) -> None:
        self.assert_top_source(
            "哪些選修課程可能不會正常開課？",
            "元智大學資訊工程學系選修科目表.txt",
        )

    def test_internship_question_finds_internship_rules(self) -> None:
        self.assert_top_source(
            "申請專業實習需要符合哪些條件？",
            "元智大學資訊工程學系專業實習實施辦法.txt",
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
