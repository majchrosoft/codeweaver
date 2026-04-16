# 🚀 codeweaver — VRAM-aware local LLM runtime proxy
MIT License

> **Turn any local LLM into a smart, VRAM-aware, production-ready system.**

---

## 🧠 What is this?

`codeweaver` is a transparent OpenAI-compatible proxy that sits between your tools (IDE, agents, CLI) and your local LLM.

But it's NOT just a proxy.

It is:

> 🔥 **A runtime optimizer for local LLMs**

---

## ⚠️ The problem

Local LLMs are powerful, but:

* VRAM is limited
* context windows are expensive
* multiple requests kill performance
* tools like Continue or LM Studio:

  * don’t manage load
  * don’t batch intelligently
  * don’t understand resource constraints

Result:

> ❌ GPU underutilized OR overloaded
> ❌ slow responses
> ❌ unstable performance

---

## 🔥 The idea

Instead of:

```text
request → model → response
```

we do:

```text
request → queue → scheduler → batch → model → response
```

---

## ⚡ Core features

### 🧠 VRAM-aware scheduling

We don’t limit requests.

We limit:

> 🔥 **tokens in flight**

```text
more tokens = more memory usage
```

This prevents:

* OOM crashes
* random slowdowns
* GPU thrashing

---

### ⚡ Async queue + batching

* incoming requests go to a shared queue
* grouped into batches dynamically
* processed concurrently (controlled)

---

### 🔒 Concurrency control

```python
asyncio.Semaphore(N)
```

Limits how many requests hit the model at once.

---

### 🔌 OpenAI-compatible API

Drop-in replacement:

```http
POST /v1/chat/completions
```

Works with:

* PhpStorm
* VS Code
* any OpenAI client

---

### 🐳 Docker-first

Runs anywhere:

```bash
docker run -p 8000:8000 --add-host=host.docker.internal:host-gateway codeweaver/llm-proxy
```

---

## 🧱 Architecture

```text
Client (IDE / CLI)
        ↓
codeweaver proxy
        ↓
[async queue]
        ↓
[VRAM-aware scheduler]
        ↓
[batch + concurrency control]
        ↓
LLM (Ollama / llama.cpp)
```

---

## 🧪 Why this matters

Most tools focus on:

> ❌ prompt engineering
> ❌ agents
> ❌ RAG

But ignore:

> 🔥 **runtime efficiency**

This project focuses on:

> **how LLMs run, not just what they say**

---

## 💡 What makes this different?

| Feature               | Typical tools | codeweaver |
| --------------------- | ------------- | ---------- |
| OpenAI proxy          | ✅             | ✅          |
| Queue                 | ❌             | ✅          |
| Batching              | ❌             | ✅          |
| VRAM-aware scheduling | ❌             | 🔥         |
| Token-based control   | ❌             | 🔥         |

---

## 🚀 Getting started

### 1. Run Ollama

```bash
ollama serve
```

---

### 2. Build image

```bash
docker build -t codeweaver/llm-proxy .
```

---

### 3. Run proxy

```bash
docker run -p 8000:8000 codeweaver/llm-proxy
```

---

### 4. Test

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello"}
    ]
  }'
```

---

## 🔧 Configuration (coming soon)

* dynamic token limits
* model routing
* priority queues

---

## 🧠 Future ideas (nice-to-have)

* smart context chunking (code-aware)
* AST-based selection
* dashboard with:

  * queue state
  * token usage
  * latency
* multi-model orchestration

---

## ⚠️ Disclaimer

This is an early-stage system.

But the idea is simple:

> 🔥 **LLMs need runtime optimization, not just better prompts**

---

## 🤝 Contributing

If you care about:

* local LLM performance
* GPU efficiency
* building real infra instead of demos

You’re welcome.

---

## 🧨 Final thought

The next wave of AI tools won’t be:

> “better prompts”

but:

> 🔥 **better systems around models**

---

**codeweaver is a step in that direction.**

## 🐳 Running with Docker (Linux + Ollama)

This project runs as a proxy in Docker, but your LLM (e.g. Ollama) runs on the host machine.

Because of that, you must correctly configure networking.

---

### 🔧 1. Start Ollama on host

By default Ollama binds to `127.0.0.1`, which is NOT accessible from Docker.

Run it like this:

```bash
OLLAMA_HOST=0.0.0.0 ollama serve
```

---

### 🧱 2. Build Docker image

```bash
docker build -t codeweaver/llm-proxy .
```

---

### 🚀 3. Run container (Linux)

```bash
docker run -p 8000:8000 \
  --add-host=host.docker.internal:host-gateway \
  codeweaver/llm-proxy
```

---

### 🧠 Why `--add-host`?

On Linux, Docker does NOT automatically expose the host machine.

This flag makes:

```text
host.docker.internal → your host machine
```

---

### 🔌 4. Access API

```bash
http://localhost:8000
```

---

### ✅ Test proxy

#### List models (proxied to Ollama)

```bash
curl http://localhost:8000/v1/models
```

#### Direct passthrough

```bash
curl http://localhost:8000/api/tags
```

---

### 📊 Dashboard

```bash
http://localhost:8000/dashboard
```

---

## ⚠️ Troubleshooting

### ❌ `Connection refused` / `ConnectError`

Make sure Ollama is running on:

```text
0.0.0.0:11434
```

Check:

```bash
ss -tulnp | grep 11434
```

---

### ❌ `host.docker.internal` not found

Make sure you used:

```bash
--add-host=host.docker.internal:host-gateway
```

---

### ❌ Still not working?

Use host IP instead:

```bash
ip a
```

Then update:

```python
OLLAMA_URL = "http://YOUR_IP:11434"
```

---

## 🧠 Architecture

```text
Client (IDE / CLI)
        ↓
codeweaver proxy (Docker)
        ↓
(host.docker.internal)
        ↓
Ollama (host machine)
```

---

## 🔥 What this enables

* OpenAI-compatible API
* Smart batching + queue
* VRAM-aware scheduling
* Transparent passthrough to Ollama

