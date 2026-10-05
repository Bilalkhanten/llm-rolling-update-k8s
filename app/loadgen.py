"""
loadgen.py - a streaming load client with a *truncation-aware* scoreboard.

A normal HTTP load tool (hey, wrk, ab) will happily report "200 OK" for a stream
that was cut in the middle of a sentence. This one only counts a request as OK
if the SSE stream ends with `data: [DONE]`.

Outcomes
  ok         stream finished with [DONE]
  truncated  HTTP 200, but the stream died before [DONE]   <- users see half an answer
  http_err   non-200 answer (503 while loading/draining, 502 from a proxy, ...)
  conn_err   could not even connect (connection refused / timeout)
"""
import argparse
import asyncio
import collections
import json
import time

import httpx

counts = collections.Counter()
versions = collections.Counter()


async def one_request(client: httpx.AsyncClient, url: str) -> None:
    counts["started"] += 1
    seen_done = False
    try:
        async with client.stream("POST", f"{url}/v1/completions", json={"prompt": "hi"}) as r:
            if r.status_code != 200:
                counts["http_err"] += 1
                return
            async for line in r.aiter_lines():
                if line == "data: [DONE]":
                    seen_done = True
                elif line.startswith("data: {"):
                    try:
                        versions[json.loads(line[6:])["model"]] += 1
                    except Exception:
                        pass
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout):
        counts["conn_err"] += 1
        return
    except (httpx.RemoteProtocolError, httpx.ReadError, httpx.ReadTimeout, httpx.WriteError):
        counts["truncated"] += 1
        return
    counts["ok" if seen_done else "truncated"] += 1


async def worker(client, url, stop_at, pause):
    while time.time() < stop_at:
        await one_request(client, url)
        await asyncio.sleep(pause)


async def reporter(t0, every, stop_at):
    while time.time() < stop_at:
        await asyncio.sleep(every)
        print_line(t0)


def print_line(t0):
    print(
        f"[t={time.time() - t0:5.0f}s] started={counts['started']:<4} ok={counts['ok']:<4} "
        f"truncated={counts['truncated']:<3} http_err={counts['http_err']:<3} "
        f"conn_err={counts['conn_err']:<3} tokens_by_version={dict(versions)}",
        flush=True,
    )


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://llm")
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--duration", type=float, default=3600, help="seconds")
    ap.add_argument("--report", type=float, default=10, help="seconds between scoreboard lines")
    ap.add_argument("--pause", type=float, default=0.2, help="pause between requests per worker")
    args = ap.parse_args()

    t0 = time.time()
    stop_at = t0 + args.duration
    # keepalive_expiry=0 -> new TCP connection per request, so the Service actually
    # load-balances (a pinned keep-alive connection would hide rollout problems).
    limits = httpx.Limits(max_keepalive_connections=0)
    timeout = httpx.Timeout(connect=3, read=30, write=5, pool=5)
    async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
        tasks = [asyncio.create_task(worker(client, args.url, stop_at, args.pause))
                 for _ in range(args.concurrency)]
        tasks.append(asyncio.create_task(reporter(t0, args.report, stop_at)))
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass
    print("---- final ----")
    print_line(t0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
