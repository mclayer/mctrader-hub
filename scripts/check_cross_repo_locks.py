#!/usr/bin/env python3
"""mctrader-hub/scripts/check_cross_repo_locks.py

ADR-030 §D13 — cross-repo uv.lock python_version + 핵심 lib major version drift gate.

Checks:
  - python_version distinct count == 1 across required repos
    (semantic = distinct equality only — 절대 minimum 미정의, FIX iter 1 P0-2 amend)
  - pyarrow / boto3 / pydantic / websockets major version 일치 (cross-repo)

Required vs optional repos:
  - REQUIRED: mctrader-data / mctrader-engine / mctrader-web / mctrader-market
    → uv.lock 부재 시 exit 99 (strict mode, FIX iter 1 P0-2 D13 coverage gap fix)
  - OPTIONAL (MISSING_OK_REPOS): mctrader-hub / mctrader-signal-collector
    → uv.lock 부재 시 WARN + skip (현 시점 uv 미도입)

Exit codes:
  0  = all aligned
  1  = python_version drift
  2  = lib major version drift
  99 = required repo uv.lock missing or parse fail
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

# uv.lock 부재 허용 repo (현 시점 uv 미도입, ADR-030 §D13 amendment box FIX iter 1)
MISSING_OK_REPOS = {"mctrader-hub", "mctrader-signal-collector"}

CHECK_LIBS = ["pyarrow", "boto3", "pydantic", "websockets"]
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]  # c:/workspace/mclayer


def load_lock(repo: str) -> dict[str, Any] | None:
    """Load uv.lock for a repo. Returns None if optional repo missing."""
    lock_path = WORKSPACE_ROOT / repo / "uv.lock"
    if not lock_path.exists():
        if repo in MISSING_OK_REPOS:
            print(f"[lock-check] WARN: {repo}/uv.lock missing (optional, skip)")
            return None
        # required repo 부재 → 호출자가 exit 99 처리
        print(f"[lock-check] FAIL: required repo {repo}/uv.lock missing")
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
        lock_path = WORKSPACE_ROOT / repo / "uv.lock"
        if not lock_path.exists():
            if repo in MISSING_OK_REPOS:
                print(f"[lock-check] WARN: {repo}/uv.lock missing (optional, skip)")
                continue
            # required repo 부재 → exit 99 (strict mode)
            print(f"[lock-check] FAIL: required repo {repo}/uv.lock missing")
            return 99
        try:
            locks[repo] = tomllib.loads(lock_path.read_text())
        except Exception as e:
            print(f"[lock-check] FAIL: {repo}/uv.lock parse error: {e}")
            return 99

    if not locks:
        print("[lock-check] FAIL: no uv.lock found in any required repo")
        return 99

    # python_version drift (distinct equality only)
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
