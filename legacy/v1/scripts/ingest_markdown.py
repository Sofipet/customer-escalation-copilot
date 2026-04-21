from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import frontmatter
from tqdm import tqdm


RAW_DATA_DIR = Path("data/raw")
OUTPUT_PATH = Path("data/processed/chunks.jsonl")


def get_all_markdown_files(root: Path) -> list[Path]:
    return sorted(root.rglob("*.md"))


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_document(file_path: Path) -> dict[str, Any]:
    post = frontmatter.load(file_path)

    metadata = {
        "title": post.get("title"),
        "document_type": post.get("document_type"),
        "version": post.get("version"),
        "date": post.get("date"),
        "region": post.get("region"),
        "product_area": post.get("product_area"),
        "team": post.get("team"),
        "source_authority": post.get("source_authority"),
    }

    content = clean_text(post.content)

    return {
        "file_path": str(file_path),
        "file_name": file_path.name,
        "metadata": metadata,
        "content": content,
    }


def split_by_headings(content: str) -> list[dict[str, str]]:
    """
    Splits markdown text into sections using headings.
    Keeps the heading with its content.
    """
    lines = content.split("\n")

    sections: list[dict[str, str]] = []
    current_heading = "Introduction"
    current_lines: list[str] = []

    heading_pattern = re.compile(r"^(#{1,6})\s+(.*)$")

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


def estimate_word_count(text: str) -> int:
    return len(text.split())


def chunk_section_text(
    text: str,
    section_title: str,
    target_words: int = 180,
    overlap_words: int = 30,
) -> list[dict[str, str]]:
    """
    Simple chunker by words.
    We first split by headings, then further split large sections into overlapping chunks.
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


def build_chunks_for_document(document: dict[str, Any]) -> list[dict[str, Any]]:
    sections = split_by_headings(document["content"])
    output_chunks: list[dict[str, Any]] = []

    for section_index, section in enumerate(sections):
        section_title = section["section_title"]
        section_text = section["text"]

        chunked_sections = chunk_section_text(
            text=section_text,
            section_title=section_title,
            target_words=180,
            overlap_words=30,
        )

        for chunk_index, chunk in enumerate(chunked_sections):
            chunk_id = (
                f"{Path(document['file_name']).stem}"
                f"__sec{section_index:02d}"
                f"__chunk{chunk_index:02d}"
            )

            output_chunks.append(
                {
                    "chunk_id": chunk_id,
                    "file_name": document["file_name"],
                    "file_path": document["file_path"],
                    "section_title": chunk["section_title"],
                    "chunk_text": chunk["chunk_text"],
                    "word_count": estimate_word_count(chunk["chunk_text"]),
                    **document["metadata"],
                }
            )

    return output_chunks


def validate_metadata(chunk: dict[str, Any]) -> list[str]:
    required_fields = [
        "title",
        "document_type",
        "version",
        "date",
        "region",
        "product_area",
        "team",
        "source_authority",
    ]
    missing = [field for field in required_fields if not chunk.get(field)]
    return missing


def main() -> None:
    files = get_all_markdown_files(RAW_DATA_DIR)

    if not files:
        raise FileNotFoundError(f"No markdown files found under {RAW_DATA_DIR}")

    all_chunks: list[dict[str, Any]] = []
    invalid_chunks: list[dict[str, Any]] = []

    for file_path in tqdm(files, desc="Processing markdown files"):
        doc = parse_document(file_path)
        chunks = build_chunks_for_document(doc)

        for chunk in chunks:
            missing_fields = validate_metadata(chunk)
            if missing_fields:
                invalid_chunks.append(
                    {
                        "chunk_id": chunk["chunk_id"],
                        "file_name": chunk["file_name"],
                        "missing_fields": missing_fields,
                    }
                )

        all_chunks.extend(chunks)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    print(f"\nSaved {len(all_chunks)} chunks to {OUTPUT_PATH}")

    if invalid_chunks:
        print(f"\nFound {len(invalid_chunks)} chunks with missing metadata:")
        for item in invalid_chunks[:10]:
            print(item)
    else:
        print("\nAll chunks have complete metadata.")


if __name__ == "__main__":
    main()