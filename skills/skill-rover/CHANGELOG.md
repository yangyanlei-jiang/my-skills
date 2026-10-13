# Changelog

## 0.3.0 — 2026-10-13

Published from `yangyanlei-jiang/my-skills` as `skill-rover-v0.3.0`. The standalone repository remains historical.

- Added read-only `doctor --project DIR --host codex|claude` to diagnose project configuration, pending routing and due reviews. Configuration checks never claim native activation or reset state.
- A replacement that has not been loaded no longer starts a premature review deadline or inflates loaded-skill counts.
- Failed instruction reads no longer commit load timestamps, usage or load history.
- Re-integration updates exact generated hooks for the same script after interpreter/state changes; customized or unrelated hooks are preserved.
- Project integration rejects symlinked configuration and skill parents before writing outside the chosen project. Generated hooks disable bytecode writes with `-B`.
- Malformed lifecycle records, usage lists and reminder timestamps now produce a preserved-state diagnostic; hooks return the documented fail-open response.

Existing version-1 state remains compatible. No automatic state reset, source-skill deletion or background daemon is introduced. The default remains 24 hours from first successful load, with due work handled on the next host event. See the [audit and validation limits](evals/audit-2026-10-13.md).
