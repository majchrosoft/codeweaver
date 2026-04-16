import asyncio
import time
from app.tokens import estimate_tokens
from app.metrics import metrics
import uuid


class Task:
    def __init__(self, payload):
        self.payload = payload
        self.future = asyncio.get_event_loop().create_future()
        self.tokens = estimate_tokens(payload)
        self.id = str(uuid.uuid4())[:8]

class Scheduler:
    def __init__(self, max_tokens_in_flight=4000, max_wait_ms=50):
        self.queue = []
        self.lock = asyncio.Lock()
        self.max_tokens = max_tokens_in_flight
        self.max_wait_ms = max_wait_ms
        self.tokens_in_flight = 0

    async def add_task(self, task: Task):
        async with self.lock:
            self.queue.append(task)
            metrics.queue_size = len(self.queue)
            metrics.total_requests += 1
            metrics.tasks.append({
               "id": task.id,
               "tokens": task.tokens,
               "status": "queued"
            })

    async def get_batch(self):
        start = time.time()

        while True:
            async with self.lock:
                batch = []
                tokens = 0

                for task in self.queue:
                    if len(batch) >= metrics.concurrency:
                        break
                    if self.tokens_in_flight + tokens + task.tokens > self.max_tokens:
                        continue

                    batch.append(task)
                    tokens += task.tokens

                if batch:
                    for t in batch:
                        self.queue.remove(t)
                        # 🔥 update status
                        for mt in metrics.tasks:
                            if mt["id"] == t.id:
                                mt["status"] = "running"

                    self.tokens_in_flight += tokens
                    
                    metrics.queue_size = len(self.queue)
                    metrics.tokens_in_flight = self.tokens_in_flight
                    metrics.last_batch_size = len(batch)


                    metrics.batches.append({
                        "tasks": [
                            {
                                "id": t.id,
                                "tokens": t.tokens
                            }
                            for t in batch
                        ],
                        "size": len(batch)
                    })

                    metrics.batches = metrics.batches[-10:]

                    return batch

                if self.queue and (time.time() - start) * 1000 > self.max_wait_ms:
                    # fallback: weź chociaż jeden
                    task = self.queue.pop(0)
                    # 🔥 update status for fallback task too
                    for mt in metrics.tasks:
                        if mt["id"] == task.id:
                            mt["status"] = "running"
                    self.tokens_in_flight += task.tokens
                    return [task]

            await asyncio.sleep(0.005)

    async def release_tokens(self, batch):
        async with self.lock:
            for task in batch:
                self.tokens_in_flight -= task.tokens
