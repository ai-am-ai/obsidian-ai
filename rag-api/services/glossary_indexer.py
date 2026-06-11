import re
import hashlib
import os
import chromadb
import httpx
from config import CHROMA_HOST, CHROMA_PORT, VAULT_PATH, OLLAMA_BASE_URL, EMBED_MODEL

GLOSSARY_COLLECTION = "definitions"
GLOSSARY_FILE = "Словарь.md"

def get_chroma_client():
    return chromadb.HttpClient(
        host=CHROMA_HOST, port=CHROMA_PORT,
        tenant="default_tenant", database="default_database"
    )

def parse_glossary(text: str) -> list[dict]:
    entries = []
    pattern = re.compile(
        r'^\*{0,2}([A-Za-zА-Яа-яЁё0-9\s\(\)\.]+)\*{0,2}[ \t]*[-–—][ \t]*(.+)',
        re.MULTILINE
    )
    for match in pattern.finditer(text):
        term = match.group(1).strip()
        definition = match.group(2).strip()
        if len(term) < 2 or len(definition) < 5:
            continue
        entries.append({"term": term, "definition": definition})
    return entries

def index_glossary():
    glossary_path = os.path.join(VAULT_PATH, GLOSSARY_FILE)
    if not os.path.exists(glossary_path):
        return {"status": "error", "message": f"{GLOSSARY_FILE} not found"}

    with open(glossary_path, encoding="utf-8") as f:
        text = f.read()

    entries = parse_glossary(text)
    if not entries:
        return {"status": "error", "message": "No entries parsed"}

    client = get_chroma_client()
    try:
        client.delete_collection(GLOSSARY_COLLECTION)
    except Exception:
        pass
    collection = client.create_collection(
        GLOSSARY_COLLECTION,
        embedding_function=None
    )

    seen = set()
    ids, documents, metadatas = [], [], []
    for entry in entries:
        chunk_id = hashlib.md5(
            (entry["term"] + "::" + entry["definition"]).encode()
        ).hexdigest()
        if chunk_id in seen:
            continue
        seen.add(chunk_id)
        ids.append(chunk_id)
        documents.append(f"{entry['term']} — {entry['definition']}")
        metadatas.append({
            "file_name": GLOSSARY_FILE,
            "term": entry["term"]
        })

    embeddings = []
    for doc in documents:
        resp = httpx.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": doc},
            timeout=60
        )
        embeddings.append(resp.json()["embedding"])

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )
    return {
        "status": "ok",
        "indexed": len(entries),
        "terms": [e["term"] for e in entries]
    }

if __name__ == "__main__":
    result = index_glossary()
    print(result)
