"""Measure localhost Statistics API cache misses and hits with repeated requests."""

from __future__ import annotations

import argparse
import json
import socket
import statistics
import time
from pathlib import Path
from urllib.request import urlopen


DEFAULT_URL = "http://127.0.0.1:8080/api/statistics/overview"
DEFAULT_REDIS_KEY = "statistics:overview"


def redis_command(host: str, port: int, *parts: str) -> str:
    encoded_parts = [part.encode("utf-8") for part in parts]
    request = f"*{len(encoded_parts)}\r\n".encode("ascii")
    for part in encoded_parts:
        request += f"${len(part)}\r\n".encode("ascii") + part + b"\r\n"
    with socket.create_connection((host, port), timeout=3) as connection:
        connection.sendall(request)
        reply = connection.recv(4096).decode("utf-8").strip()
    if reply.startswith(("+", ":")):
        return reply[1:]
    if reply.startswith("-"):
        raise RuntimeError(f"Redis command failed: {reply[1:]}")
    return reply


def request_ms(url: str) -> tuple[float, dict[str, object]]:
    started = time.perf_counter_ns()
    with urlopen(url, timeout=10) as response:
        payload = json.load(response)
    return (time.perf_counter_ns() - started) / 1_000_000, payload


def summarize(samples: list[float]) -> dict[str, object]:
    return {
        "min": round(min(samples), 4),
        "median": round(statistics.median(samples), 4),
        "max": round(max(samples), 4),
        "samples": [round(value, 4) for value in samples],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--redis-host", default="127.0.0.1")
    parser.add_argument("--redis-port", type=int, default=6379)
    parser.add_argument("--redis-key", default=DEFAULT_REDIS_KEY)
    parser.add_argument("--repetitions", type=int, default=10)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    miss_samples: list[float] = []
    hit_samples: list[float] = []
    for _ in range(args.repetitions):
        redis_command(args.redis_host, args.redis_port, "DEL", args.redis_key)
        elapsed, payload = request_ms(args.url)
        if "totalJobs" not in payload:
            raise RuntimeError("Statistics overview response is missing totalJobs")
        miss_samples.append(elapsed)
        hit_samples.append(request_ms(args.url)[0])

    ttl_reply = redis_command(args.redis_host, args.redis_port, "TTL", args.redis_key)
    result = {
        "url": args.url,
        "redis_key": args.redis_key,
        "repetitions": args.repetitions,
        "cache_miss_ms": summarize(miss_samples),
        "cache_hit_ms": summarize(hit_samples),
        "ttl_reply": ttl_reply,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
