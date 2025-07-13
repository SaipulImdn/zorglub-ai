import requests

def ask_gpt(prompt: str) -> str:
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": "deepseek-r1",
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    data = response.json()
    return data['message']['content']
