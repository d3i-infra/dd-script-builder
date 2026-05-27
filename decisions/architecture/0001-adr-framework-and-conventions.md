# ADR 0001 — ADR framework and conventions

**Status:** Accepted. Source: conversation.

## Decision

Architectural decisions for this project are recorded as ADRs
under `decisions/architecture/`. The framework follows five
rules.

1. **Location.** ADRs live in `/decisions/architecture/`
   relative to the repo root.
2. **Consultation.** ADRs are consulted before writing code.
   The relevant ADR(s) for the area being touched are read at
   the start of the work.
3. **Format.** Markdown. Filenames carry a four-digit
   numeric prefix incrementing from `0001`, followed by a
   topic-rich slug — enough context that an LLM (or human)
   can recognise the topic from the filename alone and load
   only what's relevant. Example: `0003-in-memory-build-store.md`,
   not `0003-storage.md`.
4. **Conversational ADRs are escalated.** When a decision
   surfaces inside a conversation that warrants an ADR, the
   user is prompted to escalate it. ADRs are kept concise to
   avoid context bloat — the audience is an LLM loading the
   file mid-task, not a human reading top-to-bottom.
5. **Coherence.** ADRs are kept coherent. When a new ADR
   supersedes or amends an earlier one, the earlier one's
   **Status** is updated to `Superseded by NNNN` (or
   `Amended by NNNN`) and the new ADR notes what it replaces.
   Contradictory ADRs are not allowed to coexist.

## ADR shape

Each ADR follows this shape:

```
# ADR NNNN — Topic

**Status:** Accepted | Superseded by NNNN | Amended by NNNN.
Source: <where the decision was made — conversation, design doc,
PR review>.

## Decision

<1–3 sentence statement of what was decided>

## Implication

<1–3 sentences on what this means for code — the operational
consequence the next contributor needs to act on>
```

Optional sections (`## Context`, `## Alternatives`,
`## Notes`) may be added when load-bearing, but the goal is
brevity. If an ADR runs past one screen, it is probably two
ADRs.

## Implication

A future contributor (LLM or human) discovers and applies
architectural decisions by:

1. Reading `decisions/architecture/README.md` to see the
   index of topics.
2. Loading the ADR(s) relevant to the area being touched —
   selectively, by topic-rich filename.
3. Treating the ADR's **Decision** as the authoritative
   default; a clearly better local design overrides, but the
   override is recorded as a new or amended ADR.
