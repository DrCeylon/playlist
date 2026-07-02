# Phase 4.8 — Session history

Local history for generation/import sessions in Resonance.

## Scope (MVP)

- Persistent local sessions (`data/history/sessions.json`)
- History list screen in macOS sidebar (replaces placeholder)
- Session detail panel (request/preview/import/diagnostics summary)
- Bridge commands:
  - `list_history`
  - `get_history_session`
  - `delete_history_session`
  - `clear_history`
  - `replay_generation`
  - `export_history_session`

## Storage format

- File: `data/history/sessions.json`
- Versioned envelope:
  - `schema_version`
  - `sessions[]`
- Atomic write via temp-file replace
- Corruption tolerant:
  - invalid JSON → returns empty list
  - unsupported future `schema_version` → safe empty fallback
- No secrets, no tokens, no provider-specific sensitive IDs

## Session payload (provider-neutral)

- `session_id`
- `started_at_iso`
- `finished_at_iso`
- `playlist_name`
- `provider_id`
- `status`
- `track_count`
- `added_count`
- `skipped_count`
- `not_found_count`
- `error_count`
- `duration_ms`
- `text_report_path`
- `json_report_path`
- `diagnostics`
- `generation_request`
- `generation_result`
- `import_result`

`persistent_id` is stripped during serialization.

## UI actions (4.8 MVP)

- ✅ Refresh history
- ✅ View session details
- ✅ Replay generation from stored request
- ✅ Delete local history entry
- ✅ Clear local history
- ✅ Export metadata snapshot
- ⏳ Re-import from detail: explicit “prévu” message (4.8b)

## Retention

No automatic pruning in 4.8.
Retention policy can be added later (count/date based) without storage migration.

## Limitations

- Local-only history (single machine workspace)
- No cross-device sync
- No destructive provider actions (never deletes Apple Music playlist/library)

