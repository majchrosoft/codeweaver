from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import asyncio
import httpx

OLLAMA_URL = "http://host.docker.internal:11434"

from app.scheduler import Scheduler, Task
from app.worker import worker_loop
from app.metrics import metrics
from app.pipeline import run_llm
from app.caveman import apply_caveman
import app.caveman as caveman
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

    # apply caveman if enabled
    messages = caveman.apply_caveman(list(messages))

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
            "format", "options", "keep_alive", "tools", "num_predict"
        ]
        
        for param in allowed_params:
            if param in data:
                if param == "options" and not isinstance(data[param], dict):
                    # Skip invalid options
                    continue
                else:
                    payload[param] = data[param]
            
        print(f"OLLAMA FINAL PAYLOAD: {payload}")

        task = Task(payload)
        await scheduler.add_task(task)
        result = await task.future
    except Exception as e:
        print(f"Error in ollama_chat: {e}")
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

    if not messages:
        return {"error": "No messages"}

    # apply caveman if enabled
    messages = caveman.apply_caveman(list(messages))

    # We use basic payload to match initial working state
    payload = {
        "model": body.get("model", "qwen2.5-coder:1.5b-base"),
        "messages": messages,
        "stream": False
    }

    # Extract keep_alive if present
    if "keep_alive" in body:
        payload["keep_alive"] = body["keep_alive"]

    # If the request contains OpenAI specific fields, we can still map some of them
    # But only into the 'options' sub-dictionary if they exist.
    options = {}
    
    openai_to_ollama = {
        "temperature": "temperature",
        "top_p": "top_p",
        "max_tokens": "num_predict",
        "presence_penalty": "presence_penalty",
        "frequency_penalty": "frequency_penalty"
    }
    
    for openai_param, ollama_opt in openai_to_ollama.items():
        if openai_param in body:
            options[ollama_opt] = body[openai_param]

    # Map other possible Ollama options directly if they are in body["options"]
    if "options" in body and isinstance(body["options"], dict):
        options.update(body["options"])

    if options:
        payload["options"] = options

    # Map other top-level Ollama params if they are in body
    allowed_top_params = ["format", "keep_alive", "tools", "num_predict"]
    for param in allowed_top_params:
        if param in body:
            payload[param] = body[param]

    print(f"DEBUG: V1 FINAL PAYLOAD: {payload}")

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
    caveman_input = data.get("caveman_input")
    caveman_output = data.get("caveman_output")

    response = {"mode": "manual"}

    # concurrency
    if concurrency is not None:
        set_concurrency(int(concurrency))
        response["concurrency"] = concurrency
    else:
        # auto if concurrency is null/not provided
        try:
            best = await find_optimal_concurrency()
            set_concurrency(best["c"])
            response["mode"] = "auto"
            response["optimal_concurrency"] = best["c"]
        except Exception as e:
            print(f"Error during autotune: {e}")
            return {"error": str(e)}

    # caveman
    if caveman_input is not None:
        caveman.CAVEMAN_INPUT_ENABLED = bool(caveman_input)
        response["caveman_input"] = caveman.CAVEMAN_INPUT_ENABLED

    if caveman_output is not None:
        caveman.CAVEMAN_OUTPUT_ENABLED = bool(caveman_output)
        response["caveman_output"] = caveman.CAVEMAN_OUTPUT_ENABLED

    return response

@app.get("/metrics")
async def get_metrics():
    return {
        "queue_size": metrics.queue_size,
        "tokens_in_flight": metrics.tokens_in_flight,
        "concurrency": metrics.concurrency,
        "last_batch_size": metrics.last_batch_size,
        "caveman_input_enabled": caveman.CAVEMAN_INPUT_ENABLED,
        "caveman_output_enabled": caveman.CAVEMAN_OUTPUT_ENABLED,
        "tasks": metrics.tasks[-20:],       # 🔥 ostatnie taski
        "batches": metrics.batches[-10:]    # 🔥 ostatnie batche
    }
from fastapi.responses import Response, StreamingResponse
from app.pipeline import client

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_all(request: Request, path: str):
    url = f"{OLLAMA_URL}/{path}"

    try:
        body = await request.body()
        headers = dict(request.headers)
        headers.pop("host", None)
        headers.pop("content-length", None)

        req = client.build_request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
            params=request.query_params
        )
        resp = await client.send(req, stream=True)
        
        async def iterate_and_close():
            try:
                async for chunk in resp.aiter_raw():
                    yield chunk
            finally:
                await resp.aclose()

        return StreamingResponse(
            iterate_and_close(),
            status_code=resp.status_code,
            headers=dict(resp.headers)
        )
    except Exception as e:
        print(f"Proxy error for {path}: {e}")
        return Response(content=str(e), status_code=502)
