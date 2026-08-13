"""저장된 실제 runtime artifact로 KCDD test 성능을 재현한다."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ai.model.predict import load_runtime_models
from model.evaluation import aggregate_grouped_probabilities, calculate_binary_metrics


# 명령행 인자를 받아 평가에 필요한 파일 경로를 만든다.
# 저장된 설정 파일에서 판정 기준값을 읽고 없으면 기본값을 반환한다.
def load_decision_threshold(config_file: Path, default_threshold: float) -> float:
    if not config_file.exists():
        return default_threshold
    config = json.loads(config_file.read_text(encoding="utf-8"))
    return float(config.get("decision_threshold", default_threshold))


# 명령행 인자를 받아 평가에 필요한 파일 경로를 만든다.
def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--test-csv",
        type=Path,
        default=Path("model/datasets/kcdd/processed/kcdd_test_v001.csv"),
    )
    parser.add_argument(
        "--model-file",
        type=Path,
        default=Path("ai/model/artifacts/best_model_v001.keras"),
    )
    parser.add_argument(
        "--embedder-dir",
        type=Path,
        default=Path("ai/model/embedders/bge-m3"),
    )
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--test-embeddings", type=Path, default=None)
    parser.add_argument("--test-group-sizes", type=Path, default=None)
    return parser.parse_args()


# 저장된 runtime artifact로 KCDD test 확률과 지표를 계산한다.
def evaluate_runtime(
    test_csv: Path,
    model_file: Path,
    embedder_dir: Path,
    threshold: float,
    test_embeddings: Path | None = None,
    test_group_sizes: Path | None = None,
) -> dict[str, object]:
    data = pd.read_csv(test_csv)
    if test_embeddings is not None:
        embeddings = np.load(test_embeddings)
        classifier, _ = load_runtime_models(str(model_file), str(embedder_dir))
    else:
        classifier, embedder = load_runtime_models(str(model_file), str(embedder_dir))
        embeddings = embedder.encode(
            data["conversation_text"].astype(str).tolist(),
            batch_size=128,
            show_progress_bar=True,
            normalize_embeddings=True,
        )
    expected_embedding_rows = (
        int(np.sum(np.load(test_group_sizes))) if test_group_sizes is not None else len(data)
    )
    if len(embeddings) != expected_embedding_rows:
        raise ValueError("test embeddings row count does not match test CSV/group sizes")
    probabilities = classifier.predict(np.asarray(embeddings, dtype=np.float32), verbose=0).reshape(-1)
    if test_group_sizes is not None:
        probabilities = aggregate_grouped_probabilities(
            probabilities,
            np.load(test_group_sizes).astype(np.int32).tolist(),
        )
    labels = data["binary_label"].to_numpy(dtype=np.int32)
    if len(probabilities) != len(labels):
        raise ValueError("aggregated test probabilities do not match test CSV")
    predictions = (probabilities >= threshold).astype(np.int32)
    result = calculate_binary_metrics(labels, predictions)
    result.update(
        {
            "threshold": threshold,
            "rows": len(data),
            "probability_min": float(probabilities.min()),
            "probability_max": float(probabilities.max()),
        }
    )
    return result


# 저장된 runtime artifact의 평가 결과를 출력한다.
def main() -> None:
    args = parse_arguments()
    result = evaluate_runtime(
        args.test_csv,
        args.model_file,
        args.embedder_dir,
        args.threshold,
        args.test_embeddings,
        args.test_group_sizes,
    )
    print(result)


if __name__ == "__main__":
    main()
