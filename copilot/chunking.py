from __future__ import annotations

import re
from copy import deepcopy
from pathlib import Path
from typing import List

from langchain_core.documents import Document


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_by_headings(content: str) -> list[dict[str, str]]:
    """
    Split markdown content into sections using headings.
    If text appears before the first heading, store it under 'Introduction'.
    """
    lines = content.split("\n")
    heading_pattern = re.compile(r"^(#{1,6})\s+(.*)$")

    sections: list[dict[str, str]] = []
    current_heading = "Introduction"
    current_lines: list[str] = []

    for line in lines:
        match = heading_pattern.match(line.strip())
        if match:
            if current_lines:
                section_text = clean_text("\n".join(current_lines))
                if section_text:
                    sections.append(
                        {
                            "section_title": current_heading,
                            "text": section_text,
                        }
                    )
            current_heading = match.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        section_text = clean_text("\n".join(current_lines))
        if section_text:
            sections.append(
                {
                    "section_title": current_heading,
                    "text": section_text,
                }
            )

    return sections


def chunk_text_by_words(
    text: str,
    section_title: str,
    target_words: int = 180,
    overlap_words: int = 30,
) -> list[dict[str, str]]:
    """
    Chunk one section into overlapping word windows.
    If the section is already short, keep it as one chunk.
    """
    words = text.split()

    if len(words) <= target_words:
        return [{"section_title": section_title, "chunk_text": text}]

    chunks: list[dict[str, str]] = []
    start = 0

    while start < len(words):
        end = min(start + target_words, len(words))
        chunk_words = words[start:end]
        chunk_text = " ".join(chunk_words).strip()

        if chunk_text:
            chunks.append(
                {
                    "section_title": section_title,
                    "chunk_text": chunk_text,
                }
            )

        if end == len(words):
            break

        start = end - overlap_words

    return chunks


def build_chunked_documents(
    docs: List[Document],
    target_words: int = 180,
    overlap_words: int = 30,
) -> List[Document]:
    """
    Convert source documents into heading-aware chunked LangChain Documents.
    Preserves source metadata and adds chunk-level metadata.
    """
    chunked_docs: List[Document] = []

    for doc in docs:
        source_text = clean_text(doc.page_content)
        if not source_text:
            continue

        sections = split_by_headings(source_text)

        file_name = doc.metadata.get("file_name", "unknown.md")
        file_stem = Path(file_name).stem

        for section_index, section in enumerate(sections):
            chunked_sections = chunk_text_by_words(
                text=section["text"],
                section_title=section["section_title"],
                target_words=target_words,
                overlap_words=overlap_words,
            )

            for chunk_index, chunk in enumerate(chunked_sections):
                chunk_id = f"{file_stem}__sec{section_index:02d}__chunk{chunk_index:02d}"

                metadata = deepcopy(doc.metadata)
                metadata.update(
                    {
                        "chunk_id": chunk_id,
                        "section_title": chunk["section_title"],
                        "section_index": section_index,
                        "chunk_index": chunk_index,
                        "word_count": len(chunk["chunk_text"].split()),
                    }
                )

                chunked_docs.append(
                    Document(
                        page_content=chunk["chunk_text"],
                        metadata=metadata,
                    )
                )

    return chunked_docs