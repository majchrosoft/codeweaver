from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import asyncio
import httpx

OLLAMA_URL = "http://host.docker.internal:11434"

from app.scheduler import Scheduler, Task
from app.worker import worker_loop
from app.metrics import metrics
from app.pipeline import run_llm
from fastapi import Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import time

OLLAMA_URL = "http://host.docker.internal:11434"

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")

scheduler = Scheduler()

async def find_optimal_concurrency():
    candidates = [1, 2, 4, 6, 8]

    results = []

    for c in candidates:
        start = time.time()

        tasks = [
            run_llm({
                "model": "qwen2.5-coder:1.5b-base",
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": False
            })
            for _ in range(c)
        ]

        await asyncio.gather(*tasks)

        duration = time.time() - start

        results.append({
            "c": c,
            "time": duration
        })

    best = min(results, key=lambda x: x["time"])

    return best

@app.on_event("startup")
async def startup():
    asyncio.create_task(worker_loop(scheduler))
@app.post("/api/chat")
async def ollama_chat(request: Request):
    data = await request.json()

    # 🔥 debug
    print("OLLAMA CHAT REQUEST:", data)

    messages = data.get("messages")

    # fallback jeśli ktoś używa prompt zamiast messages
    if not messages and "prompt" in data:
        messages = [
            {"role": "user", "content": data["prompt"]}
        ]

    if not messages:
        return {"error": "No messages"}

    # 🔥 używamy Twojego scheduler
    try:
        # Include all relevant fields from data into payload
        payload = {
            "model": data.get("model", "qwen2.5-coder:1.5b-base"),
            "messages": messages,
            "stream": False # Ensure non-streaming for now as run_llm doesn't handle streams
        }
        
        # Define allowed Ollama /api/chat parameters
        # reference: https://github.com/ollama/ollama/blob/main/docs/api.md#generate-a-chat-completion
        allowed_params = [
            "format", "options", "stream", "keep_alive", "tools"
        ]
        
        for param in allowed_params:
            if param in data:
                # We still override stream to False because run_llm expects it
                if param == "stream":
                    payload["stream"] = False
                elif param == "options" and not isinstance(data[param], dict):
                    # Skip invalid options
                    continue
                else:
                    payload[param] = data[param]
            
        print(f"OLLAMA FINAL PAYLOAD: {payload}")
        result = await run_llm(payload)
    except Exception as e:
        print(f"Error calling run_llm: {e}")
        return {"error": str(e)}

    return {
        "message": {
            "role": "assistant",
            "content": result
        }
    }

@app.post("/v1/chat/completions")
async def chat(req: Request):
    body = await req.json()
    messages = body.get("messages", [])

    payload = {
        "model": body.get("model", "qwen2.5-coder:1.5b-base"),
        "messages": messages,
        "stream": False
    }

    # Define allowed Ollama /api/chat parameters to pass through
    allowed_params = [
        "format", "options", "stream", "keep_alive", "tools"
    ]
    
    for param in allowed_params:
        if param in body:
            if param == "stream":
                payload["stream"] = False
            elif param == "options" and not isinstance(body[param], dict):
                continue
            else:
                payload[param] = body[param]

    task = Task(payload)
    await scheduler.add_task(task)

    result = await task.future

    return {
        "choices": [
            {
                "message": {
                    "content": result
                }
            }
        ]
    }

@app.get("/dashboard")
async def dashboard():
    return FileResponse("app/static/dashboard.html")

@app.post("/benchmark")
async def benchmark(n: int = Query(5)):
    from app.pipeline import run_llm

    test_payload = {
        "model": "qwen2.5-coder:1.5b-base",
        "messages": [{"role": "user", "content": "Explain quicksort in 2 sentences"}],
        "stream": False
    }

    start = time.time()

    tasks = [
        run_llm(test_payload)
        for _ in range(n)
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    duration = time.time() - start

    # Check for failures
    failures = [r for r in results if isinstance(r, Exception)]

    return {
        "requests": n,
        "total_time": duration,
        "avg_time": duration / n,
        "failures": len(failures),
        "errors": [str(f) for f in failures[:5]]
    }


@app.post("/autotune")
async def autotune(data: dict):
    from app.worker import set_concurrency

    concurrency = data.get("concurrency")

    # manual
    if concurrency:
        set_concurrency(int(concurrency))
        return {
            "mode": "manual",
            "concurrency": concurrency
        }

    # auto
    try:
        best = await find_optimal_concurrency()
        set_concurrency(best["c"])
    except Exception as e:
        print(f"Error during autotune: {e}")
        return {"error": str(e)}

    return {
        "mode": "auto",
        "optimal_concurrency": best["c"]
    }

@app.get("/metrics")
async def get_metrics():
    return {
        "queue_size": metrics.queue_size,
        "tokens_in_flight": metrics.tokens_in_flight,
        "concurrency": metrics.concurrency,
        "last_batch_size": metrics.last_batch_size,
        "tasks": metrics.tasks[-20:],       # 🔥 ostatnie taski
        "batches": metrics.batches[-10:]    # 🔥 ostatnie batche
    }
from fastapi import Request
from fastapi.responses import Response
import httpx

OLLAMA_URL = "http://host.docker.internal:11434"


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_all(request: Request, path: str):
    url = f"{OLLAMA_URL}/{path}"

    async with httpx.AsyncClient() as client:
        body = await request.body()

        headers = dict(request.headers)
        headers.pop("host", None)

        resp = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
            params=request.query_params
        )

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=dict(resp.headers)
    )
