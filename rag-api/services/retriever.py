import chromadb
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from config import OLLAMA_BASE_URL, CHROMA_HOST, CHROMA_PORT, COLLECTION_NAME, EMBED_MODEL, LLM_MODEL

GLOSSARY_COLLECTION = "definitions"

def _query_collection(client, collection_name: str, embedding: list, n: int = 3):
    collection = client.get_or_create_collection(collection_name)
    results = collection.query(
        query_embeddings=[embedding],
        n_results=n
    )
    return results

def get_answer(question: str) -> str:
    embed_model = OllamaEmbedding(
        model_name=EMBED_MODEL,
        base_url=OLLAMA_BASE_URL
    )
    llm = Ollama(
        model=LLM_MODEL,
        base_url=OLLAMA_BASE_URL,
        request_timeout=120.0
    )

    question_embedding = embed_model.get_text_embedding(question)

    client = chromadb.HttpClient(
        host=CHROMA_HOST,
        port=CHROMA_PORT,
        tenant="default_tenant",
        database="default_database"
    )

    # Поиск в двух коллекциях
    manuals_results = _query_collection(client, COLLECTION_NAME, question_embedding, n=5)
    glossary_results = _query_collection(client, GLOSSARY_COLLECTION, question_embedding, n=3)

    # Объединить контекст
    manuals_docs = manuals_results.get("documents", [[]])[0]

    glossary_raw_docs = glossary_results.get("documents", [[]])[0]
    glossary_distances = glossary_results.get("distances", [[]])[0]
    glossary_docs = [
        doc for doc, dist in zip(glossary_raw_docs, glossary_distances)
        if dist < 600
    ]

    parts = []
    if glossary_docs:
        parts.append("Словарные определения:\n" + "\n".join(glossary_docs))
    if manuals_docs:
        parts.append("Техническая документация:\n" + "\n".join(manuals_docs))
    context = "\n\n".join(parts)

    # Объединить источники
    manuals_meta = manuals_results.get("metadatas", [[]])[0]
    glossary_meta = [
        meta for meta, dist in zip(
            glossary_results.get("metadatas", [[]])[0],
            glossary_distances
        )
        if dist < 600
    ]
    sources = list(set(
        m.get("file_name", "unknown") for m in manuals_meta + glossary_meta
    ))

    prompt = f"""Ты ассистент по внутренней документации компании.
Отвечай ТОЛЬКО на основе предоставленного контекста.
Если ответа нет в контексте — отвечай строго: "Информация по данному вопросу отсутствует в документации."
Не используй собственные знания.

Контекст:
{context}

Источники: {sources}

Вопрос: {question}

Ответ:"""

    response = llm.complete(prompt)
    return {"answer": str(response), "sources": sources}
