"""Milestone 3 checks for deterministic local retrieval."""

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from retrieval import search_documents  # noqa: E402


IN_DOMAIN_CASES = [
    (
        "資訊工程學系畢業需要多少學分？",
        "元智大學資訊工程學系必修科目表.txt",
    ),
    (
        "程式能力檢定要答對幾題？",
        "元智大學資訊工程學系必修科目表.txt",
    ),
    (
        "申請專業實習需要符合哪些條件？",
        "元智大學資訊工程學系專業實習實施辦法.txt",
    ),
    (
        "專題製作期間要完成哪些活動？",
        "元智大學資訊工程學系專題製作實施要點.txt",
    ),
    (
        "海外研習中斷後還能累計嗎？",
        "元智大學資訊工程學系海外研習實施要點.txt",
    ),
]

OUT_OF_DOMAIN_CASES = [
    "想睡覺了怎麼辦？",
    "今天晚餐吃什麼？",
    "Python quicksort 怎麼寫？",
    "台積電股價是多少？",
    "巧克力蛋糕怎麼做？",
]


class RetrievalTests(unittest.TestCase):
    def assert_top_source(self, question: str, expected_source: str) -> None:
        result = search_documents(question)
        self.assertTrue(result["matches"], result["message"])
        self.assertEqual(result["matches"][0]["source"], expected_source)

    def test_in_domain_evaluation_cases_find_the_expected_source(self) -> None:
        for question, expected_source in IN_DOMAIN_CASES:
            with self.subTest(question=question):
                result = search_documents(question)
                self.assertTrue(result["relevance"]["accepted"])
                self.assertTrue(result["matches"], result["message"])
                self.assertEqual(result["matches"][0]["source"], expected_source)

    def test_elective_course_question_finds_elective_courses(self) -> None:
        self.assert_top_source(
            "哪些選修課程可能不會正常開課？",
            "元智大學資訊工程學系選修科目表.txt",
        )

    def test_out_of_domain_evaluation_cases_fail_the_relevance_gate(self) -> None:
        for question in OUT_OF_DOMAIN_CASES:
            with self.subTest(question=question):
                result = search_documents(question)
                self.assertFalse(result["relevance"]["accepted"])
                self.assertEqual(result["matches"], [])
                self.assertEqual(
                    result["message"],
                    "No sufficiently relevant content was found.",
                )

    def test_empty_question_has_no_matches(self) -> None:
        result = search_documents("   ")
        self.assertEqual(result["matches"], [])
        self.assertIn("Please enter", result["message"])


if __name__ == "__main__":
    unittest.main()
