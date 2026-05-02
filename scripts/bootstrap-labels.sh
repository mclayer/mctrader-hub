#!/usr/bin/env bash
# bootstrap-labels.sh — Plugin이 사용하는 GitHub label 20종 일괄 생성 (1회).
#
# CFP-11 end-to-end 실증에서 발견된 bootstrap drift — 신규 repo에 plugin 적용 시
# type:* / phase:* / gate:* / fix:* / hotfix:* / audit:* 라벨 부재로 Issue Form
# 제출 자체가 실패한다.
#
# 본 스크립트는 idempotent — 기존 라벨은 "already exists" 메시지 후 통과.
#
# Usage:
#   gh auth login   # 사전 인증 필요
#   bash scripts/bootstrap-labels.sh                # 현재 repo
#   bash scripts/bootstrap-labels.sh org/repo       # 명시 repo
#   bash scripts/bootstrap-labels.sh --dry-run      # 라벨 목록만 stdout 출력 (gh 미호출, CFP-33 lint 용)
#
# Exit code: 0 (모두 처리, 일부 already-exists 포함) / 1 (gh 미설치 또는 인증 실패)

set -u

DRY_RUN=0
REPO_ARG=""
if [ $# -ge 1 ]; then
    if [ "$1" = "--dry-run" ]; then
        DRY_RUN=1
    else
        REPO_ARG="--repo $1"
    fi
fi

if [ $DRY_RUN -eq 0 ] && ! command -v gh >/dev/null 2>&1; then
    echo "ERROR: gh CLI 미설치. https://cli.github.com 에서 설치 후 'gh auth login' 실행." >&2
    exit 1
fi

# Idempotent label create — 이미 존재하면 0 반환 (silent).
# --dry-run 모드: gh 미호출, "name|color|desc" tab-separated 출력 → CFP-33 check-label-registry.sh 가 parse.
create_label() {
    local name="$1"
    local color="$2"
    local desc="$3"
    if [ $DRY_RUN -eq 1 ]; then
        printf '%s\t%s\t%s\n' "$name" "$color" "$desc"
        return 0
    fi
    # shellcheck disable=SC2086
    gh label create "$name" --color "$color" --description "$desc" $REPO_ARG 2>/dev/null \
        || gh label edit "$name" --color "$color" --description "$desc" $REPO_ARG 2>/dev/null \
        || echo "  ! $name: create/edit 실패 (권한 문제 가능)"
}

[ $DRY_RUN -eq 0 ] && echo "Plugin label 20종 부트스트랩..."

# type:* (4종)
create_label "type:epic"        "5319e7" "Epic (사용자 요구사항 1건 = Milestone + Issue)"
create_label "type:story"       "0e8a16" "Story (PR 1쌍 = Phase 1 + Phase 2)"
create_label "type:bug"         "d73a4a" "Bug"
create_label "impl-manifest"    "fbca04" "Sub-issue (Impl Manifest 파일 단위)"

# phase:* (7종, single-active)
for p in 요구사항 설계 설계-리뷰 구현 구현-리뷰 구현-테스트 보안-테스트; do
    create_label "phase:$p" "1d76db" "Phase: $p"
done

# gate:* (2종)
create_label "gate:design-review-pass"   "0e8a16" "Design review PASS"
create_label "gate:security-test-pass"   "0e8a16" "Security test PASS"

# fix:* (4종)
for r in 설계-리뷰 구현-리뷰 구현-테스트 보안-테스트; do
    create_label "fix:$r-retry" "e99695" "FIX retry: $r"
done

# hotfix / audit (3종)
create_label "hotfix:minimal"     "ff9999" "Hotfix minimal"
create_label "hotfix:critical"    "ff0000" "Hotfix critical"
create_label "audit:post-hotfix"  "fef2c0" "Post-hotfix audit Story"

if [ $DRY_RUN -eq 0 ]; then
    echo ""
    echo "✓ 20 label 처리 완료. 'gh label list' 로 확인."
fi
