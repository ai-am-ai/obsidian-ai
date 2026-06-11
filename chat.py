import requests
import json

print("RAG чат | Ctrl+C для выхода\n")

while True:
    try:
        q = input("Вопрос: ").strip()
        if not q:
            continue
        
        r = requests.post(
            "http://localhost:8080/ask",
            json={"question": q}
        )
        data = r.json()
        
        print(f"\nОтвет: {data['answer']}")
        if data.get('sources'):
            print(f"Источники: {', '.join(data['sources'])}")
        print()
        
    except KeyboardInterrupt:
        print("\nВыход")
        break
    except Exception as e:
        print(f"Ошибка: {e}\n")
