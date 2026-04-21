from __future__ import annotations

from pathlib import Path
from typing import List

import frontmatter
from langchain_core.documents import Document

RAW_DATA_DIR = Path("data/raw")


def load_markdown_documents(root: Path = RAW_DATA_DIR) -> List[Document]:
    docs: List[Document] = []

    for file_path in sorted(root.rglob("*.md")):
        post = frontmatter.load(file_path)

        metadata = {
            "source": str(file_path),
            "file_name": file_path.name,
            "title": post.get("title"),
            "document_type": post.get("document_type"),
            "version": post.get("version"),
            "date": post.get("date"),
            "region": post.get("region"),
            "product_area": post.get("product_area"),
            "team": post.get("team"),
            "source_authority": post.get("source_authority"),
        }

        content = post.content.strip()
        if not content:
            continue

        docs.append(Document(page_content=content, metadata=metadata))

    return docs