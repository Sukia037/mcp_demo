"""Small, explainable keyword retriever for the prepared local documents."""

import math
import re
from collections import Counter
from dataclasses import dataclass

from knowledge import DOCUMENTS


TOKEN_PATTERN = re.compile(
    r"[a-zA-Z]+(?:'[a-zA-Z]+)?|\d+(?:\.\d+)?|[\u3400-\u4dbf\u4e00-\u9fff]+"
)
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "do",
    "does",
    "for",
    "from",
    "how",
    "i",
    "if",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "was",
    "what",
    "when",
    "where",
    "which",
    "why",
    "with",
}


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for token in TOKEN_PATTERN.findall(text.lower()):
        if re.fullmatch(r"[\u3400-\u4dbf\u4e00-\u9fff]+", token):
            tokens.append(token)
            tokens.extend(token[index : index + 2] for index in range(len(token) - 1))
        elif token not in STOP_WORDS and len(token) > 1:
            tokens.append(token)
    return tokens


@dataclass(frozen=True)
class IndexedChunk:
    source: str
    chunk_number: int
    text: str
    term_counts: Counter[str]


INDEXED_CHUNKS = tuple(
    IndexedChunk(
        source=document.name,
        chunk_number=chunk_number,
        text=chunk,
        term_counts=Counter(tokenize(chunk)),
    )
    for document in DOCUMENTS
    for chunk_number, chunk in enumerate(document.chunks, start=1)
)

DOCUMENT_FREQUENCIES = Counter(
    token
    for chunk in INDEXED_CHUNKS
    for token in chunk.term_counts
)


def _score(query_terms: Counter[str], chunk: IndexedChunk) -> float:
    matched_terms = query_terms.keys() & chunk.term_counts.keys()
    if not matched_terms:
        return 0.0

    total_chunks = len(INDEXED_CHUNKS)
    weighted_matches = sum(
        query_terms[term]
        * (1.0 + math.log(chunk.term_counts[term]))
        * (math.log((total_chunks + 1) / (DOCUMENT_FREQUENCIES[term] + 1)) + 1.0)
        for term in matched_terms
    )
    coverage = len(matched_terms) / len(query_terms)
    length_normalizer = math.sqrt(max(sum(chunk.term_counts.values()), 1))
    return weighted_matches / length_normalizer + (2.0 * coverage)


def search_documents(question: str, limit: int = 3) -> dict[str, object]:
    question = question.strip()
    query_terms = Counter(tokenize(question))
    if not question or not query_terms:
        return {
            "query": question,
            "matches": [],
            "message": "Please enter a question with searchable words.",
        }

    ranked = sorted(
        (
            (_score(query_terms, chunk), chunk)
            for chunk in INDEXED_CHUNKS
        ),
        key=lambda item: (-item[0], item[1].source, item[1].chunk_number),
    )
    matches = [
        {
            "source": chunk.source,
            "chunk": chunk.chunk_number,
            "score": round(score, 4),
            "content": chunk.text,
        }
        for score, chunk in ranked[: max(limit, 0)]
        if score > 0
    ]

    return {
        "query": question,
        "matches": matches,
        "message": None if matches else "No sufficiently relevant content was found.",
    }
