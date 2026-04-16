# 🚀 codeweaver — local LLM runtime proxy
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
docker run -p 8000:8000 codeweaver/llm-proxy
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

