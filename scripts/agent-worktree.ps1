#Requires -Version 5.1
<#
.SYNOPSIS
    ADR-019 D1: git worktree-based agent isolation script

.DESCRIPTION
    Creates or removes an isolated git worktree when 2+ agents share the same
    repository working directory concurrently. Each worktree maps to a sanitized
    branch name under BasePath (.worktrees by default).

.PARAMETER Branch
    Branch name for the worktree (required).

.PARAMETER BasePath
    Root directory for worktrees (default: .worktrees).

.PARAMETER Mode
    create - provision a new worktree; cleanup - remove an existing one.

.PARAMETER BaseRef
    Base ref when creating a new branch (default: HEAD).

.EXAMPLE
    # Existing remote branch
    .\agent-worktree.ps1 -Branch "feat/foo"

    # New branch based on main
    .\agent-worktree.ps1 -Branch "feat/bar" -BaseRef "main"

    # Remove worktree
    .\agent-worktree.ps1 -Branch "feat/foo" -Mode cleanup
#>

param(
    [Parameter(Mandatory)][string]$Branch,
    [string]$BasePath = ".worktrees",
    [ValidateSet("create", "cleanup")][string]$Mode = "create",
    [string]$BaseRef = "HEAD"
)

$ErrorActionPreference = "Stop"

# Replace slashes with hyphens to produce a filesystem-safe name
$sanitized = $Branch -replace '/', '-'
$worktreePath = Join-Path $BasePath $sanitized

function Get-AbsolutePath {
    param([string]$Path)
    return [System.IO.Path]::GetFullPath($Path)
}

if ($Mode -eq "create") {
    Write-Host "[Worktree] === Create mode start ==="
    Write-Host "[Worktree] Branch    : $Branch"
    Write-Host "[Worktree] Sanitized : $sanitized"
    Write-Host "[Worktree] Path      : $worktreePath"
    Write-Host "[Worktree] BaseRef   : $BaseRef"

    # Step 1: prune stale worktree entries first
    Write-Host "[Worktree] Pruning stale worktree entries (git worktree prune)..."
    git worktree prune
    if (-not $?) {
        Write-Warning "[Worktree] git worktree prune failed — continuing anyway."
    }

    # Step 2: check whether the branch already exists on the remote
    Write-Host "[Worktree] Checking remote branch existence..."
    $remoteRef = git ls-remote --heads origin $Branch
    $remoteExists = (-not [string]::IsNullOrWhiteSpace($remoteRef))

    if ($remoteExists) {
        Write-Host "[Worktree] Remote branch found — creating worktree from origin/$Branch"
        git worktree add $worktreePath "origin/$Branch"
    } else {
        Write-Host "[Worktree] Remote branch not found — creating new branch '$Branch' from $BaseRef"
        git worktree add -b $Branch $worktreePath $BaseRef
    }

    if (-not $?) {
        Write-Error "[Worktree] Failed to create worktree."
        exit 1
    }

    $absolutePath = Get-AbsolutePath $worktreePath
    Write-Host "[Worktree] Created: $absolutePath"

    # Output absolute path as the last line of stdout for callers to capture
    $absolutePath

} elseif ($Mode -eq "cleanup") {
    Write-Host "[Worktree] === Cleanup mode start ==="
    Write-Host "[Worktree] Branch    : $Branch"
    Write-Host "[Worktree] Sanitized : $sanitized"
    Write-Host "[Worktree] Path      : $worktreePath"

    $absolutePath = Get-AbsolutePath $worktreePath

    # Gracefully handle missing worktree directory
    if (-not (Test-Path $worktreePath)) {
        Write-Host "[Worktree] Worktree path not found — skipping removal: $absolutePath"
    } else {
        # Step 1: attempt normal removal, fall back to --force
        Write-Host "[Worktree] Removing worktree: $worktreePath"
        git worktree remove $worktreePath
        if (-not $?) {
            Write-Host "[Worktree] Normal removal failed — retrying with --force..."
            git worktree remove --force $worktreePath
            if (-not $?) {
                Write-Error "[Worktree] --force removal also failed: $worktreePath"
                exit 1
            }
        }
        Write-Host "[Worktree] Removed: $absolutePath"
    }

    # Step 2: prune dangling worktree references
    Write-Host "[Worktree] Pruning orphaned worktree references (git worktree prune)..."
    git worktree prune
    if (-not $?) {
        Write-Warning "[Worktree] git worktree prune failed — continuing anyway."
    }

    Write-Host "[Worktree] Cleanup complete: $Branch ($sanitized)"
}
