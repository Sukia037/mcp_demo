"""Build a small, deterministic answer from retrieved local context."""

from retrieval import search_documents


NO_ANSWER_MESSAGE = (
    "I could not find enough relevant information in the local documents."
)


def answer_question(question: str) -> dict[str, object]:
    retrieval = search_documents(question, limit=3)
    matches = retrieval["matches"]
    if not matches:
        return {
            "question": question.strip(),
            "answer": NO_ANSWER_MESSAGE,
            "sources": [],
        }

    most_relevant = matches[0]
    answer = (
        "Based on the most relevant local lecture section:\n\n"
        f"{most_relevant['content']}"
    )
    sources = [
        {
            "name": match["source"],
            "chunk": match["chunk"],
            "score": match["score"],
        }
        for match in matches
    ]
    return {
        "question": question.strip(),
        "answer": answer,
        "sources": sources,
    }

