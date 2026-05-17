from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check():
    """Health check endpoint"""

    return {
        "status": "healthy"
    }


@router.post("/upload")
def upload_document(file_name: str):
    """Upload a document to DocuMind"""

    return {
        "message": f"Uploaded {file_name} successfully"
    }


@router.post("/query")
def query_documents(query: str):
    """Query semantic search system"""

    return {
        "query": query,
        "results": []
    }