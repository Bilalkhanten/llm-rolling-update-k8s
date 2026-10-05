"""
fake_llm.py - a tiny stand-in for an LLM server (vLLM, TGI, Triton, ...).

It misbehaves in exactly the ways real ones do:
  * "loads the model" for LOAD_SECONDS (and the port is open the whole time)
  * streams tokens slowly over Server-Sent Events, so one request takes
    TOKENS * TOKEN_DELAY seconds
  * reacts to SIGTERM either gracefully (default) or abruptly

Endpoints
  GET  /livez           200 while the process is alive      (livenessProbe)
  GET  /readyz          200 only when the model is loaded   (readiness/startupProbe)
  POST /v1/completions  SSE stream; a complete answer ends with "data: [DONE]"

Env vars
  MODEL_VERSION  label echoed in every token           (default v1)
  LOAD_SECONDS   simulated model load time              (default 45)
  TOKENS         tokens per response                    (default 120)
  TOKEN_DELAY    seconds between tokens                 (default 0.5 -> 60 s per answer)
  SHUTDOWN_MODE  graceful | abrupt                      (default graceful)
"""
import asyncio
import json
import logging
import os
import signal
import sys
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse

MODEL_VERSION = os.getenv("MODEL_VERSION", "v1")
LOAD_SECONDS = float(os.getenv("LOAD_SECONDS", "45"))
TOKENS = int(os.getenv("TOKENS", "120"))
TOKEN_DELAY = float(os.getenv("TOKEN_DELAY", "0.5"))
SHUTDOWN_MODE = os.getenv("SHUTDOWN_MODE", "graceful")

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s %(levelname)s fake-llm[%(process)d] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("fake-llm")

state = {"loaded": False, "draining": False, "inflight": 0}


async def load_model() -> None:
    t0 = time.time()
    log.info("loading model %s (takes %.0fs)...", MODEL_VERSION, LOAD_SECONDS)
    await asyncio.sleep(LOAD_SECONDS)
    state["loaded"] = True
    log.info("model %s loaded in %.1fs, ready to serve", MODEL_VERSION, time.time() - t0)


def install_sigterm_logging() -> None:
    """Log what was in flight when SIGTERM arrived; optionally die immediately."""
    previous = signal.getsignal(signal.SIGTERM)

    def handler(signum, frame):
        state["draining"] = True
        log.warning("SIGTERM received, in-flight requests: %d, mode=%s",
                    state["inflight"], SHUTDOWN_MODE)
        if SHUTDOWN_MODE == "abrupt":
            log.warning("abrupt mode: exiting NOW")
            os._exit(143)
        if callable(previous):
            previous(signum, frame)  # uvicorn: stop accepting, wait for in-flight

    signal.signal(signal.SIGTERM, handler)


@asynccontextmanager
async def lifespan(_: FastAPI):
    install_sigterm_logging()
    task = asyncio.create_task(load_model())
    yield
    task.cancel()
    log.info("shutdown complete (in-flight at exit: %d)", state["inflight"])


app = FastAPI(lifespan=lifespan)


@app.get("/livez")
async def livez() -> Response:
    return Response("alive\n", status_code=200)


@app.get("/readyz")
async def readyz() -> Response:
    if state["loaded"] and not state["draining"]:
        return Response("ready\n", status_code=200)
    reason = "draining" if state["draining"] else "model not loaded"
    return Response(f"not ready: {reason}\n", status_code=503)


@app.post("/v1/completions")
async def completions() -> Response:
    if not state["loaded"]:
        return Response("model still loading\n", status_code=503)

    async def stream():
        state["inflight"] += 1
        try:
            for i in range(TOKENS):
                payload = {"model": MODEL_VERSION, "index": i, "token": f"tok{i}"}
                yield f"data: {json.dumps(payload)}\n\n"
                await asyncio.sleep(TOKEN_DELAY)
            yield "data: [DONE]\n\n"
        finally:
            state["inflight"] -= 1

    return StreamingResponse(stream(), media_type="text/event-stream")
