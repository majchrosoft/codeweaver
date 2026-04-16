import asyncio
from app.scheduler import Scheduler
from app.pipeline import run_llm
from app.metrics import metrics

import asyncio
from app.metrics import metrics

semaphore = asyncio.Semaphore(metrics.concurrency)
def set_concurrency(n: int):
    global semaphore

    metrics.concurrency = n
    semaphore = asyncio.Semaphore(n)


async def run_with_limit(messages):
    async with semaphore:
        return await run_llm(messages)


async def worker_loop(scheduler: Scheduler):
    while True:
        batch = await scheduler.get_batch()

        if not batch:
            await asyncio.sleep(0.01)
            continue

        tasks = [
            run_with_limit(task.messages)
            for task in batch
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for task, result in zip(batch, results):
            if isinstance(result, Exception):
                task.future.set_result(str(result))
            else:
                task.future.set_result(result)

            for mt in metrics.tasks:
                if mt["id"] == task.id:
                    mt["status"] = "done"

        # 🔥 KLUCZOWE
        await scheduler.release_tokens(batch)
