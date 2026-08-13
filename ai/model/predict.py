"""로컬로 저장된 실제 모델 artifact를 이용한 괴롭힘 위험 확률 추론."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Protocol

import numpy as np


MODEL_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_FILE = MODEL_DIR / "artifacts" / "best_model_v001.keras"
DEFAULT_EMBEDDER_DIR = MODEL_DIR / "embedders" / "bge-m3"
EMBEDDER_WEIGHT_FILES = ("model.safetensors", "pytorch_model.bin")
INFERENCE_WINDOW_SIZES = (1, 2)


class MessageLike(Protocol):
    """실제 모델 점수 계산에 필요한 메시지 필드를 정의한다."""

    text: str


# 메시지 묶음을 학습 때 사용한 대화 문자열 형식으로 바꾼다.
def build_conversation_text(messages: list[MessageLike]) -> str:
    return " | ".join(message.text for message in messages)


# 여러 메시지 대화를 짧은 문맥 창으로 나눠 위험 신호 희석을 줄인다.
def build_message_windows(messages: list[MessageLike], window_size: int) -> list[str]:
    if window_size < 1:
        raise ValueError("window_size must be at least 1")
    texts = [message.text for message in messages]
    if len(texts) <= window_size:
        return [" | ".join(texts)]
    return [" | ".join(texts[index : index + window_size]) for index in range(len(texts) - window_size + 1)]


# 창별 확률 중 가장 높은 위험 신호와 그 위치를 반환한다.
def aggregate_window_probabilities(probabilities):
    values = np.asarray(probabilities, dtype=np.float32).reshape(-1)
    if len(values) == 0:
        raise ValueError("probabilities must not be empty")
    index = int(np.argmax(values))
    return float(values[index]), index


# 선택된 학습 방식에 맞는 runtime 추론 창 크기를 읽는다.
def select_inference_window_sizes(model_file: Path) -> tuple[int, ...]:
    config_file = model_file.with_name(
        model_file.name.replace("best_model_", "best_model_config_").replace(".keras", ".json")
    )
    if not config_file.exists():
        return INFERENCE_WINDOW_SIZES
    try:
        config = json.loads(config_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return INFERENCE_WINDOW_SIZES
    selected = config.get("selected_experiment", {})
    if selected.get("window_augmentation") is True:
        return INFERENCE_WINDOW_SIZES
    return (0,)


# 모델 artifact와 임베더 폴더가 추론 가능한 위치에 있는지 확인한다.
def validate_runtime_files(model_file: Path, embedder_dir: Path) -> None:
    if not model_file.exists():
        raise FileNotFoundError(f"model file not found: {model_file}")
    if not embedder_dir.exists():
        raise FileNotFoundError(f"embedder directory not found: {embedder_dir}")
    if not any((embedder_dir / file_name).exists() for file_name in EMBEDDER_WEIGHT_FILES):
        expected_files = ", ".join(EMBEDDER_WEIGHT_FILES)
        raise FileNotFoundError(
            f"embedder weight file not found in {embedder_dir}; expected one of: {expected_files}"
        )


# TensorFlow와 SentenceTransformer 모델을 한 번만 로딩한다.
@lru_cache(maxsize=1)
def load_runtime_models(model_file: str, embedder_dir: str):
    import tensorflow as tf
    from sentence_transformers import SentenceTransformer

    return (
        load_keras_model_with_dense_compatibility(tf, model_file),
        SentenceTransformer(embedder_dir),
    )


# Colab 저장본의 Dense 설정 중 현재 로컬 Keras가 모르는 키를 제거해 로딩한다.
def load_keras_model_with_dense_compatibility(tf, model_file: str):
    dense_layer = tf.keras.layers.Dense
    original_from_config = dense_layer.from_config

    @classmethod
    def patched_from_config(cls, config):
        cleaned_config = dict(config)
        cleaned_config.pop("quantization_config", None)
        return original_from_config(cleaned_config)

    dense_layer.from_config = patched_from_config
    try:
        return tf.keras.models.load_model(model_file, compile=False)
    finally:
        dense_layer.from_config = original_from_config


# 모델 출력값을 SilentGuard 계약의 0~1 확률로 제한한다.
def clamp_probability(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


# 원본 메시지 묶음에 대한 실제 괴롭힘 위험 확률을 반환한다.
def get_bullying_probability(
    messages: list[MessageLike],
    model_file: Path = DEFAULT_MODEL_FILE,
    embedder_dir: Path = DEFAULT_EMBEDDER_DIR,
) -> float:
    validate_runtime_files(model_file, embedder_dir)

    import numpy as np

    classifier, embedder = load_runtime_models(str(model_file), str(embedder_dir))
    window_sizes = select_inference_window_sizes(model_file)
    window_texts = (
        [build_conversation_text(messages)]
        if window_sizes == (0,)
        else [
            window
            for window_size in window_sizes
            for window in build_message_windows(messages, window_size)
        ]
    )
    x = embedder.encode(window_texts, normalize_embeddings=True)
    probability, _ = aggregate_window_probabilities(
        classifier.predict(np.asarray(x, dtype=np.float32), verbose=0)
    )
    return clamp_probability(probability)


# CLI에서 실제 모델 추론을 빠르게 확인한다.
def main() -> None:
    class SampleMessage:
        def __init__(self, text: str) -> None:
            self.text = text

    messages = [
        SampleMessage("너 왜 또 여기 들어왔냐"),
        SampleMessage("아무도 너랑 같이 하기 싫어해"),
    ]
    probability = get_bullying_probability(messages)
    print(f"bullying_probability: {probability:.4f}")


if __name__ == "__main__":
    main()
