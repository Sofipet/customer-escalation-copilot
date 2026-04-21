from __future__ import annotations

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from copilot.utils import load_markdown_documents

PERSIST_DIRECTORY = "data/artifacts/chroma_db"
COLLECTION_NAME = "customer_escalation_copilot"


def main() -> None:
    docs = load_markdown_documents()
    print(f"Loaded {len(docs)} markdown documents.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    splits = splitter.split_documents(docs)
    print(f"Created {len(splits)} chunks.")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=PERSIST_DIRECTORY,
    )

    print(f"Saved Chroma collection to {PERSIST_DIRECTORY}")
    print(f"Stored chunks: {vectorstore._collection.count()}")


if __name__ == "__main__":
    main()