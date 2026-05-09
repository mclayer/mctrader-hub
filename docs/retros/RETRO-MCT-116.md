# RETRO: MCT-116 ADR-018 Audit (mctrader-engine)

**Date:** 2026-05-09  
**Story:** MCT-116  
**Status:** Completed  
**PR:** mctrader-engine#43 (merged)  
**Test Result:** 768 passed, 1 pre-existing failure, 3 skipped

---

## What Went Well

1. **Comprehensive pattern sweep** — ADR-018 D1-D7 audit identified 3 violation categories (D2, D3, D5) across 7 files
2. **Code review caught critical fsync gap** — Initial `_write_json_atomic` implementation was missing `fsync`, violating ADR-018 D5 explicit requirement. Review caught this before merge
3. **Smart refactoring** — Eliminated code duplication by consolidating 3 ad-hoc fsync+rename implementations into shared `_io.py` module
4. **Existing codebase patterns identified** — `wfo/decision_group.py` and `wfo/promote/ack.py` already had correct atomic write patterns (with fsync), used as reference

---

## What Could Be Improved

1. **Initial scan incomplete** — `paper_runner.py` non-atomic write was missed in first pass, only caught during code review. Need checklist: explicitly scan all `*runner*.py` and `cli.py` for file I/O
2. **Missing fsync on first attempt** — Implementation forgot D5 explicitly requires `fsync` before `os.replace`, despite existing correct patterns in codebase. Suggests: reference pattern scan step before implementation
3. **Branch race incident** — Implementer subagent switched to `feat/mct-112-pr-template-adr018` instead of correct `feat/mct-116-adr018-audit-engine`, requiring cherry-pick recovery. Blocked by parallel session workspace sharing

---

## Patterns & ADRs Reinforced

- **ADR-018 D5 (Atomic Writes):** `fsync()` is not optional—required for durability guarantee across all file writes (not just `os.replace`)
- **Code duplication as warning signal** — Multiple implementations of same pattern across codebase = missing shared utility, not feature variation
- **Review-as-safety-net** — Code review caught both `fsync` gap and missed file locations that initial scan missed

---

## Action Items for Future Audit Stories

| Action | Owner | Priority |
|--------|-------|----------|
| Create audit checklist template (file locations, pattern detection) | PMO | High |
| Before implementing ADR fix, scan codebase for existing correct patterns | Dev | High |
| Enforce branch consistency check pre-implementation in parallel session scenarios | Orchestrator | Medium |
| Add ADR-018 D5 reference example to `_io.py` module docstring | Dev | Low |

---

## Session Impact

- **Token efficiency:** Story scope well-defined, minimal re-planning needed
- **Iteration count:** 2 (initial implementation + fsync fix)
- **Cross-story pattern:** Third consecutive audit story with "missing shared utility" finding — suggests template/checklist for audits reduces rework
