# SilentGuard Single Local Runtime Implementation Plan

> **현재 상태:** 이 문서는 2026-08-11 단일 `app/` 런타임 계획 기록이다. 최신 실행 구조는 `front/`, `back/`, `ai/` 분리 구조이며, 최신 API 계약은 `POST /api/chat/rooms`, `GET /api/chat/rooms`, `POST /api/chat/analyze` 순서와 루트 `data_schema.md`를 따른다.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the NVIDIA frontend, mock model path, Agent analysis, notification status, and API from one root `app/` server while preserving the source folders.

**Architecture:** Root `app/` becomes the only runtime package. It serves the copied NVIDIA frontend at `/` and exposes `POST /api/chat/analyze`; it invokes the existing root Agent implementation through an adapter only for `warning` and `immediate`. The mock scorer deterministically maps the four documented demo conversations to the required probability bands without acting as a semantic production model.

**Tech Stack:** Python 3.13 virtual environment at `/Users/mac/venvs/agent`, FastAPI, Pydantic, Uvicorn, pytest, vanilla JavaScript.

## Global Constraints

- Keep `Nvidia_test/` source files unchanged and preserve them as reference material.
- Use the contract in `agent/data_schema.md` and `agent/docs/phase_01_*` through `phase_07_*`.
- Root `app/` is the only runtime location; no second frontend or Agent HTTP server remains necessary.
- The Agent must not make final determinations about school violence or participant roles.
- Store executable phase evidence in root `test/`.

---

### Task 1: Define root API contract tests

**Files:**
- Create: `test/test_phase_01_to_03_api_contract.py`
- Modify: `app/api.py`

**Interfaces:**
- Consumes: a JSON request with `room_id` and `messages`.
- Produces: `POST /api/chat/analyze` response with `analysis_id`, probability, and server-calculated risk level.

- [ ] Write tests for accepted Phase 01 payloads, ordered Phase 02 payload forwarding, and Phase 03 numeric probability output.
- [ ] Run the tests and verify they fail because root API code does not exist.
- [ ] Implement request validation, message ordering, deterministic mock scoring, and risk-level mapping.
- [ ] Run the tests and verify they pass.

### Task 2: Connect root API to the Agent and notification adapter

**Files:**
- Create: `app/api.py`
- Create: `app/mock_model.py`
- Modify: `app/silentguard_agent.py`
- Create: `test/test_phase_04_to_06_integration.py`

**Interfaces:**
- Consumes: Phase 04 Agent request containing analysis fields and original messages.
- Produces: Phase 05 incident JSON and Phase 06 local `notification_delivery` JSON.

- [ ] Write tests proving normal/caution bypass the Agent and warning/immediate pass only Phase 04 fields to it.
- [ ] Run the tests and verify they fail against the missing root API integration.
- [ ] Implement the adapter, Agent result validation, and local-only notification state.
- [ ] Run the tests and verify they pass.

### Task 3: Serve the NVIDIA frontend from the root runtime

**Files:**
- Create: `app/frontend/index.html`
- Create: `app/frontend/app.js`
- Create: `app/frontend/style.css`
- Modify: `app/api.py`
- Create: `test/test_phase_07_frontend_runtime.py`

**Interfaces:**
- Consumes: browser requests for `/`, `/app.js`, `/style.css` and the Phase 07 API response.
- Produces: one same-origin user interface and relative `/api/chat/analyze` request.

- [ ] Write route tests for the frontend document and assets.
- [ ] Run the tests and verify they fail because root routes are absent.
- [ ] Copy the existing NVIDIA frontend to root `app/frontend/` and serve it from the root FastAPI app.
- [ ] Run route and JavaScript syntax tests and verify they pass.

### Task 4: Execute phase checks and record evidence

**Files:**
- Create: `test/phase_01_frontend_to_backend_result.md`
- Create: `test/phase_02_backend_to_model_result.md`
- Create: `test/phase_03_model_to_backend_result.md`
- Create: `test/phase_04_backend_to_agent_result.md`
- Create: `test/phase_05_agent_to_backend_result.md`
- Create: `test/phase_06_backend_to_notification_result.md`
- Create: `test/phase_07_backend_to_frontend_result.md`

**Interfaces:**
- Consumes: the running root FastAPI app and phase test cases.
- Produces: factual per-phase commands, outcome, and remaining issues.

- [ ] Execute the full test suite with the specified virtual environment.
- [ ] Start one root Uvicorn server on an unused local port and exercise normal and immediate requests.
- [ ] Check HTML, JavaScript, and API responses use the documented routes and field names.
- [ ] Record actual command output summaries in the seven test reports.
- [ ] Update relevant Agent Phase status and checklist records with final results.
