from __future__ import annotations

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from copilot.reranking import rerank_docs
from copilot.retrieval_config import (
    EMBEDDING_MODEL,
    FINAL_TOP_K,
    STRUCTURED_COLLECTION_NAME,
    STRUCTURED_INDEX_DIR,
)

from copilot.tracing import traceable

def get_vectorstore() -> Chroma:
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    return Chroma(
        collection_name=STRUCTURED_COLLECTION_NAME,
        persist_directory=str(STRUCTURED_INDEX_DIR),
        embedding_function=embeddings,
    )


def dense_recall(query: str, k: int = 10):
    vectorstore = get_vectorstore()
    return vectorstore.similarity_search(query, k=k)


@traceable(name="retrieve_and_rerank", run_type="retriever")
def retrieve_and_rerank(query: str, initial_k: int = 10, final_k: int = FINAL_TOP_K):
    initial_docs = dense_recall(query, k=initial_k)
    reranked = rerank_docs(initial_docs, query)
    return reranked[:final_k]