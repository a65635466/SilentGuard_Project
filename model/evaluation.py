"""KCDD 검증과 별도 서비스 평가셋을 같은 기준으로 측정한다."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


RISK_LEVELS = ("normal", "caution", "warning", "immediate")


# 원본 대화를 1·2발화 창으로 확장하고 원본 대화별 창 개수를 반환한다.
def build_window_dataset(data: pd.DataFrame) -> tuple[pd.DataFrame, list[int]]:
    rows = []
    group_sizes = []
    for _, row in data.iterrows():
        turns = [turn.strip() for turn in str(row["conversation_text"]).split("|") if turn.strip()]
        windows = []
        for size in (1, 2):
            if len(turns) <= size:
                windows.append(" | ".join(turns))
            else:
                windows.extend(
                    " | ".join(turns[index : index + size])
                    for index in range(len(turns) - size + 1)
                )
        group_sizes.append(len(windows))
        for window in windows:
            rows.append({"conversation_text": window, "binary_label": int(row["binary_label"])})
    return pd.DataFrame(rows), group_sizes


# 이진 예측 배열에서 외부 평가 라이브러리 없이 기본 지표를 계산한다.
def calculate_binary_metrics(labels: np.ndarray, predictions: np.ndarray) -> dict[str, float]:
    labels = np.asarray(labels, dtype=np.int32)
    predictions = np.asarray(predictions, dtype=np.int32)
    true_positive = int(np.sum((labels == 1) & (predictions == 1)))
    true_negative = int(np.sum((labels == 0) & (predictions == 0)))
    false_positive = int(np.sum((labels == 0) & (predictions == 1)))
    false_negative = int(np.sum((labels == 1) & (predictions == 0)))
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "accuracy": (true_positive + true_negative) / len(labels),
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


# 확률을 SilentGuard의 네 단계 위험도로 변환한다.
def probability_to_risk_level(probability: float) -> str:
    if probability < 0.50:
        return "normal"
    if probability < 0.70:
        return "caution"
    if probability < 0.85:
        return "warning"
    return "immediate"


# 여러 창의 확률을 원본 대화별 최대 위험 확률로 합친다.
def aggregate_grouped_probabilities(
    probabilities: np.ndarray,
    group_sizes: list[int],
) -> np.ndarray:
    values = np.asarray(probabilities, dtype=np.float32).reshape(-1)
    if sum(group_sizes) != len(values) or any(size < 1 for size in group_sizes):
        raise ValueError("group_sizes must partition probabilities")
    result = []
    offset = 0
    for size in group_sizes:
        result.append(float(np.max(values[offset : offset + size])))
        offset += size
    return np.asarray(result, dtype=np.float32)


# 창별로 반복된 정답 라벨을 원본 대화별 한 개 라벨로 합친다.
def aggregate_grouped_labels(labels: np.ndarray, group_sizes: list[int]) -> np.ndarray:
    values = np.asarray(labels, dtype=np.int32).reshape(-1)
    if sum(group_sizes) != len(values) or any(size < 1 for size in group_sizes):
        raise ValueError("group_sizes must partition labels")
    result = []
    offset = 0
    for size in group_sizes:
        group = values[offset : offset + size]
        if not np.all(group == group[0]):
            raise ValueError("all labels in a group must match")
        result.append(int(group[0]))
        offset += size
    return np.asarray(result, dtype=np.int32)


# 검증셋에서 F1이 가장 높은 이진 분류 threshold를 찾는다.
def find_best_binary_threshold(
    labels: np.ndarray,
    probabilities: np.ndarray,
    candidate_thresholds: Iterable[float] | None = None,
) -> tuple[float, dict[str, float]]:
    thresholds = (
        np.arange(0.01, 1.00, 0.01)
        if candidate_thresholds is None
        else np.asarray(list(candidate_thresholds), dtype=np.float32)
    )
    best_threshold = 0.5
    best_result: dict[str, float] | None = None

    for raw_threshold in thresholds:
        threshold = round(float(raw_threshold), 2)
        predictions = (probabilities >= threshold).astype(np.int32)
        result = calculate_binary_metrics(labels, predictions)
        if best_result is None or (result["f1"], result["recall"], -threshold) > (
            best_result["f1"],
            best_result["recall"],
            -best_threshold,
        ):
            best_threshold = float(threshold)
            best_result = result

    assert best_result is not None
    return best_threshold, best_result


# 네 단계 기대값과 모델 확률의 일치율을 계산한다.
def evaluate_service_levels(
    expected_levels: np.ndarray,
    probabilities: np.ndarray,
) -> dict[str, object]:
    predicted_levels = np.array([probability_to_risk_level(value) for value in probabilities])
    matrix = np.zeros((len(RISK_LEVELS), len(RISK_LEVELS)), dtype=np.int32)
    for expected, predicted in zip(expected_levels, predicted_levels):
        matrix[RISK_LEVELS.index(expected), RISK_LEVELS.index(predicted)] += 1
    confusion = {
        expected: {predicted: int(matrix[row, column]) for column, predicted in enumerate(RISK_LEVELS)}
        for row, expected in enumerate(RISK_LEVELS)
    }
    return {
        "accuracy": float(np.mean(expected_levels == predicted_levels)),
        "confusion_matrix": confusion,
        "predicted_levels": predicted_levels.tolist(),
    }


# 서비스 평가 CSV에 필요한 명시적 라벨과 입력 컬럼을 검증한다.
def load_service_eval_csv(path: str | Path) -> pd.DataFrame:
    data = pd.read_csv(path)
    required_columns = {"conversation_text", "binary_label", "expected_risk_level"}
    missing_columns = required_columns - set(data.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"service evaluation CSV missing columns: {missing}")
    if not data["expected_risk_level"].isin(RISK_LEVELS).all():
        raise ValueError("expected_risk_level must be normal, caution, warning, or immediate")
    if not data["binary_label"].isin([0, 1]).all():
        raise ValueError("binary_label must be 0 or 1")
    return data[["conversation_text", "binary_label", "expected_risk_level"]]
