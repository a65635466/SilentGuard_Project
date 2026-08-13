from ai.notification.notion_delivery import build_notion_create_page_body


# Notion 생성 body가 markdown 문자열 대신 native children 블록을 사용하는지 확인한다.
def test_notion_create_page_body_uses_native_children_blocks() -> None:
    body = build_notion_create_page_body(
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
            "manager_summary": "원본 대화에서 배제와 압박의 위험 신호가 보입니다.",
            "context_reason": "특정 사용자를 향한 배제 표현이 반복됩니다.",
            "suspected_risk_types": [
                {"type": "배제성", "evidence_message_ids": ["msg_001", "msg_003"]}
            ],
            "risk_chat_segments": [
                {
                    "start_at": "2026-08-08T14:28:00+09:00",
                    "end_at": "2026-08-08T14:31:00+09:00",
                    "reason": "배제와 압박의 위험 신호가 이어져 추가 확인이 필요합니다.",
                    "evidence_message_ids": ["msg_001", "msg_003"],
                }
            ],
            "evidence_message_ids": ["msg_001", "msg_003"],
            "recommended_initial_actions": ["관련 학생과 개별 면담 일정을 잡습니다."],
            "disclaimer": "자동 분석된 위험 신호이며 최종 판단이 아닙니다.",
        },
        "parent_001",
    )

    assert "markdown" not in body
    assert body["parent"] == {"type": "page_id", "page_id": "parent_001"}
    assert body["properties"]["title"]["title"][0]["text"]["content"] == "REDPLAG\n[위험 신호 알림]"
    assert body["children"]
    assert body["children"][0]["type"] == "heading_1"
    assert body["children"][0]["heading_1"]["rich_text"][0]["text"]["content"] == "REDPLAG"
    assert body["children"][1]["type"] == "heading_2"
    assert body["children"][1]["heading_2"]["rich_text"][0]["text"]["content"] == "[위험 신호 알림]"


# Notion native children이 refined 보고서 섹션과 표/콜아웃 블록을 포함하는지 확인한다.
def test_notion_native_children_include_refined_report_blocks() -> None:
    body = build_notion_create_page_body(
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
            "manager_summary": "원본 대화에서 배제와 압박의 위험 신호가 보입니다.",
            "context_reason": "특정 사용자를 향한 배제 표현이 반복됩니다.",
            "suspected_risk_types": [
                {"type": "배제성", "evidence_message_ids": ["msg_001", "msg_003"]}
            ],
            "risk_chat_segments": [
                {
                    "start_at": "2026-08-08T14:28:00+09:00",
                    "end_at": "2026-08-08T14:31:00+09:00",
                    "reason": "배제와 압박의 위험 신호가 이어져 추가 확인이 필요합니다.",
                    "evidence_message_ids": ["msg_001", "msg_003"],
                }
            ],
            "evidence_message_ids": ["msg_001", "msg_003"],
            "recommended_initial_actions": ["관련 학생과 개별 면담 일정을 잡습니다."],
            "disclaimer": "자동 분석된 위험 신호이며 최종 판단이 아닙니다.",
        },
        "parent_001",
    )

    heading_texts = [
        block[block["type"]]["rich_text"][0]["text"]["content"]
        for block in body["children"]
        if block["type"] == "heading_2"
        and block[block["type"]]["rich_text"][0]["text"]["content"][0].isdigit()
    ]
    assert heading_texts == [
        "1. 탐지 개요",
        "2. 관리자 확인 내용",
        "3. 감지된 위험 유형",
        "4. 위험 구간 로그",
        "5. 주요 근거 메시지",
        "6. 추천 조치",
        "7. 주의 문구",
    ]

    tables = [block for block in body["children"] if block["type"] == "table"]
    assert len(tables) == 3
    assert tables[0]["table"]["table_width"] == 2
    assert tables[1]["table"]["table_width"] == 2
    assert tables[2]["table"]["table_width"] == 4
    assert "children" not in tables[0]
    assert len(tables[0]["table"]["children"]) == 4
    assert len(tables[1]["table"]["children"]) == 2
    assert len(tables[2]["table"]["children"]) == 2

    callout_texts = [
        block["callout"]["rich_text"][0]["text"]["content"]
        for block in body["children"]
        if block["type"] == "callout"
    ]
    assert "관리자 요약: 원본 대화에서 배제와 압박의 위험 신호가 보입니다." in callout_texts
    assert "맥락상 위험 이유: 특정 사용자를 향한 배제 표현이 반복됩니다." in callout_texts
    assert "작성자: A · 시간: 2026-08-08T14:28:00+09:00\n너 왜 또 여기 들어왔냐" in callout_texts
    assert "자동 분석된 위험 신호이며 최종 판단이 아닙니다." in callout_texts

    bullet_texts = [
        block["bulleted_list_item"]["rich_text"][0]["text"]["content"]
        for block in body["children"]
        if block["type"] == "bulleted_list_item"
    ]
    assert bullet_texts == ["관련 학생과 개별 면담 일정을 잡습니다."]
