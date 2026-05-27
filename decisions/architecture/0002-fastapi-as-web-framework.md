# ADR 0002 — FastAPI as the web framework

**Status:** Accepted. Source: conversation.

## Decision

The service is built on FastAPI. Pydantic models handle request
validation; background tasks (via FastAPI's `BackgroundTasks`)
handle async build execution.

## Implication

New routes are added as FastAPI path-operation functions. Request
bodies are declared as `BaseModel` subclasses. Do not introduce a
second framework (Flask, Django, etc.).
