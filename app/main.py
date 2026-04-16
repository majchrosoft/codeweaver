from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import asyncio

from app.scheduler import Scheduler, Task
from app.worker import worker_loop
from app.metrics import metrics
from app.pipeline import run_llm
from fastapi import Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import time

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")

scheduler = Scheduler()

async def find_optimal_concurrency():
    candidates = [1, 2, 4, 6, 8]

    results = []

    for c in candidates:
        start = time.time()

        tasks = [
            run_llm([{"role": "user", "content": "Hello"}])
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


@app.post("/v1/chat/completions")
async def chat(req: Request):
    body = await req.json()
    messages = body.get("messages", [])

    task = Task(messages)
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

    test_prompt = [
        {"role": "user", "content": "Explain quicksort in 2 sentences"}
    ]

    start = time.time()

    tasks = [
        run_llm(test_prompt)
        for _ in range(n)
    ]

    await asyncio.gather(*tasks)

    duration = time.time() - start

    return {
        "requests": n,
        "total_time": duration,
        "avg_time": duration / n
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
    best = await find_optimal_concurrency()
    set_concurrency(best["c"])

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
