import asyncio
import httpx

llm_lock = asyncio.Lock()

client = httpx.AsyncClient(
    timeout=httpx.Timeout(120.0, connect=10.0, read=110.0, write=10.0),
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    # Some local servers might have issues with HTTP/2, sticking to 1.1 for stability
    http2=False
)

async def run_llm(payload):
    print(f"DEBUG: OLLAMA REQUEST PAYLOAD: {payload}")
    async with llm_lock:
        try:
            response = await client.post(
                "http://host.docker.internal:11434/api/chat",
                json=payload,
            )
            if response.status_code != 200:
                error_msg = f"OLLAMA API ERROR: {response.status_code} - {response.text}"
                print(error_msg)
                raise Exception(error_msg)
            
            data = response.json()
            if "message" not in data or "content" not in data["message"]:
                error_msg = f"OLLAMA API ERROR: Missing 'message' or 'content' in response: {data}"
                print(error_msg)
                raise Exception(error_msg)
                
            return data["message"]["content"]
        except httpx.HTTPError as e:
            error_msg = f"OLLAMA HTTP ERROR: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"OLLAMA UNKNOWN ERROR: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
