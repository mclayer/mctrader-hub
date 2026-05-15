#!/usr/bin/env python3
"""verify_cross_repo_secret.py — 6 repo MCTRADER_CROSS_REPO_TOKEN secret read 검증.

MCT-177 AC-5 (carry over from MCT-176):
  6 repo (data/engine/web/market/signal-collector/hub) 측
  MCTRADER_CROSS_REPO_TOKEN secret read 검증 후 결과 박제.

NOTE: 본 스크립트는 mctrader-data#65 LAND 후 실행 의무.
      현재 상태 = placeholder (data#65 LAND 대기 중).
      실행 결과는 Story MCT-177 §12 측정 표에 박제.

Usage (data#65 LAND 후):
    python scripts/verify_cross_repo_secret.py

Requirements:
    - gh CLI 로그인 상태 (`gh auth status`)
    - 6 repo 에 대한 secret read 권한 (admin or repo owner)

Exit codes:
    0 — 6 repo 전부 MCTRADER_CROSS_REPO_TOKEN secret 존재 확인
    1 — 1개 이상 누락 (누락 repo 목록 출력)
"""
# TODO(MCT-177): data#65 LAND 후 실행. 현재 placeholder — 6 repo secret verify 로직 미완성.
# 실 구현은 mctrader-data#65 PR 에서 제공 (scripts/verify_cross_repo_secret.py).
# 본 hub 측 파일은 박제 anchor 역할 (AC-5 Story §12 측정 표 참조 경로).

import subprocess
import sys

REPOS = [
    "mclayer/mctrader-data",
    "mclayer/mctrader-engine",
    "mclayer/mctrader-web",
    "mclayer/mctrader-market",
    "mclayer/mctrader-signal-collector",
    "mclayer/mctrader-hub",
]
SECRET_NAME = "MCTRADER_CROSS_REPO_TOKEN"


def check_secret(repo: str) -> bool:
    """gh CLI 로 repo secret list 조회 후 SECRET_NAME 존재 여부 반환."""
    result = subprocess.run(
        ["gh", "secret", "list", "--repo", repo],
        capture_output=True,
        text=True,
    )
    return SECRET_NAME in result.stdout


def main() -> int:
    missing = []
    for repo in REPOS:
        if check_secret(repo):
            print(f"[PASS] {repo}: {SECRET_NAME} 존재")
        else:
            print(f"[FAIL] {repo}: {SECRET_NAME} 부재")
            missing.append(repo)

    if missing:
        print("\n[ERROR] 누락 repo:")
        for r in missing:
            print(f"  - {r}")
        print("\n등록 가이드:")
        print("  gh secret set MCTRADER_CROSS_REPO_TOKEN --repo <repo> --body <token>")
        return 1

    print(f"\n[OK] 6 repo 전부 {SECRET_NAME} 확인 완료")
    return 0


if __name__ == "__main__":
    sys.exit(main())
