function colorStatus(status) {
    if (status === "running") return "orange";
    if (status === "done") return "green";
    return "gray";
}

async function refresh() {
    try {
        const res = await fetch('/metrics');
        const data = await res.json();

        // 🔢 podstawowe metryki
        document.getElementById('queue').innerText =
            "Size: " + data.queue_size;

        document.getElementById('tokens').innerText =
            "In flight: " + data.tokens_in_flight;

        document.getElementById('concurrency').innerText =
            "Current: " + data.concurrency;

        document.getElementById('batch').innerText =
            "Last batch size: " + data.last_batch_size;

        // 🔥 TASKS
        const tasksHtml = data.tasks.map(t =>
            `<div style="color:${colorStatus(t.status)}">
                ${t.id} | ${t.tokens} tokens | ${t.status}
            </div>`
        ).join("");

        document.getElementById('tasks').innerHTML = tasksHtml;

        // 🔥 BATCHES
        const batchesHtml = data.batches.map(b =>
            `<div style="margin-bottom:10px">
                <b>Batch (${b.size})</b><br>
                ${b.tasks.map(t =>
                    `${t.id} (${t.tokens})`
                ).join("<br>")}
            </div>`
        ).join("");

        document.getElementById('batches').innerHTML = batchesHtml;

    } catch (err) {
        console.error("refresh error:", err);
    }
}


async function autotune() {
    try {
        const input = document.getElementById('concurrency-input').value;

        const res = await fetch('/autotune', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                concurrency: input ? parseInt(input) : null
            })
        });

        const data = await res.json();

        document.getElementById('result').innerText =
            JSON.stringify(data);

        await refresh();

    } catch (err) {
        console.error("autotune error:", err);
    }
}


// 🔥 live refresh
setInterval(refresh, 1000);
refresh();
