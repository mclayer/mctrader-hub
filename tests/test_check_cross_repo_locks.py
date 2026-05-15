"""Unit tests for scripts/check_cross_repo_locks.py
ADR-030 §D13 — lib_major() + python_version() 함수 단위 검증.
"""

from __future__ import annotations

import sys
from pathlib import Path

# scripts/ 를 sys.path 에 추가 (importlib 불필요)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_cross_repo_locks import lib_major, python_version  # noqa: E402


def _make_lock(packages: list[dict], requires_python: str | None = None) -> dict:
    lock: dict = {"package": packages}
    if requires_python is not None:
        lock["requires-python"] = requires_python
    return lock


class TestLibMajor:
    def test_returns_major_for_known_package(self) -> None:
        lock = _make_lock([{"name": "pyarrow", "version": "15.0.2"}])
        assert lib_major(lock, "pyarrow") == "15"

    def test_returns_none_for_missing_package(self) -> None:
        lock = _make_lock([{"name": "boto3", "version": "1.34.0"}])
        assert lib_major(lock, "pyarrow") is None

    def test_major_only_first_segment(self) -> None:
        lock = _make_lock([{"name": "pydantic", "version": "2.7.1"}])
        assert lib_major(lock, "pydantic") == "2"

    def test_empty_version_returns_none(self) -> None:
        lock = _make_lock([{"name": "websockets", "version": ""}])
        assert lib_major(lock, "websockets") is None

    def test_single_segment_version(self) -> None:
        lock = _make_lock([{"name": "boto3", "version": "1"}])
        assert lib_major(lock, "boto3") == "1"


class TestPythonVersion:
    def test_requires_python_field(self) -> None:
        lock = _make_lock([], requires_python=">=3.12")
        assert python_version(lock) == ">=3.12"

    def test_python_version_field_fallback(self) -> None:
        lock: dict = {"package": [], "python-version": "3.12"}
        assert python_version(lock) == "3.12"

    def test_missing_both_fields_returns_none(self) -> None:
        lock = _make_lock([])
        assert python_version(lock) is None

    def test_requires_python_takes_precedence(self) -> None:
        lock: dict = {
            "package": [],
            "requires-python": ">=3.12",
            "python-version": "3.11",
        }
        assert python_version(lock) == ">=3.12"
