import httpx

OLLAMA_URL = "http://172.17.0.1:11434/api/chat"

async def run_llm(messages):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            OLLAMA_URL,
            json={
                "model": "deepseek-coder:6.7b",
                "messages": messages,
                "stream": False
            }
        )
    data = response.json()
    return data.get("message", {}).get("content", "")
