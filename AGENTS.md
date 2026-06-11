# AGENTS.md — Local Enterprise RAG System

## Твоя роль
Ты технический исполнитель. Все архитектурные решения принимает куратор (Claude).
Точно выполняй инструкции, генерируй отчёты по шаблону.

## Формат работы
Один шаг → жди вывода пользователя → следующий шаг.
Никогда не давай несколько шагов сразу.

Формат шага:
### Шаг N: [название]
[одна команда или действие]
Что ожидаем: [результат]

## Правило эскалации (ОБЯЗАТЕЛЬНО)
При нетривиальной проблеме:
1. СТОП — прекращаешь попытки решить самостоятельно
2. Генерируешь отчёт куратору по шаблону 🚨
3. Ждёшь нового промпта

Нетривиальная проблема:
- Несовместимость версий
- Ошибка без решения в рамках текущего кода
- 2+ неудачных попытки в одном направлении

Запрещено: предлагать варианты A/B/C пользователю — это решает куратор.

## Зафиксированный стек (не менять)
- API: FastAPI
- RAG: LlamaIndex
- Vector DB: ChromaDB 0.5.23 (клиент и сервер)
- LLM + Embeddings: Ollama
- Контейнеризация: Docker Compose
- ОС: WSL2 Ubuntu

Модели Ollama:
- LLM: qwen2.5:3b-instruct-q4_K_M
- Embeddings: bge-m3 (1024 dim)
- Чанкинг: 512 токенов, overlap 50

## Структура проекта
~/obsidian-ai/
├── docker-compose.yml
├── .gitignore
├── README.md
├── AGENTS.md
├── vault/                        # тестовые .md (не реальная база)
├── rag-api/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── config.py
│   ├── data/                     # манифест индекса (не в git)
│   └── services/
│       ├── init.py
│       ├── indexer.py
│       └── retriever.py
├── ollama_data/
├── chroma_data/
└── n8n_data/                     # не трогать

## config.py (зафиксировано)
python
OLLAMA_BASE_URL = "http://ollama:11434"
CHROMA_HOST = "chromadb"
CHROMA_PORT = 8000
COLLECTION_NAME = "manuals"
LLM_MODEL = "qwen2.5:3b-instruct-q4_K_M"
EMBED_MODEL = "bge-m3"
VAULT_PATH = "/vault"
MANIFEST_PATH = "/app/data/index_manifest.json"

## requirements.txt (зафиксировано)

fastapi
uvicorn
llama-index-core
llama-index-llms-ollama
llama-index-embeddings-ollama
llama-index-vector-stores-chroma
llama-index-readers-file==0.2.2
chromadb==0.5.23

## Docker сеть
- ai-net (все сервисы)
- ollama: 11434
- chromadb: 8000, образ chromadb/chroma:0.5.23
- rag-api: 8080
- n8n: 5678 (не трогать)

Volumes rag-api:
- /mnt/c/Users/Айдын/Desktop/mathmodelvault:/vault:ro
- ./rag-api/data:/app/data

## Ключевые архитектурные решения

### indexer.py
- Манифест: /app/data/index_manifest.json
- ID чанка: md5(file_name + "::" + content)
- Исключать: .git, Excalidraw, .obsidian папки
- Индексировать только .md файлы
- Логика: новый → индексировать, mtime не изменился → пропустить,
  mtime изменился → удалить старые чанки + переиндексировать,
  файл удалён → удалить чанки из ChromaDB

### retriever.py
- НЕ использует LlamaIndex query engine
- Прямой collection.query(query_embeddings=[...], n_results=3)
- Возвращает {"answer": "...", "sources": ["file.md"]}
- Строгий prompt: только из контекста, при отсутствии →
  "Информация по данному вопросу отсутствует в документации."

### ChromaDB клиент
python
client = chromadb.HttpClient(
    host=CHROMA_HOST,
    port=CHROMA_PORT,
    tenant="default_tenant",
    database="default_database"
)
`

## Эндпоинты API
- GET  /health  — проверка
- POST /index   — инкрементальная индексация vault
- POST /ask     — вопрос → ответ + sources
- GET  /status  — кол-во документов в ChromaDB
- GET  /        — веб-интерфейс (Блок 6, в работе)

## Статус блоков
- ✅ Блок 1 — FastAPI структура
- ✅ Блок 2 — Indexer + Retriever
- ✅ Блок 3 — Upsert + /status
- ✅ Блок Git — GitHub (git@github.com:ai-am-ai/obsidian-ai.git)
- ✅ Блок 4 — Качество ответов (строгий prompt + sources)
- ✅ Блок 5 — Инкрементальная индексация с манифестом
- 🔄 Блок 6 — Веб-интерфейс (в работе)
- 🔄 Блок 7 — Подключение реальной базы знаний

## Решённые проблемы (не повторять)
- TLS timeout → daemon.json MTU=1450, IPv4, DNS 8.8.8.8
- ChromaDB tenant error → версии клиент+сервер 0.5.23
- ChromaDB where={} → прямой collection.query()
- Сетевая изоляция → ai-net всем сервисам
- Дубли при индексации → md5(file+content) как ID
- 404 после правки → docker compose build rag-api
- Манифест в read-only vault → вынесен в /app/data/

## Git
- Репо: git@github.com:ai-am-ai/obsidian-ai.git
- Ветка: main
- После каждого блока: git add . && git commit -m "block N: ..." && git push

## Запрещено без куратора
- Менять стек, версии, структуру
- Добавлять пакеты в requirements.txt
- Рефакторить код вне задачи
- Самостоятельно решать нетривиальные проблемы

## Шаблон 🚨 эскалации
## 🚨 Эскалация куратору: Блок N — [название]
Шаг: N — [описание]
Ошибка: [полный текст]
Попытки в рамках инструкции: [что пробовал]
Гипотеза: [причина]
Требует решения куратора: [что нужно]
## Шаблон финального отчёта
## Отчёт: Блок N — [Название]
Статус: ✅ / 🔴
Что сделано: ...
Файлы созданы/изменены: ...
Результаты проверки: ...
Отклонения: ...
Доп. пакеты: ...
Ошибки и решения: ...
Текущее состояние: ...
```
