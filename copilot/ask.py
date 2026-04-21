from __future__ import annotations

from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

PERSIST_DIRECTORY = "data/artifacts/chroma_db"
COLLECTION_NAME = "customer_escalation_copilot"
PROMPT_PATH = Path("copilot/prompts/system_prompt.txt")


def format_docs(docs) -> str:
    formatted = []
    for i, doc in enumerate(docs, start=1):
        meta = doc.metadata
        formatted.append(
            f"""[Document {i}]
title: {meta.get('title')}
file_name: {meta.get('file_name')}
document_type: {meta.get('document_type')}
version: {meta.get('version')}
date: {meta.get('date')}
region: {meta.get('region')}
source_authority: {meta.get('source_authority')}

content:
{doc.page_content}
"""
        )
    return "\n\n" + ("-" * 80 + "\n\n").join(formatted)


def main() -> None:
    prompt_text = PROMPT_PATH.read_text(encoding="utf-8").strip()

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=PERSIST_DIRECTORY,
        embedding_function=embeddings,
    )

    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", prompt_text),
            ("human", "Customer escalation:\n{question}\n\nRetrieved context:\n{context}"),
        ]
    )

    rag_chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    question = input("Ask a question / paste an escalation:\n> ").strip()
    answer = rag_chain.invoke(question)

    print("\n" + "=" * 100)
    print(answer)


if __name__ == "__main__":
    main()