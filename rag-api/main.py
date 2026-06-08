import chromadb
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from services.indexer import build_index
from services.retriever import get_answer
from config import CHROMA_HOST, CHROMA_PORT, COLLECTION_NAME

app = FastAPI()

class QuestionRequest(BaseModel):
    question: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/status")
def status():
    try:
        client = chromadb.HttpClient(
            host=CHROMA_HOST,
            port=CHROMA_PORT,
            tenant="default_tenant",
            database="default_database"
        )
        collection = client.get_or_create_collection(COLLECTION_NAME)
        count = collection.count()
        return {"status": "ok", "documents_in_collection": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index")
def index():
    try:
        result = build_index()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
def ask(request: QuestionRequest):
    try:
        answer = get_answer(request.question)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))