#!/usr/bin/env python3
"""
sigterm_lab.py - replay Kubernetes' pod-termination sequence against a local process.

No cluster needed. For each scenario we start the fake LLM server, get a few
60-second answers streaming, then do what the kubelet does:

    t0            pod is marked Terminating (grace-period clock starts NOW,
                  preStop time is *part of* the grace period)
    t0 .. t0+3s   "propagation window": proxies / kube-proxy / gateways that have not
                  noticed yet keep sending NEW requests to the pod
    t0+preStop    SIGTERM
    t0+grace      SIGKILL if the process is still alive

and then we count what the users would have seen.

Usage:  python lab/sigterm_lab.py
"""
import asyncio
import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx

APP_DIR = Path(__file__).resolve().parent.parent / "app"
TOKENS, DELAY = 120, 0.5            # one answer = 60 s
N_STREAMS, STAGGER = 4, 12          # 4 in-flight answers, started 12 s apart
PREROLL = (N_STREAMS - 1) * STAGGER + 9   # t0 = 45 s -> remaining: 15, 27, 39, 51 s
PROPAGATION_WINDOW = 3.0            # seconds during which stale routes still send traffic


@dataclass
class Scenario:
    key: str
    title: str
    grace: int
    prestop: int
    mode: str
    port: int
    events: list = field(default_factory=list)
    inflight: dict = field(default_factory=lambda: {"ok": 0, "truncated": 0})
    late: dict = field(default_factory=lambda: {"ok": 0, "refused": 0})
    t0: float = 0.0

    def log(self, msg):
        self.events.append(f"[{self.key}] +{time.time() - self.t0:5.1f}s  {msg}")


async def stream_once(port: int) -> str:
    """One full answer. Returns 'ok' only if the stream ended with [DONE]."""
    done = False
    try:
        timeout = httpx.Timeout(connect=3, read=30, write=5, pool=5)
        async with httpx.AsyncClient(timeout=timeout) as c:
            async with c.stream("POST", f"http://127.0.0.1:{port}/v1/completions") as r:
                if r.status_code != 200:
                    return "http_err"
                async for line in r.aiter_lines():
                    if line == "data: [DONE]":
                        done = True
    except (httpx.RemoteProtocolError, httpx.ReadError, httpx.ReadTimeout):
        return "truncated"
    except httpx.ConnectError:
        return "refused"
    return "ok" if done else "truncated"


async def late_probe(port: int) -> str:
    """A NEW request that a stale route still sends to the terminating pod."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(3)) as c:
            async with c.stream("POST", f"http://127.0.0.1:{port}/v1/completions") as r:
                if r.status_code != 200:
                    return "refused"
                async for _ in r.aiter_lines():
                    return "ok"          # got the first token: request accepted
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.RemoteProtocolError, httpx.ReadError):
        return "refused"
    return "ok"


async def run(s: Scenario) -> Scenario:
    env = dict(os.environ, LOAD_SECONDS="1", TOKENS=str(TOKENS), TOKEN_DELAY=str(DELAY),
               SHUTDOWN_MODE=s.mode, MODEL_VERSION="lab")
    logfile = open(f"/tmp/lab-{s.key}.log", "w")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "fake_llm:app", "--host", "127.0.0.1", "--port", str(s.port)],
        cwd=APP_DIR, env=env, stdout=logfile, stderr=subprocess.STDOUT)

    # wait for readiness
    async with httpx.AsyncClient() as c:
        for _ in range(100):
            try:
                if (await c.get(f"http://127.0.0.1:{s.port}/readyz")).status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            await asyncio.sleep(0.2)

    start = time.time()
    tasks = []
    for i in range(N_STREAMS):
        await asyncio.sleep(max(0, start + i * STAGGER - time.time()))
        tasks.append(asyncio.create_task(stream_once(s.port)))
    await asyncio.sleep(max(0, start + PREROLL - time.time()))

    # ---- termination begins ----
    s.t0 = time.time()
    s.log(f"pod marked Terminating (grace={s.grace}s, preStop={s.prestop}s, server={s.mode})")

    async def late_traffic():
        n = int(PROPAGATION_WINDOW / 0.5)
        for _ in range(n):
            r = await late_probe(s.port)
            s.late["ok" if r == "ok" else "refused"] += 1
            await asyncio.sleep(0.5)

    late_task = asyncio.create_task(late_traffic())

    await asyncio.sleep(s.prestop)
    if s.prestop:
        s.log(f"preStop finished after {s.prestop}s")
    s.log("SIGTERM sent")
    proc.send_signal(signal.SIGTERM)

    deadline = s.t0 + s.grace
    while proc.poll() is None and time.time() < deadline:
        await asyncio.sleep(0.2)
    if proc.poll() is None:
        s.log(f"grace period ({s.grace}s) expired -> SIGKILL")
        proc.kill()
    else:
        s.log(f"process exited by itself (status {proc.returncode})")
    proc.wait()

    await late_task
    for r in await asyncio.gather(*tasks):
        s.inflight["ok" if r == "ok" else "truncated"] += 1
    s.log(f"in-flight answers: {s.inflight['ok']} complete, {s.inflight['truncated']} cut off")
    return s


async def main():
    scenarios = [
        Scenario("A", "defaults: 30s grace, no preStop",          30,  0, "graceful", 8101),
        Scenario("B", "90s grace, no preStop",                    90,  0, "graceful", 8102),
        Scenario("C", "90s grace + 10s preStop",                  90, 10, "graceful", 8103),
        Scenario("D", "90s grace + 10s preStop, but the server exits on SIGTERM without draining",
                 90, 10, "abrupt", 8104),
    ]
    print(f"Running {len(scenarios)} scenarios in parallel (~2 minutes)...\n", flush=True)
    done = await asyncio.gather(*(run(s) for s in scenarios))

    for s in done:
        print("\n".join(s.events), "\n")

    hdr = f"{'':2}{'scenario':<76}{'complete':>9}{'cut off':>9}{'new req ok':>12}{'refused':>9}"
    print(hdr)
    print("-" * len(hdr))
    for s in done:
        print(f"{s.key:2}{s.title:<76}{s.inflight['ok']:>9}{s.inflight['truncated']:>9}"
              f"{s.late['ok']:>12}{s.late['refused']:>9}")
    Path(__file__).with_name("results.json").write_text(json.dumps(
        [{"key": s.key, "title": s.title, "grace": s.grace, "prestop": s.prestop, "mode": s.mode,
          "inflight": s.inflight, "late": s.late} for s in done], indent=2))


if __name__ == "__main__":
    asyncio.run(main())
