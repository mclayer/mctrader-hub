"""Compactor tracemalloc snapshot collector.

Usage:
    # baseline (A1 적용 전):
    python tools/compactor-tracemalloc.py --duration-hours 12 --interval-min 10 --out /var/log/compactor-tracemalloc/baseline

    # after A1:
    python tools/compactor-tracemalloc.py --duration-hours 12 --interval-min 10 --out /var/log/compactor-tracemalloc/after-a1
"""
from __future__ import annotations

import argparse
import os
import pickle
import signal
import sys
import time
import tracemalloc
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration-hours", type=float, default=12.0)
    parser.add_argument("--interval-min", type=float, default=10.0)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--top", type=int, default=25)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    tracemalloc.start(25)  # 25 frames per traceback

    end = time.time() + args.duration_hours * 3600
    interval = args.interval_min * 60
    n = 0
    prev_snapshot = None

    def _stop(signum, frame):
        print(f"[tracemalloc] signal {signum} received, stopping", file=sys.stderr)
        sys.exit(0)

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    while time.time() < end:
        snap = tracemalloc.take_snapshot()
        ts = int(time.time())
        out_path = args.out / f"snap-{ts}.pkl"
        with out_path.open("wb") as f:
            pickle.dump(snap, f)

        top_stats = snap.statistics("lineno")[: args.top]
        print(f"\n[tracemalloc] snapshot {n} ts={ts} top {args.top}:")
        for stat in top_stats:
            print(f"  {stat}")

        if prev_snapshot is not None:
            diff = snap.compare_to(prev_snapshot, "lineno")[: args.top]
            print(f"[tracemalloc] diff vs prev top {args.top}:")
            for stat in diff:
                print(f"  {stat}")

        prev_snapshot = snap
        n += 1
        time.sleep(interval)

    print(f"[tracemalloc] completed {n} snapshots → {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
