from ai.notification.notion_markdown import build_notion_page_body, build_notion_page_title


# Notion 페이지 제목이 REDPLAG 브랜드와 알림명을 줄바꿈으로 나누는지 확인한다.
def test_notion_page_title_uses_redplag_brand_with_alert_label() -> None:
    assert build_notion_page_title({"incident_id": "incident_001"}) == "REDPLAG\n[위험 신호 알림]"


# Notion 탐지 개요가 내부 ID 대신 관리자 표시 정보를 보여주는지 확인한다.
def test_notion_detection_overview_shows_manager_facing_summary_without_internal_ids() -> None:
    body = build_notion_page_body(
        {
            "analysis_id": "analysis_001",
            "room_id": "room_001",
            "room_name": "1학년 3반 단체방",
            "bullying_probability": 0.91,
            "risk_level": "immediate",
            "messages": [],
        },
        {
            "incident_id": "incident_001",
            "manager_summary": "관리자 확인이 필요합니다.",
            "context_reason": "배제 위험 신호가 있습니다.",
            "suspected_risk_types": [],
            "risk_chat_segments": [],
            "evidence_message_ids": [],
            "missing_context": [],
            "recommended_initial_actions": [],
            "disclaimer": "자동 분석된 위험 신호이며 최종 판단이 아닙니다.",
        },
    )

    assert "## 1. 탐지 개요" in body
    assert "- 분석 ID:" not in body
    assert "- 사건 ID:" not in body
    assert "- 채팅방 ID:" not in body
    assert "| 채팅방 이름 | 1학년 3반 단체방 |" in body
    assert "| 괴롭힘 위험 확률 | 91% |" in body


# 감지된 위험 유형 표가 메시지 ID 대신 작성자를 보여주는지 확인한다.
def test_notion_risk_types_show_sender_labels_instead_of_message_ids() -> None:
    body = build_notion_page_body(
        {
            "room_name": "1학년 3반 단체방",
            "bullying_probability": 0.91,
            "risk_level": "immediate",
            "messages": [
                {
                    "message_id": "msg_001",
                    "sender_label": "A",
                    "text": "너 왜 또 여기 들어왔냐",
                    "created_at": "2026-08-08T14:28:00+09:00",
                },
                {
                    "message_id": "msg_002",
                    "sender_label": "B",
                    "text": "그냥 나가라",
                    "created_at": "2026-08-08T14:28:20+09:00",
                },
            ],
        },
        {
            "incident_id": "incident_001",
            "manager_summary": "관리자 확인이 필요합니다.",
            "context_reason": "배제 위험 신호가 있습니다.",
            "suspected_risk_types": [
                {"type": "배제성", "evidence_message_ids": ["msg_001", "msg_002"]}
            ],
            "risk_chat_segments": [],
            "evidence_message_ids": [],
            "missing_context": [],
            "recommended_initial_actions": [],
            "disclaimer": "자동 분석된 위험 신호이며 최종 판단이 아닙니다.",
        },
    )

    assert "## 3. 감지된 위험 유형" in body
    assert "| 감지 유형 | 근거 작성자 |" in body
    assert "| 배제성 | A, B |" in body
    assert "| 배제성 | msg_001, msg_002 |" not in body


# Refined Notion 디자인 순서와 핵심 섹션이 Markdown으로 반영되는지 확인한다.
def test_notion_page_body_uses_refined_dossier_design_sections() -> None:
    body = build_notion_page_body(
        {
            "room_name": "1학년 3반 단체방",
            "bullying_probability": 0.91,
            "risk_level": "immediate",
            "messages": [
                {
                    "message_id": "msg_001",
                    "sender_label": "A",
                    "text": "너 왜 또 여기 들어왔냐",
                    "created_at": "2026-08-08T14:28:00+09:00",
                },
                {
                    "message_id": "msg_003",
                    "sender_label": "A",
                    "text": "아무도 너랑 말하기 싫대",
                    "created_at": "2026-08-08T14:30:00+09:00",
                },
            ],
        },
        {
            "incident_id": "incident_001",
            "manager_summary": "원본 대화에서 배제와 압박의 위험 신호가 보입니다.",
            "context_reason": "특정 사용자를 향한 배제 표현이 반복됩니다.",
            "suspected_risk_types": [
                {"type": "배제성", "evidence_message_ids": ["msg_001", "msg_003"]}
            ],
            "risk_chat_segments": [
                {
                    "segment_id": "seg_001",
                    "start_at": "2026-08-08T14:28:00+09:00",
                    "end_at": "2026-08-08T14:31:00+09:00",
                    "reason": "배제와 압박의 위험 신호가 이어져 추가 확인이 필요합니다.",
                    "evidence_message_ids": ["msg_001", "msg_003"],
                }
            ],
            "evidence_message_ids": ["msg_001", "msg_003"],
            "missing_context": ["이전 대화 확인이 필요합니다."],
            "recommended_initial_actions": ["관련 학생과 개별 면담 일정을 잡습니다."],
            "disclaimer": "자동 분석된 위험 신호이며 최종 판단이 아닙니다.",
        },
    )

    expected_order = [
        "## 1. 탐지 개요",
        "## 2. 관리자 확인 내용",
        "## 3. 감지된 위험 유형",
        "## 4. 위험 구간 로그",
        "## 5. 주요 근거 메시지",
        "## 6. 추천 조치",
        "## 7. 주의 문구",
    ]
    assert [body.index(section) for section in expected_order] == sorted(
        body.index(section) for section in expected_order
    )
    assert "> **관리자 요약:** 원본 대화에서 배제와 압박의 위험 신호가 보입니다." in body
    assert "> **맥락상 위험 이유:** 특정 사용자를 향한 배제 표현이 반복됩니다." in body
    assert "| 시간 범위 | 위험 유형 | 탐지 사유 | 근거 메시지 |" in body
    assert "| 2026-08-08T14:28:00+09:00 ~ 2026-08-08T14:31:00+09:00 | 배제성 | 배제와 압박의 위험 신호가 이어져 추가 확인이 필요합니다. | msg_001, msg_003 |" in body
    assert "> **작성자:** A · **시간:** 2026-08-08T14:28:00+09:00" in body
    assert "> 너 왜 또 여기 들어왔냐" in body
    assert "## 7. 추가 확인이 필요한 점" not in body
    assert "## 8. 초기 조치 참고사항" not in body
    assert "- 관련 학생과 개별 면담 일정을 잡습니다." in body
