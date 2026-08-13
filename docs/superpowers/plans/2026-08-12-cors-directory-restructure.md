# SilentGuard CORS Directory Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the local MVP into `front/`, `back/`, and `ai/`, move project-wide docs/schema to the root, preserve legacy NVIDIA work, and verify the frontend talks to the backend through local CORS.

**Architecture:** `front/` is a static browser client on port `5173`. `back/` is the FastAPI API server on port `8000`, owns CORS, request validation, risk-level mapping, and orchestration. `ai/` owns mock/model scoring, Agent analysis, incident notification formatting, and OpenAI config normalization.

**Tech Stack:** Python 3, FastAPI, pytest, static frontend JavaScript, `python -m http.server`.

**Execution Status:** Completed on 2026-08-12. Latest contract update: chat rooms are created through `POST /api/chat/rooms` with required `room_name` and `notification_email`; analysis uses the backend-created `room_id`. Current verification: `python3 -m pytest test -q` passed with 17 tests.

## Global Constraints

- Work in `/Users/mac/Desktop/Team/silentguard`; this folder is not a git repository, so skip worktree and commit steps.
- Use root `data_schema.md` as the project-wide data contract after it is moved from `agent/data_schema.md`.
- Keep `agent/phases/` as AI-only phase records.
- Move `agent/docs/` project phase docs to root `docs/`, preserving `docs/superpowers/`.
- Preserve all old `Nvidia_test/` content under `legacy/Nvidia_test/`.
- Backend CORS must allow `http://127.0.0.1:5173` and `http://localhost:5173`.
- Frontend must call `http://127.0.0.1:8000/api/chat/rooms` before analysis, then call `http://127.0.0.1:8000/api/chat/analyze` with the backend-created `room_id`.
- Add Korean one-line comments immediately above any new function or method declarations.
- Do not make semantic risk judgments in `back/`; `ai/` owns Agent risk segments and incidents.
- Actual tests and phase result Markdown stay in `test/`; phase contracts live in root `docs/phase_*.md`.

---

### Task 1: Add Failing Contract Tests For CORS Split

**Files:**
- Modify: `test/test_phase_07_frontend_runtime.py`
- Modify: `test/test_root_runtime_runner.py`

**Interfaces:**
- Consumes: future `back.api.app`, future `front/app.js`, future `back.run_local_demo`.
- Produces: failing checks that require backend CORS and frontend absolute API URL.

- [ ] **Step 1: Change phase 07 runtime tests**

Replace imports and assertions so the test imports `back.api.app`, sends an `OPTIONS /api/chat/analyze` request with `Origin: http://127.0.0.1:5173`, and reads `front/app.js`.

- [ ] **Step 2: Change local runner test**

Assert `back.run_local_demo.run()` calls uvicorn with `"back.api:app"`, host `"127.0.0.1"`, and port `8000`.

- [ ] **Step 3: Verify RED**

Run:

```bash
python3 -m pytest test/test_phase_07_frontend_runtime.py test/test_root_runtime_runner.py -q
```

Expected: fail because `back/` and `front/` do not exist yet.

### Task 2: Move Runtime Code Into `back/`, `ai/`, And `front/`

**Files:**
- Create: `back/__init__.py`
- Move: `app/api.py` to `back/api.py`
- Move: `app/run_local_demo.py` to `back/run_local_demo.py`
- Create: `ai/__init__.py`
- Create: `ai/model/__init__.py`
- Create: `ai/agent_analysis/__init__.py`
- Create: `ai/notification/__init__.py`
- Create: `ai/schemas/__init__.py`
- Move: `app/config.py` to `ai/config.py`
- Move: `app/mock_model.py` to `ai/model/mock_model.py`
- Move: `app/silentguard_agent.py` to `ai/agent_analysis/silentguard_agent.py`
- Move: `app/contract.py` to `ai/schemas/contract.py`
- Move: `app/risk_segments.py` to `ai/agent_analysis/risk_segments.py`
- Move: `app/incident_notification.py` to `ai/notification/incident_notification.py`
- Move: `app/frontend/index.html` to `front/index.html`
- Move: `app/frontend/app.js` to `front/app.js`
- Move: `app/frontend/style.css` to `front/style.css`
- Preserve: remaining `app/` phase/demo files by moving them to `ai/legacy_app/`

**Interfaces:**
- Consumes: existing behavior from `app.*`.
- Produces: `back.api.app`, `back.run_local_demo.run`, `ai.*` imports, and `front/` static assets.

- [ ] **Step 1: Move files without deleting history**

Create destination package directories and move files. Keep non-runtime old `app/` scripts/tests/output/sample files under `ai/legacy_app/`.

- [ ] **Step 2: Update Python imports**

`back/api.py` imports `get_mock_bullying_probability` from `ai.model.mock_model` and `SilentGuardAgent` from `ai.agent_analysis.silentguard_agent`.

`ai/agent_analysis/silentguard_agent.py` imports config from `ai.config`, contract from `ai.schemas.contract`, risk helpers from `ai.agent_analysis.risk_segments`, and notification helpers from `ai.notification.incident_notification`.

- [ ] **Step 3: Remove backend static frontend routes**

`back/api.py` keeps only API behavior and request validation; `GET /`, `GET /app.js`, and `GET /style.css` are no longer backend routes.

### Task 3: Add CORS And Frontend Absolute API URL

**Files:**
- Modify: `back/api.py`
- Modify: `front/app.js`

**Interfaces:**
- Consumes: `FastAPI()` app and browser JavaScript submit flow.
- Produces: CORS-enabled API and frontend calls to `http://127.0.0.1:8000/api/chat/rooms` and `http://127.0.0.1:8000/api/chat/analyze`.

- [ ] **Step 1: Add FastAPI CORS middleware**

Configure `CORSMiddleware` on `app` with origins `http://127.0.0.1:5173` and `http://localhost:5173`, all methods, all headers, and no credentials.

- [ ] **Step 2: Update frontend fetch endpoint**

Replace same-origin API calls with absolute API URLs under `http://127.0.0.1:8000`.

- [ ] **Step 3: Verify GREEN for CORS tests**

Run:

```bash
python3 -m pytest test/test_phase_07_frontend_runtime.py test/test_root_runtime_runner.py -q
node --check front/app.js
```

Expected: pass.

### Task 4: Move Project Docs, Schema, And Legacy NVIDIA Folder

**Files:**
- Move: `agent/docs/phase_*.md` to `docs/phase_*.md`
- Move: `agent/data_schema.md` to `data_schema.md`
- Move: `Nvidia_test/` to `legacy/Nvidia_test/`

**Interfaces:**
- Consumes: existing project-wide docs and schema.
- Produces: root-level project docs/schema while preserving `docs/superpowers/` and all NVIDIA historical files.

- [ ] **Step 1: Move docs and schema**

Move only project-wide docs from `agent/docs/`; do not move `agent/phases/`.

- [ ] **Step 2: Move NVIDIA history**

Create `legacy/` and move `Nvidia_test/` into `legacy/Nvidia_test/`.

### Task 5: Update Tests And Phase Result Records

**Files:**
- Modify: `test/test_phase_01_to_03_api_contract.py`
- Modify: `test/test_phase_04_to_06_integration.py`
- Modify: `test/test_openai_config.py`
- Modify: `test/phase_01_frontend_to_backend_result.md`
- Modify: `test/phase_02_backend_to_model_result.md`
- Modify: `test/phase_03_model_to_backend_result.md`
- Modify: `test/phase_04_backend_to_agent_result.md`
- Modify: `test/phase_05_agent_to_backend_result.md`
- Modify: `test/phase_06_backend_to_notification_result.md`
- Modify: `test/phase_07_backend_to_frontend_result.md`
- Modify: `test/openai_config_normalization_result.md`

**Interfaces:**
- Consumes: new `back.*` and `ai.*` paths.
- Produces: passing test suite and accurate phase result Markdown.

- [ ] **Step 1: Update import paths in tests**

Use `back.api` for API tests, `ai.config` for config tests, and new `ai.*` paths where old `app.*` paths remain.

- [ ] **Step 2: Update phase result Markdown**

Record the CORS split, new paths, and verification commands in the existing `test/*.md` phase result files.

### Task 6: Update Root Instructions And README

**Files:**
- Modify: `AGENTS.md`
- Replace: `README.md`
- Modify: `agent/phases/phase_07_status.md`

**Interfaces:**
- Consumes: approved directory design and root `data_schema.md`.
- Produces: current contributor/run/test instructions.

- [ ] **Step 1: Update AGENTS.md**

Keep Notion links, work-start rules, development principles, function rules, and section 10 rules. Update service overview, role separation, directory paths, and add root `data_schema.md` as the project-wide schema rule.

- [ ] **Step 2: Replace README.md**

Write the current directory structure, backend/frontend run commands, browser URL, test command, and legacy preservation note.

- [ ] **Step 3: Update AI phase status**

Update `agent/phases/phase_07_status.md` so it no longer claims the frontend is served from backend same-origin.

### Task 7: Full Verification And Local Server Check

**Files:**
- No source edits unless verification exposes a bug.

**Interfaces:**
- Consumes: final tree.
- Produces: evidence that the local CORS split works.

- [ ] **Step 1: Run full automated tests**

```bash
python3 -m pytest test -q
node --check front/app.js
```

- [ ] **Step 2: Start backend and frontend locally**

Backend:

```bash
python3 -m back.run_local_demo
```

Frontend:

```bash
python3 -m http.server 5173 -d front
```

- [ ] **Step 3: Verify HTTP behavior**

Use `curl` to confirm:

```bash
curl -i -X OPTIONS http://127.0.0.1:8000/api/chat/analyze -H 'Origin: http://127.0.0.1:5173' -H 'Access-Control-Request-Method: POST'
curl -s http://127.0.0.1:5173/
```

Expected: backend returns `access-control-allow-origin: http://127.0.0.1:5173`; frontend returns `index.html`.

- [ ] **Step 4: Report run instructions**

Tell the user to open `http://127.0.0.1:5173` while backend `8000` and frontend `5173` are running.
