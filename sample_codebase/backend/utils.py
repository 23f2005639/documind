import os


def chunk_text(text: str, chunk_size: int = 500):
    """Split large text into smaller chunks"""

    chunks = []

    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])

    return chunks


def get_file_extension(file_name: str):
    """Return file extension"""

    return os.path.splitext(file_name)[1]

# Made with Bob