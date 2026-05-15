"""Unit tests for scripts/check_cross_repo_locks.py
ADR-030 §D13 — lib_major() + python_version() 함수 단위 검증 + main() exit code matrix.

FIX iter 1 (P0-2 + P2-2): test_main_exit_99_when_required_repo_missing +
test_main_exit_0_when_optional_repo_missing + test_main_exit_1_when_python_version_drift.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

# scripts/ 를 sys.path 에 추가 (importlib 불필요)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import check_cross_repo_locks  # noqa: E402
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


class TestMainExitMatrix:
    """main() integration tests — FIX iter 1 P0-2 + P2-2.

    WORKSPACE_ROOT 를 tmp_path 로 swap 하여 fixture repo layout 생성.
    """

    def _make_lock_text(self, requires_python: str = ">=3.12", libs: dict | None = None) -> str:
        """Generate minimal uv.lock TOML text."""
        libs = libs or {
            "pyarrow": "15.0.2",
            "boto3": "1.34.0",
            "pydantic": "2.7.1",
            "websockets": "12.0",
        }
        lines = [f'requires-python = "{requires_python}"', ""]
        for name, version in libs.items():
            lines.extend([
                "[[package]]",
                f'name = "{name}"',
                f'version = "{version}"',
                "",
            ])
        return "\n".join(lines)

    def _setup_repos(self, tmp_path: Path, repos: dict[str, str | None]) -> None:
        """Create repo dirs under tmp_path. None value = skip uv.lock creation."""
        for repo, content in repos.items():
            repo_dir = tmp_path / repo
            repo_dir.mkdir(parents=True, exist_ok=True)
            if content is not None:
                (repo_dir / "uv.lock").write_text(content)

    def test_main_exit_0_when_all_aligned(self, tmp_path: Path) -> None:
        """All required repos aligned + optional missing → exit 0."""
        lock_text = self._make_lock_text()
        repos = {
            "mctrader-hub": None,  # MISSING_OK
            "mctrader-data": lock_text,
            "mctrader-engine": lock_text,
            "mctrader-web": lock_text,
            "mctrader-signal-collector": None,  # MISSING_OK
            "mctrader-market": lock_text,
        }
        self._setup_repos(tmp_path, repos)
        with patch.object(check_cross_repo_locks, "WORKSPACE_ROOT", tmp_path):
            assert check_cross_repo_locks.main() == 0

    def test_main_exit_99_when_required_repo_missing(self, tmp_path: Path) -> None:
        """Required repo (mctrader-data) uv.lock 부재 → exit 99 (strict mode)."""
        lock_text = self._make_lock_text()
        repos = {
            "mctrader-hub": None,
            "mctrader-data": None,  # required 부재
            "mctrader-engine": lock_text,
            "mctrader-web": lock_text,
            "mctrader-signal-collector": None,
            "mctrader-market": lock_text,
        }
        self._setup_repos(tmp_path, repos)
        with patch.object(check_cross_repo_locks, "WORKSPACE_ROOT", tmp_path):
            assert check_cross_repo_locks.main() == 99

    def test_main_exit_0_when_optional_repo_missing(self, tmp_path: Path) -> None:
        """Optional repo (hub + signal-collector) 부재 = WARN + skip → exit 0."""
        lock_text = self._make_lock_text()
        repos = {
            "mctrader-hub": None,  # MISSING_OK
            "mctrader-data": lock_text,
            "mctrader-engine": lock_text,
            "mctrader-web": lock_text,
            "mctrader-signal-collector": None,  # MISSING_OK
            "mctrader-market": lock_text,
        }
        self._setup_repos(tmp_path, repos)
        with patch.object(check_cross_repo_locks, "WORKSPACE_ROOT", tmp_path):
            assert check_cross_repo_locks.main() == 0

    def test_main_exit_1_when_python_version_drift(self, tmp_path: Path) -> None:
        """python_version distinct count > 1 → exit 1."""
        lock_a = self._make_lock_text(requires_python=">=3.12")
        lock_b = self._make_lock_text(requires_python=">=3.11")
        repos = {
            "mctrader-hub": None,
            "mctrader-data": lock_a,
            "mctrader-engine": lock_b,  # drift
            "mctrader-web": lock_a,
            "mctrader-signal-collector": None,
            "mctrader-market": lock_a,
        }
        self._setup_repos(tmp_path, repos)
        with patch.object(check_cross_repo_locks, "WORKSPACE_ROOT", tmp_path):
            assert check_cross_repo_locks.main() == 1

    def test_main_exit_2_when_lib_major_drift(self, tmp_path: Path) -> None:
        """lib major version drift → exit 2."""
        lock_a = self._make_lock_text(libs={
            "pyarrow": "15.0.2",
            "boto3": "1.34.0",
            "pydantic": "2.7.1",
            "websockets": "12.0",
        })
        lock_b = self._make_lock_text(libs={
            "pyarrow": "16.0.0",  # major drift
            "boto3": "1.34.0",
            "pydantic": "2.7.1",
            "websockets": "12.0",
        })
        repos = {
            "mctrader-hub": None,
            "mctrader-data": lock_a,
            "mctrader-engine": lock_b,
            "mctrader-web": lock_a,
            "mctrader-signal-collector": None,
            "mctrader-market": lock_a,
        }
        self._setup_repos(tmp_path, repos)
        with patch.object(check_cross_repo_locks, "WORKSPACE_ROOT", tmp_path):
            assert check_cross_repo_locks.main() == 2
