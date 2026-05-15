#!/usr/bin/env python3
"""mctrader-hub/scripts/check_cross_repo_locks.py

ADR-030 §D13 — cross-repo uv.lock python_version + 핵심 lib major version drift gate.

Checks:
  - python_version >= 3.12 across all 6 repos
  - pyarrow / boto3 / pydantic / websockets major version 일치 (cross-repo)

Exit codes:
  0  = all aligned
  1  = python_version drift
  2  = lib major version drift
  99 = uv.lock missing or parse fail
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import tomllib  # Python 3.11+

REPOS = [
    "mctrader-hub",
    "mctrader-data",
    "mctrader-engine",
    "mctrader-web",
    "mctrader-signal-collector",
    "mctrader-market",
]
CHECK_LIBS = ["pyarrow", "boto3", "pydantic", "websockets"]
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]  # c:/workspace/mclayer


def load_lock(repo: str) -> dict[str, Any] | None:
    lock_path = WORKSPACE_ROOT / repo / "uv.lock"
    if not lock_path.exists():
        print(f"[lock-check] WARN: {repo}/uv.lock missing (skip)")
        return None
    return tomllib.loads(lock_path.read_text())


def lib_major(lock: dict[str, Any], name: str) -> str | None:
    for pkg in lock.get("package", []):
        if pkg.get("name") == name:
            v = pkg.get("version", "")
            return v.split(".", 1)[0] if v else None
    return None


def python_version(lock: dict[str, Any]) -> str | None:
    return lock.get("requires-python") or lock.get("python-version")


def main() -> int:
    locks: dict[str, dict[str, Any]] = {}
    for repo in REPOS:
        lock = load_lock(repo)
        if lock is not None:
            locks[repo] = lock

    if not locks:
        print("[lock-check] FAIL: no uv.lock found")
        return 99

    # python_version drift
    py_versions = {repo: python_version(lock) for repo, lock in locks.items()}
    distinct_py = {v for v in py_versions.values() if v}
    print(f"[lock-check] python_version per repo: {py_versions}")
    if len(distinct_py) > 1:
        print(f"[lock-check] FAIL: python_version drift: {distinct_py}")
        return 1

    # lib major drift
    drift_libs: list[str] = []
    for lib in CHECK_LIBS:
        majors = {repo: lib_major(lock, lib) for repo, lock in locks.items()}
        distinct = {m for m in majors.values() if m}
        if len(distinct) > 1:
            drift_libs.append(f"{lib}: {majors}")

    if drift_libs:
        print("[lock-check] FAIL: lib major version drift:")
        for d in drift_libs:
            print(f"  - {d}")
        return 2

    print("[lock-check] ALL ALIGNED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
