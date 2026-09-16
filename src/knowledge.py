"""Load one local knowledge base and split its text files into chunks."""

import os
import re
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_KNOWLEDGE_BASE = "yzu"
KNOWLEDGE_BASE = os.getenv("KNOWLEDGE_BASE", DEFAULT_KNOWLEDGE_BASE).strip()
DATA_DIR = PROJECT_ROOT / "data" / (KNOWLEDGE_BASE or DEFAULT_KNOWLEDGE_BASE)
SUPPORTED_SUFFIXES = {".md", ".txt"}
MAX_CHUNK_CHARACTERS = 1_600


@dataclass(frozen=True)
class Document:
    name: str
    chunks: tuple[str, ...]


def _split_long_section(section: str) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", section) if part.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_length = 0

    for paragraph in paragraphs:
        if len(paragraph) > MAX_CHUNK_CHARACTERS:
            if current:
                chunks.append("\n\n".join(current))
                current = []
                current_length = 0
            chunks.extend(
                paragraph[start : start + MAX_CHUNK_CHARACTERS]
                for start in range(0, len(paragraph), MAX_CHUNK_CHARACTERS)
            )
            continue

        separator_length = 2 if current else 0
        if current_length + separator_length + len(paragraph) > MAX_CHUNK_CHARACTERS:
            chunks.append("\n\n".join(current))
            current = [paragraph]
            current_length = len(paragraph)
        else:
            current.append(paragraph)
            current_length += separator_length + len(paragraph)

    if current:
        chunks.append("\n\n".join(current))
    return chunks


def split_into_chunks(text: str) -> tuple[str, ...]:
    sections = [
        section.strip()
        for section in re.split(r"(?=^##\s+)", text, flags=re.MULTILINE)
        if section.strip()
    ]
    chunks = [chunk for section in sections for chunk in _split_long_section(section)]
    return tuple(chunks)


def load_documents(data_dir: Path = DATA_DIR) -> tuple[Document, ...]:
    if not data_dir.is_dir():
        raise FileNotFoundError(f"Knowledge directory not found: {data_dir}")

    documents = []
    for path in sorted(data_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            continue
        chunks = split_into_chunks(text)
        if chunks:
            documents.append(Document(name=path.name, chunks=chunks))
    return tuple(documents)


DOCUMENTS = load_documents()


def get_knowledge_status() -> dict[str, object]:
    return {
        "document_count": len(DOCUMENTS),
        "chunk_count": sum(len(document.chunks) for document in DOCUMENTS),
        "documents": [
            {"name": document.name, "chunks": len(document.chunks)}
            for document in DOCUMENTS
        ],
    }
