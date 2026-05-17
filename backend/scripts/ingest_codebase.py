# scripts/ingest_codebase.py
import sys
from pathlib import Path

# Add backend root to Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import os
import asyncio
from pathlib import Path

from app.services.vector_store import vector_store


SUPPORTED_EXTENSIONS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".md",
    ".json",
}


async def ingest():
    base_path = Path("../")  # project root

    documents = []

    for file_path in base_path.rglob("*"):
        if file_path.suffix not in SUPPORTED_EXTENSIONS:
            continue

        try:
            content = file_path.read_text(encoding="utf-8")

            # simple chunking
            chunk_size = 1500

            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]

                documents.append({
                    "doc_id": str(file_path),
                    "content": chunk,
                    "metadata": {
                        "file_name": file_path.name,
                        "file_path": str(file_path),
                        "chunk_index": i // chunk_size,
                        "language": file_path.suffix,
                    }
                })

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    print(f"Total chunks: {len(documents)}")

    await vector_store.initialize_collection()

    batch_size = 32

    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]

        await vector_store.index_documents_batch(batch)

        print(f"Indexed {i + len(batch)} / {len(documents)}")

    print("Ingestion complete")


if __name__ == "__main__":
    asyncio.run(ingest())