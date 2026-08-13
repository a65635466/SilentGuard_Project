from types import SimpleNamespace

import numpy as np
import pytest

from ai.model.predict import aggregate_window_probabilities, build_message_windows
from ai.model.predict import select_inference_window_sizes


def test_build_message_windows_preserves_order_and_context() -> None:
    messages = [SimpleNamespace(text=text) for text in ["a", "b", "c"]]

    windows = build_message_windows(messages, window_size=2)

    assert windows == ["a | b", "b | c"]


def test_aggregate_window_probabilities_returns_highest_risk_window() -> None:
    probability, index = aggregate_window_probabilities(np.array([0.21, 0.87, 0.42]))

    assert probability == pytest.approx(0.87)
    assert index == 1


def test_select_inference_window_sizes_reads_selected_training_mode(tmp_path) -> None:
    config = tmp_path / "best_model_config_v001.json"
    config.write_text('{"selected_experiment": {"window_augmentation": true}}', encoding="utf-8")

    assert select_inference_window_sizes(tmp_path / "best_model_v001.keras") == (1, 2)
