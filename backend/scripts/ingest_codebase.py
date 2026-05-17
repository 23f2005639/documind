# scripts/ingest_codebase.py
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import asyncio

from app.services.embedding import embedding_service
from app.services.vector_store import vector_store

SUPPORTED_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".md"}

SKIP_DIRS = {
    "node_modules", ".venv", "__pycache__", ".git",
    "qdrant_storage", ".mypy_cache", "dist", "build",
    ".next", "coverage", ".pytest_cache",
}


async def ingest():
    base_path = Path(__file__).resolve().parent.parent.parent  # project root
    print(f"Indexing from: {base_path}")

    embedding_service._load_model()

    documents = []

    for file_path in base_path.rglob("*"):
        # Skip unwanted directories
        if any(skip in file_path.parts for skip in SKIP_DIRS):
            continue
        if file_path.suffix not in SUPPORTED_EXTENSIONS:
            continue
        if not file_path.is_file():
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            if not content.strip():
                continue

            rel_path = str(file_path.relative_to(base_path))
            chunk_size = 1500
            overlap = 200

            for i in range(0, len(content), chunk_size - overlap):
                chunk = content[i:i + chunk_size]
                if not chunk.strip():
                    continue

                documents.append({
                    "doc_id": f"{rel_path}:chunk{i // (chunk_size - overlap)}",
                    "content": chunk,
                    "metadata": {
                        "file_name": file_path.name,
                        "file_path": rel_path,
                        "chunk_index": i // (chunk_size - overlap),
                        "type": "code" if file_path.suffix != ".md" else "documentation",
                        "language": file_path.suffix.lstrip("."),
                    }
                })

        except Exception as e:
            print(f"  Skipped {file_path}: {e}")

    print(f"Total chunks to index: {len(documents)}")

    await vector_store.initialize_collection()

    batch_size = 32
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        await vector_store.index_documents_batch(batch)
        print(f"  Indexed {min(i + batch_size, len(documents))} / {len(documents)}")

    print("Ingestion complete!")


if __name__ == "__main__":
    asyncio.run(ingest())
