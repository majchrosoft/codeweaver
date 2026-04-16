console.log("dashboard.js loaded v3");

window.applySettings = async function() {
    try {
        const concurrency = document.getElementById('concurrency-input').value;
        const cavemanInput = document.getElementById('caveman-input-enabled').checked;
        const cavemanOutput = document.getElementById('caveman-output-enabled').checked;

        const res = await fetch('/autotune', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                concurrency: concurrency ? parseInt(concurrency) : null,
                caveman_input: cavemanInput,
                caveman_output: cavemanOutput
            })
        });

        const data = await res.json();

        const resultEl = document.getElementById('result');
        resultEl.innerText = "Settings applied: " + JSON.stringify(data);
        resultEl.style.color = "green";

        // Optional: clear message after 3 seconds
        setTimeout(() => {
            resultEl.innerText = "";
        }, 3000);

        await refresh(true);

    } catch (err) {
        console.error("applySettings error:", err);
        const resultEl = document.getElementById('result');
        resultEl.innerText = "Error: " + err.message;
        resultEl.style.color = "red";
    }
}

function colorStatus(status) {
    if (status === "running") return "orange";
    if (status === "done") return "green";
    return "gray";
}

async function refresh(isInitial = false) {
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

        // 🔥 CAVEMAN (only update on initial load)
        if (isInitial) {
            document.getElementById('caveman-input-enabled').checked = data.caveman_input_enabled;
            document.getElementById('caveman-output-enabled').checked = data.caveman_output_enabled;
            if (data.concurrency && !document.getElementById('concurrency-input').value) {
                document.getElementById('concurrency-input').value = data.concurrency;
            }
        }

    } catch (err) {
        console.error("refresh error:", err);
    }
}

// 🔥 live refresh
setInterval(() => refresh(false), 1000);
refresh(true);
