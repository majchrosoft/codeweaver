import asyncio
import httpx

llm_lock = asyncio.Lock()

client = httpx.AsyncClient(timeout=120)

async def run_llm(payload):
    print(f"DEBUG: OLLAMA REQUEST PAYLOAD: {payload}")
    async with llm_lock:
        response = await client.post(
            "http://host.docker.internal:11434/api/chat",
            json=payload,
        )
        if response.status_code != 200:
            error_msg = f"OLLAMA API ERROR: {response.status_code} - {response.text}"
            print(error_msg)
            raise Exception(error_msg)
        return response.json()["message"]["content"]
