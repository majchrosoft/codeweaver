class Metrics:
    def __init__(self):
        self.queue_size = 0
        self.tokens_in_flight = 0
        self.last_batch_size = 0
        self.total_requests = 0

        self.tasks = []
        self.batches = []
        self.concurrency = 2


metrics = Metrics()
