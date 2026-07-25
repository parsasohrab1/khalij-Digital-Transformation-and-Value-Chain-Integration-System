"""Load test for critical path endpoints (Phase 5 / NFR-PER / NFR-SCL).

Runs concurrent requests against health + optimize + dashboard to estimate TPS.
Does not claim full 50k TPS locally; reports projected capacity with horizontal scale factor.
"""
from __future__ import annotations

import argparse
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def hit(client: httpx.Client, method: str, url: str, json_body: dict | None = None) -> tuple[bool, float, int]:
    t0 = time.perf_counter()
    try:
        if method == "GET":
            r = client.get(url)
        else:
            r = client.post(url, json=json_body or {})
        ok = r.status_code < 500
        return ok, (time.perf_counter() - t0) * 1000, r.status_code
    except Exception:  # noqa: BLE001
        return False, (time.perf_counter() - t0) * 1000, 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Khalij DVC load test")
    parser.add_argument("--base", default="http://127.0.0.1:8002", help="analytics base for optimize")
    parser.add_argument("--bi", default="http://127.0.0.1:8005", help="BI base")
    parser.add_argument("--concurrency", type=int, default=32)
    parser.add_argument("--requests", type=int, default=200)
    parser.add_argument("--scale-factor", type=int, default=50, help="assumed horizontal replicas for projection")
    args = parser.parse_args()

    paths = [
        ("GET", f"{args.bi}/health", None),
        ("GET", f"{args.bi}/dashboard?period=7d&locale=en", None),
        (
            "POST",
            f"{args.base}/optimize/integrated",
            {"horizon_days": 30, "available_feedstock_tons": 2000, "oil_price_usd_bbl": 75, "model": "prophet"},
        ),
    ]

    latencies: list[float] = []
    ok_count = 0
    t_start = time.perf_counter()

    def worker(i: int):
        method, url, body = paths[i % len(paths)]
        with httpx.Client(timeout=30.0) as client:
            return hit(client, method, url, body)

    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [pool.submit(worker, i) for i in range(args.requests)]
        for fut in as_completed(futures):
            ok, ms, _code = fut.result()
            latencies.append(ms)
            if ok:
                ok_count += 1

    elapsed = time.perf_counter() - t_start
    tps = args.requests / max(elapsed, 1e-6)
    p50 = statistics.median(latencies)
    p95 = sorted(latencies)[int(0.95 * (len(latencies) - 1))]
    projected = tps * args.scale_factor

    print("✅ Load test complete")
    print(f"requests={args.requests} concurrency={args.concurrency} ok={ok_count}")
    print(f"elapsed_s={elapsed:.2f} measured_tps={tps:.1f}")
    print(f"latency_ms p50={p50:.1f} p95={p95:.1f}")
    print(f"projected_tps_with_{args.scale_factor}_replicas={projected:.0f} (target=50000)")
    print("note: projection is linear capacity estimate for planning, not a guarantee")


if __name__ == "__main__":
    main()
