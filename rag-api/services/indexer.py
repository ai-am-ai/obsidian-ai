import hashlib
import chromadb
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.ollama import OllamaEmbedding
from config import (
    OLLAMA_BASE_URL, CHROMA_HOST, CHROMA_PORT,
    COLLECTION_NAME, EMBED_MODEL, VAULT_PATH
)

def make_chunk_id(file_name: str, content: str) -> str:
    raw = f"{file_name}::{content}"
    return hashlib.md5(raw.encode()).hexdigest()

def build_index():
    embed_model = OllamaEmbedding(
        model_name=EMBED_MODEL,
        base_url=OLLAMA_BASE_URL
    )
    documents = SimpleDirectoryReader(
        input_dir=VAULT_PATH,
        required_exts=[".md"],
        recursive=True
    ).load_data()

    splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    chunks = splitter.get_nodes_from_documents(documents)

    client = chromadb.HttpClient(
        host=CHROMA_HOST,
        port=CHROMA_PORT,
        tenant="default_tenant",
        database="default_database"
    )
    collection = client.get_or_create_collection(COLLECTION_NAME)

    ids, texts, embeddings, metadatas = [], [], [], []
    for chunk in chunks:
        file_name = chunk.metadata.get("file_name", "unknown")
        content = chunk.get_content()
        chunk_id = make_chunk_id(file_name, content)
        embedding = embed_model.get_text_embedding(content)

        ids.append(chunk_id)
        texts.append(content)
        embeddings.append(embedding)
        metadatas.append({"file_name": file_name})

    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )
    return {
        "status": "ok",
        "documents_indexed": len(documents),
        "chunks": len(chunks)
    }