import numpy as np
import pandas as pd
import pytest

from model.evaluation import (
    evaluate_service_levels,
    find_best_binary_threshold,
    aggregate_grouped_probabilities,
    aggregate_grouped_labels,
    build_window_dataset,
    load_service_eval_csv,
)


def test_find_best_binary_threshold_uses_validation_scores() -> None:
    threshold, result = find_best_binary_threshold(
        labels=np.array([0, 0, 1, 1]),
        probabilities=np.array([0.10, 0.40, 0.45, 0.60]),
    )

    assert threshold == pytest.approx(0.41)
    assert result["f1"] == pytest.approx(1.0)
    assert result["recall"] == pytest.approx(1.0)


def test_evaluate_service_levels_reports_expected_four_level_predictions() -> None:
    result = evaluate_service_levels(
        expected_levels=np.array(["normal", "caution", "warning", "immediate"]),
        probabilities=np.array([0.10, 0.60, 0.75, 0.90]),
    )

    assert result["accuracy"] == pytest.approx(1.0)
    assert result["confusion_matrix"] == {
        "normal": {"normal": 1, "caution": 0, "warning": 0, "immediate": 0},
        "caution": {"normal": 0, "caution": 1, "warning": 0, "immediate": 0},
        "warning": {"normal": 0, "caution": 0, "warning": 1, "immediate": 0},
        "immediate": {"normal": 0, "caution": 0, "warning": 0, "immediate": 1},
    }


def test_load_service_eval_csv_requires_explicit_labels(tmp_path) -> None:
    path = tmp_path / "service_eval.csv"
    pd.DataFrame(
        {
            "conversation_text": ["정상 대화"],
            "binary_label": [0],
            "expected_risk_level": ["normal"],
        }
    ).to_csv(path, index=False)

    result = load_service_eval_csv(path)

    assert list(result.columns) == ["conversation_text", "binary_label", "expected_risk_level"]


def test_load_service_eval_csv_rejects_missing_expected_labels(tmp_path) -> None:
    path = tmp_path / "service_eval.csv"
    pd.DataFrame({"conversation_text": ["문장"], "binary_label": [1]}).to_csv(path, index=False)

    with pytest.raises(ValueError, match="expected_risk_level"):
        load_service_eval_csv(path)


def test_aggregate_grouped_probabilities_uses_maximum_per_conversation() -> None:
    result = aggregate_grouped_probabilities(
        probabilities=np.array([0.1, 0.8, 0.2, 0.4, 0.9]),
        group_sizes=[2, 1, 2],
    )

    assert result.tolist() == pytest.approx([0.8, 0.2, 0.9])


def test_aggregate_grouped_labels_keeps_one_label_per_conversation() -> None:
    result = aggregate_grouped_labels(np.array([1, 1, 0, 0, 0]), [2, 1, 2])

    assert result.tolist() == [1, 0, 0]


def test_build_window_dataset_repeats_labels_for_each_window() -> None:
    source = pd.DataFrame(
        {
            "conversation_text": ["a | b | c"],
            "binary_label": [1],
        }
    )

    windows, group_sizes = build_window_dataset(source)

    assert group_sizes == [5]
    assert windows["conversation_text"].tolist() == ["a", "b", "c", "a | b", "b | c"]
    assert windows["binary_label"].tolist() == [1, 1, 1, 1, 1]
