const senderInput = document.getElementById("sender");
const messageInput = document.getElementById("message");
const addMessageButton = document.getElementById("add-message-btn");
const bulkMessageInput = document.getElementById("bulk-message-input");
const bulkAddButton = document.getElementById("bulk-add-btn");
const analyzeButton = document.getElementById("analyze-btn");
const scenarioCards = document.querySelectorAll("[data-scenario]");
const createRoomApiUrl = "http://127.0.0.1:8000/api/chat/rooms";
const analyzeApiUrl = "http://127.0.0.1:8000/api/chat/analyze";

const roomNameInput = document.getElementById("new-room-name");
const createRoomButton = document.getElementById("create-room-btn");
const roomList = document.getElementById("room-list");
const roomCount = document.getElementById("room-count");
const activeRoomName = document.getElementById("active-room-name");
const roomNotificationEmailInput = document.getElementById("room-notification-email");
const addRoomEmailButton = document.getElementById("add-room-email-btn");
const roomEmailList = document.getElementById("room-email-list");
const roomEmailFeedback = document.getElementById("room-email-feedback");

const chatList = document.getElementById("chat-list");
const emptyChat = document.getElementById("empty-chat");
const chatCount = document.getElementById("chat-count");

const chatScreenButton = document.getElementById("chat-screen-btn");
const resultScreenButton = document.getElementById("result-screen-btn");
const backToChatButton = document.getElementById("back-to-chat-btn");

const chatScreen = document.getElementById("chat-screen");
const resultScreen = document.getElementById("result-screen");

const analysisFeedback = document.getElementById("analysis-feedback");

let chatRooms = [];
let activeRoomId = "";
let messages = [];
let nextMessageNumber = 1;
let notificationEmails = [];
let focusClearTimer = null;
let selectedSampleScenario = null;
const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const scenarioSamples = {
    normal: [
        { sender: "A", text: "오늘 체육복 챙겼어?" },
        { sender: "B", text: "응 챙겼어." },
        { sender: "A", text: "끝나고 같이 매점 갈래?" }
    ],
    caution: [
        { sender: "A", text: "너 오늘 왜 답이 이렇게 늦어?" },
        { sender: "B", text: "학원 다녀오느라 조금 늦었어." },
        { sender: "A", text: "다음에는 바로 답해. 다들 기다리잖아." }
    ],
    warning: [
        { sender: "A", text: "또 실수했네. 너 때문에 분위기 다 망쳤어." },
        { sender: "B", text: "미안, 다음에는 조심할게." },
        { sender: "C", text: "항상 저래. 그냥 빼고 하자." }
    ],
    immediate: [
        { sender: "A", text: "너 왜 또 여기 들어왔냐" },
        { sender: "B", text: "그냥 얘기하려고" },
        { sender: "A", text: "아무도 너랑 말하기 싫대" },
        { sender: "C", text: "맞아 그냥 나가" }
    ]
};

function formatOffsetDate(date) {
    const timezoneOffsetMinutes = -date.getTimezoneOffset();
    const sign = timezoneOffsetMinutes >= 0 ? "+" : "-";
    const absoluteOffsetMinutes = Math.abs(timezoneOffsetMinutes);
    const offsetHours = String(Math.floor(absoluteOffsetMinutes / 60)).padStart(2, "0");
    const offsetMinutes = String(absoluteOffsetMinutes % 60).padStart(2, "0");

    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");
    const seconds = String(date.getSeconds()).padStart(2, "0");

    return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}${sign}${offsetHours}:${offsetMinutes}`;
}

function formatDisplayTime(isoString) {
    if (!isoString) {
        return "-";
    }

    const date = new Date(isoString);

    if (Number.isNaN(date.getTime())) {
        return isoString;
    }

    return date.toLocaleString("ko-KR", {
        hour12: false,
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
    });
}

function setActiveScreen(screenName) {
    const isChatScreen = screenName === "chat";

    chatScreen.classList.toggle("is-active", isChatScreen);
    resultScreen.classList.toggle("is-active", !isChatScreen);
    chatScreenButton.classList.toggle("is-active", isChatScreen);
    resultScreenButton.classList.toggle("is-active", !isChatScreen);
}

function setAnalysisFeedback(message, state = "default") {
    analysisFeedback.textContent = message;
    analysisFeedback.className = "status-banner";

    if (state === "loading") {
        analysisFeedback.classList.add("is-loading");
    } else if (state === "success") {
        analysisFeedback.classList.add("is-success");
    } else if (state === "error") {
        analysisFeedback.classList.add("is-error");
    }
}

function syncScenarioCards() {
    scenarioCards.forEach((card) => {
        card.classList.toggle("is-selected", card.dataset.scenario === selectedSampleScenario);
    });
}

function getActiveRoom() {
    return chatRooms.find((room) => room.room_id === activeRoomId) || null;
}

function syncActiveRoomState() {
    const activeRoom = getActiveRoom();

    if (!activeRoom) {
        return;
    }

    activeRoom.messages = messages;
    activeRoom.nextMessageNumber = nextMessageNumber;
}

function activateRoom(roomId) {
    const targetRoom = chatRooms.find((room) => room.room_id === roomId);

    if (!targetRoom) {
        return;
    }

    syncActiveRoomState();
    activeRoomId = targetRoom.room_id;
    messages = targetRoom.messages;
    nextMessageNumber = targetRoom.nextMessageNumber;
    selectedSampleScenario = null;

    renderMessages();
    renderRoomList();
    syncScenarioCards();
    clearAnalysisResult();
    setActiveScreen("chat");
}

function buildCreateRoomRequest(roomName, notificationEmail) {
    return {
        room_name: roomName,
        notification_email: notificationEmail
    };
}

async function requestCreateChatRoom(roomName, notificationEmail) {
    const response = await fetch(createRoomApiUrl, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(buildCreateRoomRequest(roomName, notificationEmail))
    });

    if (!response.ok) {
        throw new Error(`채팅방 생성 서버 오류: ${response.status}`);
    }

    return response.json();
}

function buildChatRoomFromResponse(room) {
    return {
        room_id: room.room_id,
        name: room.room_name,
        notification_email: room.notification_email,
        messages: [],
        nextMessageNumber: 1
    };
}

async function createChatRoom() {
    const roomName = roomNameInput.value.trim();
    const notificationEmail = roomNotificationEmailInput.value.trim();

    if (!roomName) {
        alert("생성할 채팅방 이름을 입력해주세요.");
        roomNameInput.focus();
        return;
    }

    if (!notificationEmail) {
        setEmailInputFeedback("채팅방 생성에 사용할 이메일 주소를 입력해주세요.");
        roomNotificationEmailInput.focus();
        return;
    }

    if (!emailPattern.test(notificationEmail)) {
        setEmailInputFeedback("이메일 형식으로 입력해주세요.");
        roomNotificationEmailInput.focus();
        return;
    }

    createRoomButton.disabled = true;
    createRoomButton.textContent = "생성 중...";

    try {
        const createdRoom = await requestCreateChatRoom(roomName, notificationEmail);
        const newRoom = buildChatRoomFromResponse(createdRoom);

        syncActiveRoomState();
        chatRooms.push(newRoom);
        roomNameInput.value = "";
        roomNotificationEmailInput.value = "";
        notificationEmails = [newRoom.notification_email];
        setEmailInputFeedback("");
        renderNotificationEmails();
        activateRoom(newRoom.room_id);
    } catch (error) {
        console.error("채팅방 생성 API 오류:", error);
        setEmailInputFeedback("채팅방 생성에 실패했습니다. 백엔드 서버를 확인해주세요.");
    } finally {
        createRoomButton.disabled = false;
        createRoomButton.textContent = "생성";
    }
}

function deleteChatRoom(roomId) {
    const roomIndex = chatRooms.findIndex((room) => room.room_id === roomId);

    if (roomIndex < 0) {
        return;
    }

    chatRooms.splice(roomIndex, 1);

    if (activeRoomId === roomId) {
        const fallbackRoom = chatRooms[Math.max(0, roomIndex - 1)] || chatRooms[0] || null;
        activeRoomId = fallbackRoom?.room_id || "";
        messages = fallbackRoom?.messages || [];
        nextMessageNumber = fallbackRoom?.nextMessageNumber || 1;
        selectedSampleScenario = null;
        clearAnalysisResult();
    }

    renderMessages();
    renderRoomList();
    syncScenarioCards();
}

function renderRoomList() {
    roomList.innerHTML = "";
    roomCount.textContent = String(chatRooms.length);

    if (chatRooms.length === 0) {
        const emptyRoom = document.createElement("div");
        emptyRoom.className = "room-list-empty";
        emptyRoom.textContent = "아직 생성된 채팅방이 없습니다.";
        roomList.appendChild(emptyRoom);
        return;
    }

    chatRooms.forEach((room) => {
        const roomButton = document.createElement("button");
        roomButton.type = "button";
        roomButton.className = "room-list-item";
        roomButton.classList.toggle("is-active", room.room_id === activeRoomId);

        const latestMessage = room.messages[room.messages.length - 1];
        const latestText = latestMessage ? latestMessage.text : "메시지가 없습니다.";
        const messageLabel = `${room.messages.length}개`;
        const deleteButtonHtml =
            `<button type="button" class="room-delete-button" aria-label="${escapeHtml(room.name)} 채팅방 삭제">×</button>`;

        roomButton.innerHTML = `
            <div class="room-list-item-header">
                <span class="room-list-item-name">${escapeHtml(room.name)}</span>
                <span class="room-list-item-actions">
                    <span class="room-list-item-count">${escapeHtml(messageLabel)}</span>
                    ${deleteButtonHtml}
                </span>
            </div>
            <div class="room-list-item-meta">
                <span class="room-status-dot"></span>
                <span>${escapeHtml(latestText)}</span>
            </div>
        `;

        roomButton.addEventListener("click", () => {
            activateRoom(room.room_id);
        });

        const deleteButton = roomButton.querySelector(".room-delete-button");

        if (deleteButton) {
            deleteButton.addEventListener("click", (event) => {
                event.stopPropagation();
                deleteChatRoom(room.room_id);
            });
        }

        roomList.appendChild(roomButton);
    });

    const activeRoom = getActiveRoom();
    activeRoomName.textContent = activeRoom ? activeRoom.name : "채팅방을 생성해주세요";
}

function renderNotificationEmails() {
    roomEmailList.innerHTML = "";

    if (notificationEmails.length === 0) {
        const emptyEmail = document.createElement("div");
        emptyEmail.className = "email-address-empty";
        emptyEmail.textContent = "입력된 이메일이 없습니다.";
        roomEmailList.appendChild(emptyEmail);
        return;
    }

    notificationEmails.forEach((email) => {
        const emailItem = document.createElement("div");
        emailItem.className = "email-address-item";

        const emailText = document.createElement("span");
        emailText.className = "email-address-text";
        emailText.textContent = email;

        emailItem.appendChild(emailText);
        roomEmailList.appendChild(emailItem);
    });
}

function addNotificationEmail() {
    const email = roomNotificationEmailInput.value.trim();

    if (!email) {
        setEmailInputFeedback("이메일 주소를 입력해주세요.");
        return;
    }

    if (!emailPattern.test(email)) {
        setEmailInputFeedback("이메일 형식으로 입력해주세요.");
        return;
    }

    if (!notificationEmails.includes(email)) {
        notificationEmails.push(email);
    }

    roomNotificationEmailInput.value = "";
    setEmailInputFeedback("");
    renderNotificationEmails();
}

function setEmailInputFeedback(message) {
    roomEmailFeedback.textContent = message;
    roomNotificationEmailInput.classList.toggle("is-invalid", Boolean(message));
}

function buildMessage(sender, text) {
    const senderValue = sender.trim();

    return {
        message_id: `msg_${String(nextMessageNumber).padStart(3, "0")}`,
        sender_id: senderValue,
        sender_label: senderValue,
        text: text.trim(),
        created_at: formatOffsetDate(new Date())
    };
}

function updateChatCount() {
    chatCount.textContent = `${messages.length}개 메시지`;
    const activeRoom = getActiveRoom();
    activeRoomName.textContent = activeRoom ? activeRoom.name : "채팅방을 생성해주세요";
}

function renderMessages() {
    chatList.innerHTML = "";
    syncActiveRoomState();
    updateChatCount();
    renderRoomList();

    if (messages.length === 0) {
        chatList.appendChild(emptyChat);
        return;
    }

    messages.forEach((item, index) => {
        const messageCard = document.createElement("div");
        messageCard.className = "message-card";
        messageCard.dataset.messageId = item.message_id;

        messageCard.innerHTML = `
            <div class="message-header">
                <strong>${escapeHtml(item.sender_label)}</strong>
                <span>${escapeHtml(item.message_id)}</span>
                <span>${escapeHtml(formatDisplayTime(item.created_at))}</span>
            </div>
            <div class="message-content">
                ${escapeHtml(item.text)}
            </div>
        `;

        chatList.appendChild(messageCard);
    });
}

function addMessage(sender, text) {
    if (!getActiveRoom()) {
        alert("먼저 채팅방을 생성해주세요.");
        roomNameInput.focus();
        return false;
    }

    if (!sender.trim() || !text.trim()) {
        alert("보낸 사람과 메시지를 모두 입력해주세요.");
        return false;
    }

    const newMessage = buildMessage(sender, text);
    messages.push(newMessage);
    nextMessageNumber += 1;
    syncActiveRoomState();

    renderMessages();

    messageInput.value = "";
    messageInput.focus();

    return true;
}

function focusMessageById(messageId) {
    if (!messageId) {
        return;
    }

    const target = chatList.querySelector(`[data-message-id="${CSS.escape(messageId)}"]`);

    if (!target) {
        return;
    }

    setActiveScreen("chat");

    if (focusClearTimer) {
        clearTimeout(focusClearTimer);
    }

    chatList.querySelectorAll(".message-card.is-focused").forEach((card) => {
        card.classList.remove("is-focused");
    });

    target.classList.add("is-focused");
    target.scrollIntoView({
        behavior: "smooth",
        block: "center"
    });

    focusClearTimer = setTimeout(() => {
        target.classList.remove("is-focused");
    }, 2400);
}

function parseBulkMessages(rawText) {
    const lines = rawText
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter((line) => line.length > 0);

    const parsedMessages = [];

    for (const line of lines) {
        const separatorIndex = line.indexOf(":");

        if (separatorIndex <= 0) {
            return {
                ok: false,
                invalidLine: line
            };
        }

        const sender = line.slice(0, separatorIndex).trim();
        const text = line.slice(separatorIndex + 1).trim();

        if (!sender || !text) {
            return {
                ok: false,
                invalidLine: line
            };
        }

        parsedMessages.push({ sender, text });
    }

    return {
        ok: true,
        messages: parsedMessages
    };
}

function addBulkMessages() {
    if (!getActiveRoom()) {
        alert("먼저 채팅방을 생성해주세요.");
        roomNameInput.focus();
        return;
    }

    const rawText = bulkMessageInput.value.trim();

    if (!rawText) {
        alert("일괄 입력할 메시지를 먼저 작성해주세요.");
        return;
    }

    const parsed = parseBulkMessages(rawText);

    if (!parsed.ok) {
        alert(
            "일괄 입력 형식이 올바르지 않습니다.\n\n" +
            "`보낸 사람: 메시지` 형식으로 줄마다 입력해주세요.\n" +
            `문제 줄: ${parsed.invalidLine}`
        );
        return;
    }

    parsed.messages.forEach(({ sender, text }) => {
        const newMessage = buildMessage(sender, text);
        messages.push(newMessage);
        nextMessageNumber += 1;
    });

    syncActiveRoomState();
    renderMessages();
    bulkMessageInput.value = "";
    bulkMessageInput.focus();
}

function loadSample(sampleMessages) {
    if (!getActiveRoom()) {
        alert("먼저 채팅방을 생성해주세요.");
        roomNameInput.focus();
        return;
    }

    messages = [];
    nextMessageNumber = 1;

    sampleMessages.forEach(({ sender, text }) => {
        messages.push(buildMessage(sender, text));
        nextMessageNumber += 1;
    });

    syncActiveRoomState();
    renderMessages();
    clearAnalysisResult();
    setActiveScreen("chat");
}

function buildAnalyzeRequest() {
    syncActiveRoomState();

    return {
        room_id: activeRoomId,
        messages: messages.map((message) => ({
            message_id: message.message_id,
            sender_id: message.sender_id,
            sender_label: message.sender_label,
            text: message.text,
            created_at: message.created_at
        }))
    };
}

function formatDisplayValue(value, fallback = "-") {
    if (value === undefined || value === null || value === "") {
        return fallback;
    }

    if (Array.isArray(value)) {
        return value.length > 0 ? value.join(", ") : fallback;
    }

    return String(value);
}

function getFirstArray(...values) {
    const nonEmptyArray = values.find((value) => Array.isArray(value) && value.length > 0);

    if (nonEmptyArray) {
        return nonEmptyArray;
    }

    return values.find((value) => Array.isArray(value)) || [];
}

function getResponseMessages(result) {
    return getFirstArray(result.messages, messages);
}

function getIncident(result) {
    const agentResponse = result.agent_response || {};
    const topLevelIncident = result.incident || {};
    const nestedIncident = agentResponse.incident || {};

    return Object.keys(topLevelIncident).length > 0 ? topLevelIncident : nestedIncident;
}

function getRiskSegments(result, incident) {
    const agentResponse = result.agent_response || {};

    return getFirstArray(
        result.risk_segments,
        agentResponse.risk_segments,
        incident.risk_chat_segments,
        agentResponse.risk_chat_segments
    );
}

function getUniqueValues(values) {
    return [...new Set(values.filter(Boolean))];
}

function getSegmentTime(segment) {
    const segmentMessages = segment.messages || [];

    return {
        start: segment.start_time || segment.start_at || segmentMessages[0]?.created_at,
        end:
            segment.end_time ||
            segment.end_at ||
            segmentMessages[segmentMessages.length - 1]?.created_at
    };
}

function getSegmentMessages(segment, sourceMessages) {
    if (Array.isArray(segment.messages) && segment.messages.length > 0) {
        return segment.messages;
    }

    if (!Array.isArray(sourceMessages) || sourceMessages.length === 0) {
        return [];
    }

    if (segment.start_message_id && segment.end_message_id) {
        const startIndex = sourceMessages.findIndex((message) => message.message_id === segment.start_message_id);
        const endIndex = sourceMessages.findIndex((message) => message.message_id === segment.end_message_id);

        if (startIndex >= 0 && endIndex >= startIndex) {
            return sourceMessages.slice(startIndex, endIndex + 1);
        }
    }

    const ids = getUniqueValues(segment.message_ids || segment.evidence_message_ids || []);

    if (ids.length === 0) {
        return [];
    }

    return sourceMessages.filter((message) => ids.includes(message.message_id));
}

function getSegmentMessageIds(segment, segmentMessages) {
    return getUniqueValues([
        ...(segment.message_ids || []),
        ...(segment.evidence_message_ids || []),
        segment.start_message_id,
        segment.end_message_id,
        ...segmentMessages.map((message) => message.message_id)
    ]);
}

function formatRiskTypes(value) {
    if (typeof value === "string") {
        return value || "-";
    }

    if (!Array.isArray(value) || value.length === 0) {
        return "-";
    }

    return value
        .map((item) => {
            if (typeof item === "string") {
                return item;
            }

            const type = item.type || item.name || "위험 유형";
            const ids = item.evidence_message_ids || [];

            return ids.length > 0 ? `${type} (${ids.join(", ")})` : type;
        })
        .join(", ");
}

function getRiskThresholdGuide(levelClassName) {
    switch (levelClassName) {
        case "normal":
            return "0.00 이상 0.50 미만이면 정상";
        case "caution":
            return "0.50 이상 0.70 미만이면 주의";
        case "warning":
            return "0.70 이상 0.85 미만이면 경고";
        case "immediate":
            return "0.85 이상 1.00 이하면 즉시 개입";
        default:
            return "위험 단계 기준 정보를 확인할 수 없습니다.";
    }
}

function buildSystemDecisionSummary(result, level, evidenceIds) {
    let probability = Number(result.bullying_probability ?? result.score);

    if (!Number.isFinite(probability)) {
        return "괴롭힘 가능성 값이 없어 시스템 판단 근거를 계산할 수 없습니다.";
    }

    const probabilityRaw = probability <= 1 ? probability : probability / 100;
    const probabilityPercent = Math.round(probabilityRaw * 100);
    const thresholdGuide = getRiskThresholdGuide(level.className);
    const evidenceText =
        evidenceIds && evidenceIds.length > 0
            ? `참고한 근거 메시지 ID: ${evidenceIds.join(", ")}`
            : "근거 메시지 ID는 별도로 전달되지 않았습니다.";

    return [
        `백엔드 응답의 괴롭힘 가능성은 ${probabilityPercent}%(${probabilityRaw.toFixed(2)})입니다.`,
        `백엔드가 반환한 위험 단계는 '${level.text}'입니다. 기준표상 ${thresholdGuide} 구간에 해당하는 단계입니다.`,
        evidenceText
    ].join("\n");
}

function clearAnalysisResult() {
    document.getElementById("analysis-complete-badge").innerHTML = '<span class="flow-dot"></span> 분석 대기';
    document.getElementById("risk-score").textContent = "-";
    document.getElementById("risk-level").textContent = "분석 전";
    document.getElementById("risk-level-card").className = "result-card";
    document.getElementById("risk-level-description").textContent =
        "분석 결과가 표시되면 위험 단계 설명이 나타납니다.";

    document.getElementById("system-decision-summary").textContent = "분석 전";
    document.getElementById("chat-time-range").textContent = "분석 전";
    document.getElementById("risk-type").textContent = "분석 전";
    document.getElementById("risk-reason").textContent = "분석 전";
    document.getElementById("incident-summary").textContent = "분석 전";
    document.getElementById("additional-context").textContent = "분석 전";
    document.getElementById("recommended-actions").textContent = "분석 전";
    document.getElementById("analysis-disclaimer").textContent =
        "※ AI 분석은 위험 신호 탐지를 위한 참고 정보입니다. 최종 판단에는 추가 검토가 필요합니다.";
    document.getElementById("evidence-message-links").innerHTML = "";

    document.getElementById("risk-segment-list").innerHTML = `
        <div class="empty-result">
            아직 분석된 위험 구간이 없습니다.
        </div>
    `;

    document.getElementById("notification-status-value").textContent = "알림 미설정";
    document.getElementById("alert-notification-status").textContent = "알림 미설정";
    setAnalysisFeedback("채팅방 화면에서 메시지를 구성한 뒤 분석을 시작하세요.");
}

function resetAnalysisResult() {
    document.getElementById("analysis-complete-badge").innerHTML = '<span class="flow-dot"></span> 분석 중';
    document.getElementById("risk-score").textContent = "-";
    document.getElementById("risk-level").textContent = "분석 중...";
    document.getElementById("risk-level-card").className = "result-card";
    document.getElementById("risk-level-description").textContent = "분석 결과를 불러오는 중입니다.";

    document.getElementById("system-decision-summary").textContent = "분석 중...";
    document.getElementById("chat-time-range").textContent = "분석 중...";
    document.getElementById("risk-type").textContent = "분석 중...";
    document.getElementById("risk-reason").textContent = "분석 중...";
    document.getElementById("incident-summary").textContent = "분석 중...";
    document.getElementById("additional-context").textContent = "분석 중...";
    document.getElementById("recommended-actions").textContent = "분석 중...";
    document.getElementById("analysis-disclaimer").textContent = "분석 중...";
    document.getElementById("evidence-message-links").innerHTML = "";

    document.getElementById("risk-segment-list").innerHTML = `
        <div class="empty-result">
            분석 결과를 불러오는 중입니다.
        </div>
    `;

    document.getElementById("notification-status-value").textContent = "분석 중...";
    document.getElementById("alert-notification-status").textContent = "분석 중...";
    setAnalysisFeedback("분석 요청을 보냈습니다. 결과를 기다리는 중입니다.", "loading");
}

function getRiskLevel(result) {
    const levelValue = result.risk_level ?? result.level;

    switch (levelValue) {
        case "normal":
            return {
                text: "정상",
                className: "normal",
                description: "현재 대화에서 뚜렷한 괴롭힘 위험 신호가 확인되지 않았습니다."
            };
        case "caution":
            return {
                text: "주의",
                className: "caution",
                description: "일부 주의가 필요한 표현이나 관계적 위험 신호가 확인되었습니다."
            };
        case "warning":
            return {
                text: "경고",
                className: "warning",
                description: "괴롭힘으로 이어질 가능성이 있는 위험 신호가 확인되었습니다."
            };
        case "immediate":
            return {
                text: "즉시 개입",
                className: "immediate",
                description: "강한 괴롭힘 위험 신호가 확인되어 추가적인 즉시 검토가 필요합니다."
            };
        default:
            return {
                text: "응답 없음",
                className: "unknown",
                description: "백엔드 응답에 위험 단계가 포함되지 않았습니다."
            };
    }
}

function extractChatTimeRange(riskSegments, sourceMessages = messages) {
    if (riskSegments.length > 0) {
        const firstSegment = riskSegments[0];
        const lastSegment = riskSegments[riskSegments.length - 1];

        const firstTime = getSegmentTime(firstSegment);
        const lastTime = getSegmentTime(lastSegment);
        const start = firstTime.start;
        const end = lastTime.end;

        if (start || end) {
            return `${formatDisplayTime(start)} ~ ${formatDisplayTime(end)}`;
        }
    }

    if (sourceMessages.length > 0) {
        return `${formatDisplayTime(sourceMessages[0].created_at)} ~ ${formatDisplayTime(sourceMessages[sourceMessages.length - 1].created_at)}`;
    }

    return "시간 정보 없음";
}

function displayRiskSegments(segments, fallbackLevelClassName = "unknown", sourceMessages = messages) {
    const container = document.getElementById("risk-segment-list");

    if (!segments || segments.length === 0) {
        container.innerHTML = `
            <div class="empty-result">
                분석된 위험 구간이 없습니다.
            </div>
        `;
        return;
    }

    container.innerHTML = "";

    segments.forEach((segment, index) => {
        const segmentLevel = getRiskLevel({
            level: segment.risk_level ?? segment.level
        });
        const segmentLevelClass =
            segmentLevel.className === "unknown" ? fallbackLevelClassName : segmentLevel.className;

        const card = document.createElement("article");
        card.className = "risk-segment-card";
        card.classList.add(`level-${segmentLevelClass}`);

        const title = document.createElement("h3");
        title.textContent = segment.segment_id
            ? `위험 구간 ${segment.segment_id}`
            : `위험 구간 #${index + 1}`;
        card.appendChild(title);

        const metadata = document.createElement("div");
        metadata.className = "segment-metadata";

        const segmentMessages = getSegmentMessages(segment, sourceMessages);
        const ids = getSegmentMessageIds(segment, segmentMessages);
        const segmentTime = getSegmentTime({
            ...segment,
            messages: segmentMessages
        });
        let riskScore = Number(segment.score ?? segment.risk_score);
        if (riskScore <= 1) {
            riskScore *= 100;
        }

        const timeItem = document.createElement("p");
        timeItem.innerHTML = `<strong>시간</strong><br>${escapeHtml(formatDisplayValue(segmentTime.start))} ~ ${escapeHtml(formatDisplayValue(segmentTime.end))}`;
        metadata.appendChild(timeItem);

        const scoreItem = document.createElement("p");
        scoreItem.innerHTML = `<strong>위험 점수</strong><br>${escapeHtml(Number.isFinite(riskScore) ? `${Math.round(riskScore)}%` : "-")}`;
        metadata.appendChild(scoreItem);

        const reasonItem = document.createElement("p");
        reasonItem.innerHTML = `<strong>판단 이유</strong><br>${escapeHtml(formatDisplayValue(segment.reason))}`;
        metadata.appendChild(reasonItem);

        const messageIdItem = document.createElement("div");
        messageIdItem.innerHTML = `<strong>메시지 ID</strong>`;

        const messageIdLinks = document.createElement("div");
        messageIdLinks.className = "message-id-links";

        if (ids.length === 0) {
            const emptyText = document.createElement("span");
            emptyText.textContent = "-";
            messageIdLinks.appendChild(emptyText);
        } else {
            ids.forEach((messageId) => {
                const button = document.createElement("button");
                button.type = "button";
                button.className = "link-chip";
                button.textContent = messageId;
                button.addEventListener("click", () => {
                    focusMessageById(messageId);
                });
                messageIdLinks.appendChild(button);
            });
        }

        messageIdItem.appendChild(messageIdLinks);
        metadata.appendChild(messageIdItem);

        card.appendChild(metadata);

        const messagesTitle = document.createElement("h4");
        messagesTitle.textContent = "원본 대화";
        card.appendChild(messagesTitle);

        const messagesContainer = document.createElement("div");
        messagesContainer.className = "segment-messages";

        if (segmentMessages.length === 0) {
            const emptyState = document.createElement("div");
            emptyState.className = "empty-result";
            emptyState.textContent = "원본 메시지 정보가 없습니다.";
            messagesContainer.appendChild(emptyState);
        } else {
            segmentMessages.forEach((message) => {
                const messageBox = document.createElement("div");
                messageBox.className = "segment-message";
                messageBox.innerHTML = `
                    <div class="segment-message-header">
                        <strong>${escapeHtml(message.sender_label || message.sender_id || "알 수 없음")}</strong>
                        <span>${escapeHtml(message.message_id || "")}</span>
                        <span>${escapeHtml(formatDisplayTime(message.created_at || ""))}</span>
                    </div>
                    <div class="segment-message-text">
                        ${escapeHtml(message.text || "")}
                    </div>
                `;
                messagesContainer.appendChild(messageBox);
            });
        }

        card.appendChild(messagesContainer);
        container.appendChild(card);
    });
}

function mapNotificationStatus(status) {
    switch (status) {
        case "not_required":
            return "알림 전송 대상 아님";
        case "email_not_configured":
            return "이메일 전송 설정이 아직 연결되지 않음";
        case "sent":
            return "이메일 알림 전송 완료";
        case "email_failed":
            return "이메일 전송 실패";
        case "notion_failed":
            return "Notion 문서 생성 실패로 이메일 미전송";
        case "skipped_invalid_message_id":
            return "근거 메시지 ID 검증 실패로 알림 생략";
        case "분석 중...":
            return status;
        default:
            return formatDisplayValue(status, "알림 미설정");
    }
}

function formatNotificationDelivery(delivery) {
    const status = delivery.status || delivery.delivery_status || "not_required";
    const statusText = mapNotificationStatus(status);
    const details = [];

    if (delivery.channel && delivery.channel !== "none") {
        details.push(`채널: ${delivery.channel}`);
    }

    if (delivery.recipient_email) {
        details.push(`수신: ${delivery.recipient_email}`);
    }

    if (delivery.notion_url) {
        details.push(`Notion: ${delivery.notion_url}`);
    }

    if (delivery.sent_at) {
        details.push(`발송: ${formatDisplayTime(delivery.sent_at)}`);
    }

    return details.length > 0 ? `${statusText}\n${details.join("\n")}` : statusText;
}

function displayAnalysisResult(result) {
    document.getElementById("analysis-complete-badge").innerHTML = '<span class="flow-dot"></span> 분석 완료';
    const riskScore = document.getElementById("risk-score");
    const riskLevel = document.getElementById("risk-level");
    const riskLevelCard = document.getElementById("risk-level-card");
    const riskLevelDescription = document.getElementById("risk-level-description");

    let probability = Number(result.bullying_probability ?? result.score);

    if (Number.isFinite(probability)) {
        if (probability <= 1) {
            probability *= 100;
        }

        riskScore.textContent = `${Math.round(probability)}%`;
    } else {
        riskScore.textContent = "-";
    }

    const level = getRiskLevel(result);
    riskLevel.textContent = level.text;
    riskLevelCard.className = `result-card risk-${level.className}`;
    riskLevelDescription.textContent = level.description;

    const agentResponse = result.agent_response || {};
    const incident = getIncident(result);
    const riskSegments = getRiskSegments(result, incident);
    const responseMessages = getResponseMessages(result);

    const evidenceIds = agentResponse.evidence_message_ids || incident.evidence_message_ids || [];
    const reasonBase = agentResponse.context_reason || incident.context_reason || result.reason;
    const reasonText = formatDisplayValue(reasonBase);

    document.getElementById("system-decision-summary").textContent =
        buildSystemDecisionSummary(result, level, evidenceIds);
    document.getElementById("chat-time-range").textContent = extractChatTimeRange(riskSegments, responseMessages);
    document.getElementById("risk-type").textContent = formatDisplayValue(
        formatRiskTypes(agentResponse.suspected_risk_types || incident.suspected_risk_types || result.risk_type)
    );
    document.getElementById("risk-reason").textContent = reasonText;
    document.getElementById("incident-summary").textContent = formatDisplayValue(
        agentResponse.summary || agentResponse.manager_summary || incident.manager_summary || incident.summary || result.summary
    );
    document.getElementById("additional-context").textContent = formatDisplayValue(
        agentResponse.missing_context || incident.missing_context || result.additional_context
    );
    document.getElementById("recommended-actions").textContent = formatDisplayValue(
        agentResponse.recommended_initial_actions || incident.recommended_initial_actions
    );
    document.getElementById("analysis-disclaimer").textContent = formatDisplayValue(
        agentResponse.disclaimer || incident.disclaimer,
        "※ AI 분석은 위험 신호 탐지를 위한 참고 정보입니다. 최종 판단에는 추가 검토가 필요합니다."
    );
    renderEvidenceLinks(evidenceIds);

    displayRiskSegments(riskSegments, level.className, responseMessages);

    const notificationDelivery = result.notification_delivery || {};
    const notificationText = formatNotificationDelivery({
        ...notificationDelivery,
        status:
            notificationDelivery.status ||
            notificationDelivery.delivery_status ||
            result.notification_status ||
            "not_required"
    });

    document.getElementById("notification-status-value").textContent = notificationText;
    document.getElementById("alert-notification-status").textContent = notificationText;

    setAnalysisFeedback("분석 결과를 불러왔습니다. 위험 구간과 관리자용 사건 알림을 검토하세요.", "success");
}

function renderEvidenceLinks(evidenceIds) {
    const container = document.getElementById("evidence-message-links");
    container.innerHTML = "";

    if (!evidenceIds || evidenceIds.length === 0) {
        return;
    }

    evidenceIds.forEach((messageId) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "link-chip";
        button.textContent = messageId;
        button.addEventListener("click", () => {
            focusMessageById(messageId);
        });
        container.appendChild(button);
    });
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = String(text ?? "");
    return div.innerHTML;
}

addMessageButton.addEventListener("click", () => {
    addMessage(senderInput.value, messageInput.value);
});

bulkAddButton.addEventListener("click", () => {
    addBulkMessages();
});

createRoomButton.addEventListener("click", async () => {
    await createChatRoom();
});

addRoomEmailButton.addEventListener("click", () => {
    addNotificationEmail();
});

roomNameInput.addEventListener("keydown", async (event) => {
    if (event.key === "Enter") {
        event.preventDefault();
        await createChatRoom();
    }
});

roomNotificationEmailInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        event.preventDefault();
        addNotificationEmail();
    }
});

roomNotificationEmailInput.addEventListener("input", () => {
    if (roomEmailFeedback.textContent) {
        setEmailInputFeedback("");
    }
});

messageInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        addMessage(senderInput.value, messageInput.value);
    }
});

scenarioCards.forEach((card) => {
    card.addEventListener("click", () => {
        const scenario = card.dataset.scenario;

        selectedSampleScenario = scenario;
        syncScenarioCards();

        if (scenarioSamples[scenario]) {
            loadSample(scenarioSamples[scenario]);
        }
    });
});

chatScreenButton.addEventListener("click", () => {
    setActiveScreen("chat");
});

resultScreenButton.addEventListener("click", () => {
    setActiveScreen("result");
});

backToChatButton.addEventListener("click", () => {
    setActiveScreen("chat");
});

analyzeButton.addEventListener("click", async () => {
    if (messages.length === 0) {
        alert("분석할 채팅을 먼저 입력해주세요.");
        return;
    }

    setActiveScreen("result");
    resetAnalysisResult();

    analyzeButton.disabled = true;
    analyzeButton.textContent = "분석 중...";

    try {
        const response = await fetch(analyzeApiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(buildAnalyzeRequest())
        });

        if (!response.ok) {
            throw new Error(`서버 오류: ${response.status}`);
        }

        const result = await response.json();
        displayAnalysisResult(result);
    } catch (error) {
        console.error("분석 API 오류:", error);
        clearAnalysisResult();
        setAnalysisFeedback(
            "분석에 실패했습니다. 백엔드 서버가 실행 중인지 확인한 뒤 채팅방 화면에서 다시 시도하세요.",
            "error"
        );
    } finally {
        analyzeButton.disabled = false;
        analyzeButton.textContent = "분석 시작";
    }
});

renderMessages();
renderNotificationEmails();
clearAnalysisResult();
syncScenarioCards();
setActiveScreen("chat");
