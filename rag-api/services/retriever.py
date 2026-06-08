import chromadb
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from config import OLLAMA_BASE_URL, CHROMA_HOST, CHROMA_PORT, COLLECTION_NAME, EMBED_MODEL, LLM_MODEL

def get_answer(question: str) -> str:
    # Инициализация моделей
    embed_model = OllamaEmbedding(
        model_name=EMBED_MODEL,
        base_url=OLLAMA_BASE_URL
    )
    llm = Ollama(
        model=LLM_MODEL,
        base_url=OLLAMA_BASE_URL,
        request_timeout=120.0
    )

    # Получить эмбеддинг вопроса
    question_embedding = embed_model.get_text_embedding(question)

    # Прямой запрос к ChromaDB без LlamaIndex (обход where={} проблемы)
    client = chromadb.HttpClient(
        host=CHROMA_HOST,
        port=CHROMA_PORT,
        tenant="default_tenant",
        database="default_database"
    )
    collection = client.get_or_create_collection(COLLECTION_NAME)
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=3
    )

    # Собрать контекст из найденных чанков
    documents = results.get("documents", [[]])[0]
    context = "\n\n".join(documents)

    # Собрать источники из метаданных
    metadatas = results.get("metadatas", [[]])[0]
    sources = list(set(m.get("file_name", "unknown") for m in metadatas))

    # Передать контекст в LLM
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
