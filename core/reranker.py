from sentence_transformers import CrossEncoder

_reranker = CrossEncoder(
        "cross-encoder/ms-marco-MiniLM-L-6-v2"
)

def rerank_documents(question: str, docs: list, top_k: int = 3):
    """
    Re-rank retrieved documents using Cross Encoder.

    Args:
        question: User question
        docs: Retrieved LangChain Documents
        top_k: Number of documents to return

    Returns:
        Top ranked documents
    """

    if not docs:
        return []

    pairs = [
        (question, doc.page_content)
        for doc in docs
    ]

    scores = _reranker.predict(pairs)

    ranked_docs = sorted(
        zip(scores,docs),
        key = lambda x:x[0],
        reverse= True
    )


    for doc, score in zip(docs, scores):
        print("=" * 60)
        print(f"Score: {score:.4f}")
        print(doc.page_content[:120])

    return [doc for score,doc in ranked_docs[:top_k]]