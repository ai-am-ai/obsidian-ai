import os
import json
import hashlib
import chromadb
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.ollama import OllamaEmbedding
from config import (
    OLLAMA_BASE_URL, CHROMA_HOST, CHROMA_PORT,
    COLLECTION_NAME, EMBED_MODEL, VAULT_PATH, MANIFEST_PATH
)

def make_chunk_id(file_name: str, content: str) -> str:
    return hashlib.md5(f"{file_name}::{content}".encode()).hexdigest()

def load_manifest() -> dict:
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, "r") as f:
            return json.load(f)
    return {}

def save_manifest(manifest: dict):
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)

def get_vault_files() -> dict:
    """Возвращает {file_name: mtime} для всех .md файлов в vault"""
    result = {}
    for fname in os.listdir(VAULT_PATH):
        if fname.endswith(".md"):
            fpath = os.path.join(VAULT_PATH, fname)
            result[fname] = os.path.getmtime(fpath)
    return result

def index_file(file_name: str, client, collection, embed_model, splitter) -> list:
    """Индексирует один файл, возвращает список chunk_id"""
    fpath = os.path.join(VAULT_PATH, file_name)
    documents = SimpleDirectoryReader(
        input_files=[fpath]
    ).load_data()

    chunks = splitter.get_nodes_from_documents(documents)

    ids, texts, embeddings, metadatas = [], [], [], []
    for chunk in chunks:
        content = chunk.get_content()
        chunk_id = make_chunk_id(file_name, content)
        embedding = embed_model.get_text_embedding(content)

        ids.append(chunk_id)
        texts.append(content)
        embeddings.append(embedding)
        metadatas.append({"file_name": file_name})

    if ids:
        collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )
    return ids

def build_index():
    embed_model = OllamaEmbedding(
        model_name=EMBED_MODEL,
        base_url=OLLAMA_BASE_URL
    )
    splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    client = chromadb.HttpClient(
        host=CHROMA_HOST,
        port=CHROMA_PORT,
        tenant="default_tenant",
        database="default_database"
    )
    collection = client.get_or_create_collection(COLLECTION_NAME)

    manifest = load_manifest()
    vault_files = get_vault_files()

    stats = {"indexed": [], "skipped": [], "deleted": [], "updated": []}

    # Удалить чанки файлов которых больше нет в vault
    for file_name in list(manifest.keys()):
        if file_name not in vault_files:
            old_ids = manifest[file_name].get("chunk_ids", [])
            if old_ids:
                collection.delete(ids=old_ids)
            del manifest[file_name]
            stats["deleted"].append(file_name)

    # Индексировать новые и изменённые файлы
    for file_name, mtime in vault_files.items():
        in_manifest = file_name in manifest
        mtime_changed = in_manifest and manifest[file_name].get("mtime") != mtime

        if in_manifest and not mtime_changed:
            stats["skipped"].append(file_name)
            continue

        # Удалить старые чанки если файл изменился
        if mtime_changed:
            old_ids = manifest[file_name].get("chunk_ids", [])
            if old_ids:
                collection.delete(ids=old_ids)
            stats["updated"].append(file_name)
        else:
            stats["indexed"].append(file_name)

        # Индексировать файл
        chunk_ids = index_file(file_name, client, collection, embed_model, splitter)
        manifest[file_name] = {"mtime": mtime, "chunk_ids": chunk_ids}

    save_manifest(manifest)

    return {
        "status": "ok",
        "indexed": stats["indexed"],
        "updated": stats["updated"],
        "skipped": stats["skipped"],
        "deleted": stats["deleted"],
        "total_in_collection": collection.count()
    }