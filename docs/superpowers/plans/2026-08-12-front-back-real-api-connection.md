# Front Back Real API Connection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect the frontend room creation and analysis flow to the real backend API while keeping only the model score mocked.

**Architecture:** The frontend creates chat rooms through `POST /api/chat/rooms` and stores the backend-returned `room_id`. Later analysis requests use that backend-created `room_id` with `POST /api/chat/analyze`. The backend remains the source of truth for `room_id`, `analysis_id`, risk level, notification email, and delivery metadata.

**Tech Stack:** Plain HTML/CSS/JavaScript frontend, FastAPI backend, pytest contract tests, Node syntax validation.

## Global Constraints

- Frontend must not create `room_id`.
- Room creation must send real `room_name` and required `notification_email`.
- Analysis request must send only backend-created `room_id` and `messages`.
- Model output can remain mock; frontend-backend data must be real API data.

---

### Task 1: Frontend Contract Tests

**Files:**
- Modify: `test/test_phase_07_frontend_runtime.py`

**Interfaces:**
- Consumes: `front/app.js`
- Produces: tests that fail when room creation API is skipped or frontend-generated room IDs are used for analysis

- [ ] **Step 1: Write failing tests**

Add tests that assert the frontend contains the room creation endpoint, sends `notification_email`, does not create room IDs locally, and does not initialize a hardcoded analyzable `demo_room`.

- [ ] **Step 2: Run tests to verify failure**

Run: `python3 -m pytest test/test_phase_07_frontend_runtime.py -q`

Expected: FAIL because current frontend only calls `/api/chat/analyze` and creates room IDs in `createRoomNameId`.

### Task 2: Frontend API Wiring

**Files:**
- Modify: `front/app.js`

**Interfaces:**
- Consumes: `POST /api/chat/rooms` response with `room_id`, `room_name`, `notification_email`
- Produces: chat room state whose `room_id` always comes from backend

- [ ] **Step 1: Add room API URL**

Define `createRoomApiUrl = "http://127.0.0.1:8000/api/chat/rooms"`.

- [ ] **Step 2: Make room creation asynchronous**

`createChatRoom()` validates `room_name` and `notification_email`, calls `POST /api/chat/rooms`, and stores the response.

- [ ] **Step 3: Remove frontend room ID generation from the create path**

New room objects use `response.room_id`, `response.room_name`, and `response.notification_email`.

- [ ] **Step 4: Prevent analysis before a backend room exists**

Initial state starts with no active room. Message input and analysis require a selected backend-created room.

### Task 3: Verification

**Files:**
- Modify: `front_통합_테스트_체크리스트.md`

**Interfaces:**
- Consumes: local frontend and backend servers
- Produces: documented verification outcome

- [ ] **Step 1: Run targeted frontend tests**

Run: `python3 -m pytest test/test_phase_07_frontend_runtime.py -q`

- [ ] **Step 2: Run full test suite**

Run: `python3 -m pytest test -q`

- [ ] **Step 3: Validate JS syntax**

Run: `node --check front/app.js`

- [ ] **Step 4: Run local API flow**

Start latest backend, then confirm frontend event flow sends `POST /api/chat/rooms` before `POST /api/chat/analyze`.
