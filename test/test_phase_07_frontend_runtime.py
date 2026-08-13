from pathlib import Path
import subprocess
import textwrap

from fastapi.testclient import TestClient

from back.api import app


# Phase 07에서 백엔드가 프론트 로컬 출처의 CORS 요청을 허용하는지 확인한다.
def test_phase_07_backend_allows_frontend_cors_origin() -> None:
    client = TestClient(app)

    response = client.options(
        "/api/chat/analyze",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"


# Phase 07에서 프론트가 백엔드 절대 URL로 API를 호출하는지 확인한다.
def test_phase_07_frontend_calls_backend_absolute_api_url() -> None:
    javascript = Path("front/app.js").read_text(encoding="utf-8")

    assert "http://127.0.0.1:8000/api/chat/analyze" in javascript
    assert 'fetch("/api/chat/analyze"' not in javascript


# Phase 07에서 프론트 방 생성과 분석 버튼이 실제 백엔드 API 계약 순서대로 요청을 만드는지 확인한다.
def test_phase_07_frontend_creates_room_before_analyze_with_backend_room_id() -> None:
    script = textwrap.dedent(
        """
        import { readFileSync } from 'node:fs';
        import vm from 'node:vm';

        const code = readFileSync('front/app.js', 'utf8');
        const fetchCalls = [];
        const errors = [];

        class FakeClassList {
            add() {}
            remove() {}
            toggle() { return false; }
        }

        class FakeElement {
            constructor(id = '') {
                this.id = id;
                this.value = '';
                this.textContent = '';
                this.innerHTML = '';
                this.className = '';
                this.disabled = false;
                this.dataset = {};
                this.children = [];
                this.listeners = {};
                this.classList = new FakeClassList();
            }

            addEventListener(type, listener) {
                if (!this.listeners[type]) {
                    this.listeners[type] = [];
                }
                this.listeners[type].push(listener);
            }

            appendChild(child) {
                this.children.push(child);
                return child;
            }

            focus() {}
            querySelector() { return null; }
            querySelectorAll() { return []; }

            async trigger(type, event = {}) {
                for (const listener of this.listeners[type] || []) {
                    await listener({
                        preventDefault() {},
                        stopPropagation() {},
                        ...event
                    });
                }
            }
        }

        const elements = new Map();
        function getElement(id) {
            if (!elements.has(id)) {
                elements.set(id, new FakeElement(id));
            }
            return elements.get(id);
        }

        const context = {
            console: {
                error: (...args) => errors.push(args.map(String).join(' ')),
                log: () => {}
            },
            alert: (message) => errors.push(`alert:${message}`),
            setTimeout,
            clearTimeout,
            encodeURIComponent,
            Date,
            Math,
            String,
            Number,
            Boolean,
            Array,
            Object,
            RegExp,
            JSON,
            CSS: { escape: (value) => String(value) },
            window: { location: { href: '' } },
            document: {
                getElementById: getElement,
                querySelectorAll: () => [],
                createElement: (tagName) => new FakeElement(tagName)
            },
            fetch: async (url, options = {}) => {
                const parsedBody = options.body ? JSON.parse(options.body) : null;
                fetchCalls.push({
                    url,
                    method: options.method,
                    body: parsedBody
                });

                if (url.endsWith('/api/chat/rooms')) {
                    return {
                        ok: true,
                        status: 200,
                        json: async () => ({
                            room_id: 'room_20260812143005_a1b2c3',
                            room_name: parsedBody.room_name,
                            notification_email: parsedBody.notification_email,
                            created_at: '2026-08-12T14:30:05+09:00'
                        })
                    };
                }

                if (url.endsWith('/api/chat/analyze')) {
                    return {
                        ok: true,
                        status: 200,
                        json: async () => ({
                            analysis_id: 'analysis_room_20260812143005_a1b2c3_20260812143100_d4e5f6',
                            room_id: parsedBody.room_id,
                            room_name: '프론트 계약 테스트 방',
                            notification_email: 'teacher@example.com',
                            messages: parsedBody.messages,
                            bullying_probability: 0.42,
                            risk_level: 'normal',
                            incident: {},
                            risk_segments: [],
                            agent_response: {},
                            notification_delivery: {
                                channel: 'none',
                                status: 'not_configured',
                                recipient_email: 'teacher@example.com'
                            }
                        })
                    };
                }

                throw new Error(`unexpected fetch url: ${url}`);
            }
        };

        vm.createContext(context);
        vm.runInContext(code, context);

        getElement('new-room-name').value = '프론트 계약 테스트 방';
        getElement('room-notification-email').value = 'teacher@example.com';
        await getElement('create-room-btn').trigger('click');

        getElement('sender').value = 'A';
        getElement('message').value = '오늘 회의 자료 확인했어?';
        await getElement('add-message-btn').trigger('click');
        await getElement('analyze-btn').trigger('click');

        const roomRequest = fetchCalls[0];
        const analyzeRequest = fetchCalls[1];

        if (fetchCalls.length !== 2) {
            throw new Error(`expected 2 fetch calls, got ${fetchCalls.length}: ${JSON.stringify(fetchCalls)}`);
        }

        if (!roomRequest.url.endsWith('/api/chat/rooms')) {
            throw new Error(`first request must create room: ${JSON.stringify(roomRequest)}`);
        }

        if (roomRequest.body.room_name !== '프론트 계약 테스트 방') {
            throw new Error(`room_name not sent from input: ${JSON.stringify(roomRequest.body)}`);
        }

        if (roomRequest.body.notification_email !== 'teacher@example.com') {
            throw new Error(`notification_email not sent from input: ${JSON.stringify(roomRequest.body)}`);
        }

        if (!analyzeRequest.url.endsWith('/api/chat/analyze')) {
            throw new Error(`second request must analyze: ${JSON.stringify(analyzeRequest)}`);
        }

        if (analyzeRequest.body.room_id !== 'room_20260812143005_a1b2c3') {
            throw new Error(`analysis did not use backend room_id: ${JSON.stringify(analyzeRequest.body)}`);
        }

        if ('notification_email' in analyzeRequest.body) {
            throw new Error(`analysis request must not include notification_email: ${JSON.stringify(analyzeRequest.body)}`);
        }

        if (errors.length > 0) {
            throw new Error(`frontend errors: ${JSON.stringify(errors)}`);
        }
        """
    )

    result = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


# Phase 08에서 프론트가 mailto 대신 백엔드 이메일 발송 상태를 표시하는지 확인한다.
def test_phase_08_frontend_displays_backend_email_delivery_without_mailto() -> None:
    script = textwrap.dedent(
        """
        import { readFileSync } from 'node:fs';
        import vm from 'node:vm';

        const code = readFileSync('front/app.js', 'utf8');

        class FakeClassList {
            add() {}
            remove() {}
            toggle() { return false; }
        }

        class FakeElement {
            constructor(id = '') {
                this.id = id;
                this.value = '';
                this.textContent = '';
                this.innerHTML = '';
                this.className = '';
                this.disabled = false;
                this.dataset = {};
                this.children = [];
                this.listeners = {};
                this.classList = new FakeClassList();
            }

            addEventListener(type, listener) {
                if (!this.listeners[type]) {
                    this.listeners[type] = [];
                }
                this.listeners[type].push(listener);
            }

            appendChild(child) {
                this.children.push(child);
                return child;
            }

            focus() {}
            querySelector() { return null; }
            querySelectorAll() { return []; }

            async trigger(type, event = {}) {
                for (const listener of this.listeners[type] || []) {
                    await listener({
                        preventDefault() {},
                        stopPropagation() {},
                        ...event
                    });
                }
            }
        }

        const elements = new Map();
        function getElement(id) {
            if (!elements.has(id)) {
                elements.set(id, new FakeElement(id));
            }
            return elements.get(id);
        }

        const context = {
            console: { error: () => {}, log: () => {} },
            alert: () => {},
            setTimeout,
            clearTimeout,
            encodeURIComponent,
            Date,
            Math,
            String,
            Number,
            Boolean,
            Array,
            Object,
            RegExp,
            JSON,
            CSS: { escape: (value) => String(value) },
            window: { location: { href: '' } },
            document: {
                getElementById: getElement,
                querySelectorAll: () => [],
                createElement: (tagName) => new FakeElement(tagName)
            },
            fetch: async (url, options = {}) => {
                const parsedBody = options.body ? JSON.parse(options.body) : null;

                if (url.endsWith('/api/chat/rooms')) {
                    return {
                        ok: true,
                        status: 200,
                        json: async () => ({
                            room_id: 'room_email_test',
                            room_name: parsedBody.room_name,
                            notification_email: parsedBody.notification_email,
                            created_at: '2026-08-12T14:30:05+09:00'
                        })
                    };
                }

                if (url.endsWith('/api/chat/analyze')) {
                    return {
                        ok: true,
                        status: 200,
                        json: async () => ({
                            analysis_id: 'analysis_email_test',
                            room_id: parsedBody.room_id,
                            room_name: '이메일 발송 테스트 방',
                            notification_email: 'teacher@example.com',
                            messages: parsedBody.messages,
                            bullying_probability: 0.91,
                            risk_level: 'immediate',
                            incident: {
                                manager_summary: '관리자 확인이 필요합니다.',
                                evidence_message_ids: ['msg_001']
                            },
                            risk_segments: [],
                            agent_response: {},
                            notification_delivery: {
                                channel: 'email',
                                status: 'sent',
                                recipient_email: 'teacher@example.com',
                                sent_at: '2026-08-12T14:30:05+09:00',
                                external_message_id: 'smtp-message-001',
                                notion_url: 'https://notion.so/page_001'
                            }
                        })
                    };
                }

                throw new Error(`unexpected fetch url: ${url}`);
            }
        };

        vm.createContext(context);
        vm.runInContext(code, context);

        getElement('new-room-name').value = '이메일 발송 테스트 방';
        getElement('room-notification-email').value = 'teacher@example.com';
        await getElement('create-room-btn').trigger('click');

        getElement('sender').value = 'A';
        getElement('message').value = '너 왜 또 여기 들어왔냐';
        await getElement('add-message-btn').trigger('click');
        await getElement('analyze-btn').trigger('click');

        const notificationText = getElement('notification-status-value').textContent;

        if (context.window.location.href.startsWith('mailto:')) {
            throw new Error(`frontend must not open mailto after backend SMTP delivery: ${context.window.location.href}`);
        }

        if (!notificationText.includes('이메일 알림 전송 완료')) {
            throw new Error(`missing sent email status: ${notificationText}`);
        }

        if (!notificationText.includes('teacher@example.com')) {
            throw new Error(`missing recipient email: ${notificationText}`);
        }

        if (!notificationText.includes('https://notion.so/page_001')) {
            throw new Error(`missing Notion URL: ${notificationText}`);
        }
        """
    )

    result = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


# 프론트 JavaScript가 복사 과정에서 문법 오류 없이 유지되는지 확인한다.
def test_phase_07_frontend_javascript_has_valid_syntax() -> None:
    javascript_path = Path("front/app.js")

    result = subprocess.run(
        ["node", "--check", str(javascript_path)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
