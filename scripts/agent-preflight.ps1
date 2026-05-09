#Requires -Version 5.1
<#
.SYNOPSIS
    ADR-019 D2/D3/D4/D5 — Parallel agent preflight: Python 3.12 check, editable install, branch verification.

.DESCRIPTION
    D2: Verify py -3.12 is available.
    D3: Run editable install (mctrader-hub is skipped — not a Python package).
    D4: Verify current git branch matches $Branch (when provided).
    D5: Applies to 6-repo scope: mctrader-hub, mctrader-market, mctrader-market-bithumb,
        mctrader-data, mctrader-engine, mctrader-web.

.PARAMETER RepoPath
    Path to the repository root. Defaults to current directory.

.PARAMETER Branch
    Expected branch name. When provided, the script verifies current branch matches.

.PARAMETER UseWorktree
    Reserved flag for worktree-aware invocations (informational only).

.EXAMPLE
    .\agent-preflight.ps1 -RepoPath "C:\workspace\mclayer\mctrader-data" -Branch "feat/mct-118"
#>
param(
    [string]$RepoPath = ".",
    [string]$Branch = "",
    [switch]$UseWorktree
)

$ErrorActionPreference = "Stop"

Write-Host "[Preflight] Starting agent preflight for $RepoPath"

# ── D2: Python 3.12 availability ────────────────────────────────────────────
$pyVersion = py -3.12 --version 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "py -3.12 not found. Python 3.12가 설치되지 않았습니다."
}
Write-Host "[Preflight D2] Python 3.12 OK: $pyVersion"

# ── D3: Editable install ─────────────────────────────────────────────────────
# mctrader-hub is not a Python package — skip editable install.
# D5 scope: mctrader-hub, mctrader-market, mctrader-market-bithumb,
#           mctrader-data, mctrader-engine, mctrader-web
$resolvedPath = (Resolve-Path $RepoPath).Path
$repoName = Split-Path -Leaf $resolvedPath

if ($repoName -eq "mctrader-hub") {
    Write-Host "[Preflight D3] Skipping editable install — mctrader-hub is not a Python package."
} else {
    Write-Host "[Preflight D3] Running editable install for $repoName ..."
    $installTarget = $resolvedPath + "[dev]"
    py -3.12 -m pip install -e $installTarget --quiet
    if ($LASTEXITCODE -ne 0) {
        throw "Editable install failed for $repoName at $resolvedPath"
    }
    Write-Host "[Preflight D3] Editable install OK: $repoName"
}

# ── D4: Branch verification ──────────────────────────────────────────────────
if ($Branch -ne "") {
    $current = git -C $RepoPath branch --show-current 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to determine current branch in $RepoPath"
    }
    $current = $current.Trim()
    if ($current -ne $Branch) {
        throw "BRANCH MISMATCH: expected=$Branch, current=$current — aborting"
    }
    Write-Host "[Preflight D4] Branch OK: $current"
} else {
    Write-Host "[Preflight D4] Branch check skipped (no -Branch parameter provided)."
}

Write-Host "[Preflight] Done."
