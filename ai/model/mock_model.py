"""문서에 정의된 데모 대화에 대한 결정론적 mock 모델 출력."""

from __future__ import annotations

from typing import Protocol


class MessageLike(Protocol):
    """Mock 점수 계산에 필요한 메시지 필드를 정의한다."""

    text: str


DEMO_SCORES = {
    (
        "오늘 체육복 챙겼어?",
        "응 챙겼어.",
        "끝나고 같이 매점 갈래?",
    ): 0.24,
    (
        "너 오늘 왜 답이 이렇게 늦어?",
        "학원 다녀오느라 조금 늦었어.",
        "다음에는 바로 답해. 다들 기다리잖아.",
    ): 0.58,
    (
        "또 실수했네. 너 때문에 분위기 다 망쳤어.",
        "미안, 다음에는 조심할게.",
        "항상 저래. 그냥 빼고 하자.",
    ): 0.75,
    (
        "너 왜 또 여기 들어왔냐",
        "그냥 얘기하려고",
        "아무도 너랑 말하기 싫대",
        "맞아 그냥 나가",
    ): 0.91,
}


# 원본 메시지 묶음에 대응하는 mock 괴롭힘 확률을 반환한다.
def get_mock_bullying_probability(messages: list[MessageLike]) -> float:
    message_texts = tuple(message.text for message in messages)
    return DEMO_SCORES.get(message_texts, 0.42)
