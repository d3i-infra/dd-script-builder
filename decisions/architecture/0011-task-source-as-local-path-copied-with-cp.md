# ADR 0011 — TASK_SOURCE is a local filesystem path; repo is copied with `cp -r`

**Status:** Accepted. Source: conversation.

## Decision

`TASK_SOURCE` is a path to a pre-cloned local directory, not a
remote URL. Each build copies it into a fresh temp dir using
`cp -r {TASK_SOURCE}/. {tmp_dir}` rather than cloning via git.

## Implication

Deployment must supply a pre-cloned, up-to-date checkout at
`TASK_SOURCE`. The service does not fetch or pull; keeping
`TASK_SOURCE` current is an operational responsibility outside this
service. Do not replace the `cp -r` step with `git clone` without
a new ADR — the current model avoids network calls during builds
and makes repo management explicit.
