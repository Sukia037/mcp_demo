"""Milestone 2 checks for local document loading and chunking."""

import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from knowledge import DOCUMENTS, load_documents  # noqa: E402


class KnowledgeLoadingTests(unittest.TestCase):
    def test_yzu_documents_are_loaded(self) -> None:
        self.assertEqual(len(DOCUMENTS), 5)
        names = {document.name for document in DOCUMENTS}
        self.assertIn("元智大學資訊工程學系必修科目表.txt", names)
        self.assertIn("元智大學資訊工程學系選修科目表.txt", names)
        self.assertIn("元智大學資訊工程學系專業實習實施辦法.txt", names)
        self.assertGreater(sum(len(document.chunks) for document in DOCUMENTS), 5)

    def test_supported_text_is_loaded_and_other_extensions_are_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            data_dir = Path(directory)
            unique_sentence = "A unique sentence for the loading test."
            (data_dir / "sample.txt").write_text(unique_sentence, encoding="utf-8")
            (data_dir / "ignored.pdf").write_bytes(b"not a real PDF")

            documents = load_documents(data_dir)

            self.assertEqual(len(documents), 1)
            self.assertEqual(documents[0].name, "sample.txt")
            self.assertIn(unique_sentence, documents[0].chunks[0])

    def test_missing_knowledge_directory_has_a_clear_error(self) -> None:
        missing_dir = PROJECT_ROOT / "directory-that-does-not-exist"
        with self.assertRaisesRegex(FileNotFoundError, "Knowledge directory not found"):
            load_documents(missing_dir)


if __name__ == "__main__":
    unittest.main()
