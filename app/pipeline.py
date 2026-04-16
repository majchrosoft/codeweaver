import asyncio
import httpx

llm_lock = asyncio.Lock()

client = httpx.AsyncClient(timeout=120)

async def run_llm(payload):
    async with llm_lock:
        response = await client.post(
            "http://host.docker.internal:11434/api/chat",
            json=payload,
        )
        response.raise_for_status()
        return response.json()["message"]["content"]
