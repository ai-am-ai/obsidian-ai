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

    # Передать контекст в LLM
    prompt = f"""Используй следующий контекст для ответа на вопрос.
Если ответа нет в контексте — скажи об этом явно.

Контекст:
{context}

Вопрос: {question}

Ответ:"""

    response = llm.complete(prompt)
    return str(response)
