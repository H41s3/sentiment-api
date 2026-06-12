# Engineering Decisions

A plain-English breakdown of every change made and why.

---

## 1. Fixed the README

The README was documenting a version of the project that no longer existed. The batch endpoint,
versioned health check, middleware, and utils were all missing. A new engineer cloning this repo
would have no idea those features existed.

Also added a note clarifying that the real DistilBERT model only outputs POSITIVE/NEGATIVE — no
NEUTRAL. The stub does, the model doesn't. That's a silent inconsistency that would confuse anyone
running it in prod for the first time.

---

## 2. Uncommented ML Dependencies

```python
# before — silently runs keyword matching in prod
# transformers==4.40.2
# torch==2.3.0

# after
transformers==4.40.2
torch==2.3.0
```

Someone commented these out and left a note "uncomment when ready." They were never uncommented.
The Docker image was shipping the stub, not DistilBERT. That's a critical bug disguised as a comment.

Also added `gunicorn` here because you can't run multi-worker production without it.

---

## 3. CORS Middleware

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # defaults to ["*"]
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

Without CORS headers, any browser-based client (a dashboard, a frontend app) calling this API gets
blocked. Defaults to `["*"]` so it works out of the box, but you can lock it down to specific
origins via the `CORS_ORIGINS` env var in production. No code change needed when you deploy to a
real domain.

---

## 4. Global Error Handler

```python
@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    return JSONResponse(status_code=500, content={"error": "internal_error", "message": "..."})
```

Before this, if the pipeline crashed or threw an unexpected exception, FastAPI would return a raw
500 with whatever Python put in the traceback — sometimes leaking internal paths or library details.
Now every error returns the same shape. Clients can always expect `{error, message}` regardless of
what went wrong.

---

## 5. Optional API Key Auth

```python
# app/auth.py
async def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if settings.api_key is None:
        return  # auth disabled — no env var set
    if x_api_key != settings.api_key:
        raise HTTPException(401, ...)
```

The key design decision here was making it **opt-in**. If `API_KEY` is not set in your environment,
the dependency just returns immediately — no auth enforced. This means existing deployments and all
existing tests keep working with zero changes. When you're ready to lock it down, you set one env var.

It's wired in as a route-level dependency, not middleware, so the health endpoints are always
public — you need those for container orchestration probes.

---

## 6. Text Preprocessing Improvements

```python
# before
def preprocess(text):
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text

# after
def preprocess(text):
    text = _HTML_TAG.sub(" ", text)   # strip <b>bold</b> → " bold "
    text = _URL.sub("[URL]", text)    # replace https://... → [URL]
    text = text.strip()
    text = _WHITESPACE.sub(" ", text)
    return text
```

Two real-world problems this fixes: people submitting HTML from a rich text editor, and people
submitting text with URLs. The model was trained on clean text. Feeding it raw HTML tags or long
URLs as tokens adds noise that reduces classification accuracy. Replacing URLs with the literal
token `[URL]` is a common NLP convention — the model understands it as "a URL was here" rather
than trying to tokenize `https://very-long-domain.com/path?query=value`.

---

## 7. Vectorized Batch Inference

```python
# before — N forward passes
items = [BatchSentimentItem(text=t, sentiment=service.analyze(t)) for t in request.texts]

# after — 1 forward pass
def analyze_batch(self, texts):
    results = self._pipeline(truncated)  # list in, list out
    return [SentimentResult(...) for r in results]
```

HuggingFace pipelines natively accept a list and run a single batched matrix multiplication. The
old code called the pipeline once per text. For a 32-item batch that's 32 forward passes vs 1. On
CPU that's roughly 32x slower. On GPU you throw away the entire advantage of having a GPU.

---

## 8. Async Inference via run_in_executor

```python
# before — blocks the event loop
result = service.analyze(request.text)

# after — runs in a thread, event loop stays free
result = await loop.run_in_executor(None, service.analyze, request.text)
```

FastAPI is async. When you call a slow synchronous function directly from an async route handler,
you freeze the entire server — no other requests can be processed until inference finishes.
`run_in_executor` hands the work off to Python's default thread pool. The event loop stays
responsive, health checks keep responding, and other requests can be accepted while inference
is running.

---

## 9. X-Request-ID Tracing Header

```python
request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
logger.info("[%s] %s %s -> %d  (%.1f ms)", request_id, ...)
response.headers["x-request-id"] = request_id
```

Every log line now has a request ID. If a client sends their own ID (which good API clients do),
we echo it back so their logs and your logs correlate. If they don't send one, we generate a UUID.
This is the foundation of distributed tracing — when you add a frontend or a second service later,
you can follow a single request end-to-end through logs without guessing.

---

## 10. Dockerfile — Gunicorn + Weight Pre-Baking

```dockerfile
# pre-download weights at build time
RUN python -c "from transformers import pipeline; pipeline('sentiment-analysis', model='...')" || true

CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "-w", "2", ...]
```

Two separate fixes here:

**Gunicorn** — uvicorn alone is a single process. One request blocks during inference. Gunicorn
spawns 2 worker processes, each with their own copy of the model in memory. You get real
parallelism. The `|| true` on the pre-download step means if there's a network issue during build,
the build doesn't fail — it just downloads at first start instead.

**Weight pre-baking** — without this, the first time a container starts, it downloads ~260MB from
HuggingFace Hub before serving any traffic. In Kubernetes, this means a new pod takes 2+ minutes
to become ready. Every auto-scale event, every deploy, every crash restart hits that cold start.
Baking the weights into the image makes pod startup near-instant.

---

## 11. Docker Compose Split

```
docker-compose.yml       — prod: gunicorn, no volume mount
docker-compose.dev.yml   — dev: uvicorn --reload, source mounted
```

The original `docker-compose.yml` had `volumes: - .:/app` which mounts your source directory into
the container. In dev this is great — edit a file, see it reload. In production this is dangerous
— if you run `docker compose up` on a server, the container ignores the built image and runs
whatever is on disk at that path. The split makes the intent explicit.

---

## 12. ErrorResponse Schema in OpenAPI

```python
class ErrorResponse(BaseModel):
    error: str
    message: str

_AUTH_RESPONSES = {401: {"model": ErrorResponse}}

@router.post("/analyze", responses=_AUTH_RESPONSES, ...)
```

Without this, the `/docs` page shows no 401 response for the analyze endpoints — a developer
integrating against your API has no idea what error shape to expect. With it, the Swagger UI shows
the exact JSON structure they'll receive if their API key is wrong.

---

## 13. Per-Key Rate Limiting

```python
# before — all clients at the same IP share one bucket
limiter = Limiter(key_func=get_remote_address)

# after — each API key gets its own independent bucket
def _rate_limit_key(request: Request) -> str:
    api_key = request.headers.get("x-api-key")
    if api_key:
        return f"key:{api_key}"  # prefix prevents collision with a literal IP string
    return get_remote_address(request)
```

The original IP-based limiter has a real problem in production: multiple
clients behind a shared NAT (an office, a cloud provider's egress IP) all
count against the same bucket. One busy client can rate-limit everyone else
at that address.

Per-key limiting gives each API key its own independent counter. A client
hitting their own limit doesn't affect anyone else. Unauthenticated traffic
still falls back to IP — no behaviour change for clients without a key.

The `"key:"` prefix is a deliberate collision guard: without it, an API key
whose value happens to be an IP address would silently merge with that IP's
bucket — a subtle bug that would be very hard to diagnose in production.

---

## The Through-Line

Every decision followed the same principle: **close the gap between what the code says and what
it actually does in production.**

The commented-out ML deps, the single-worker config, the blocking inference, the undocumented
endpoints — none of those are bugs in isolation. But together they mean the version running locally
and the version you'd actually ship are different systems. These commits make them the same system.
