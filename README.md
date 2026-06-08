# Local Enterprise RAG System

Офлайн self-hosted RAG-система для корпоративной документации.

## Стек
- **API**: FastAPI
- **RAG**: LlamaIndex
- **Vector DB**: ChromaDB 0.5.23
- **LLM + Embeddings**: Ollama (qwen2.5:3b + bge-m3)
- **Оркестрация**: Docker Compose

## Быстрый старт

bash
# 1. Запустить сервисы
docker compose up -d

# 2. Проиндексировать документы (положить .md файлы в vault/)
curl -X POST http://localhost:8080/index

# 3. Задать вопрос
curl -X POST http://localhost:8080/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "твой вопрос"}'

# 4. Проверить статус
curl http://localhost:8080/status


## Структура

rag-api/          # FastAPI сервис
  services/
    indexer.py    # Индексация .md файлов
    retriever.py  # Поиск + генерация ответа
vault/            # Документы (не в репо, добавить локально)


## Требования
- Docker + Docker Compose
- WSL2 (Ubuntu) или Linux
- Ollama модели: qwen2.5:3b-instruct-q4_K_M, bge-m3
