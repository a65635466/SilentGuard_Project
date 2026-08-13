"""KCDD dev 기준으로 여러 분류기 설정을 비교하고 최종 runtime bundle을 만든다."""

from __future__ import annotations

import json
import random
import shutil
import time
from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

from model import train_model as training
from model.evaluation import (
    aggregate_grouped_probabilities,
    aggregate_grouped_labels,
    build_window_dataset,
    calculate_binary_metrics,
    evaluate_service_levels,
    find_best_binary_threshold,
)
from model.export_runtime_bundle import export_runtime_bundle


EXPERIMENTS = [
    {
        "name": "balanced_256_128_dropout03",
        "use_balanced_train": True,
        "hidden_units": [256, 128],
        "dropout": 0.3,
        "learning_rate": 0.001,
    },
    {
        "name": "balanced_256_128_64_dropout02",
        "use_balanced_train": True,
        "hidden_units": [256, 128, 64],
        "dropout": 0.2,
        "learning_rate": 0.001,
    },
    {
        "name": "full_256_128_dropout03",
        "use_balanced_train": False,
        "hidden_units": [256, 128],
        "dropout": 0.3,
        "learning_rate": 0.001,
    },
    {
        "name": "balanced_256_128_dropout03_lr0003",
        "use_balanced_train": True,
        "hidden_units": [256, 128],
        "dropout": 0.3,
        "learning_rate": 0.0003,
    },
    {
        "name": "balanced_windows_256_128_dropout03",
        "use_balanced_train": True,
        "window_augmentation": True,
        "hidden_units": [256, 128],
        "dropout": 0.3,
        "learning_rate": 0.001,
    },
    {
        "name": "full_windows_256_128_dropout03",
        "use_balanced_train": False,
        "window_augmentation": True,
        "hidden_units": [256, 128],
        "dropout": 0.3,
        "learning_rate": 0.001,
    },
]


# 같은 seed로 후보 모델의 비교 조건을 맞춘다.
def seed_everything() -> None:
    random.seed(training.RANDOM_SEED)
    np.random.seed(training.RANDOM_SEED)
    tf.random.set_seed(training.RANDOM_SEED)


# 후보 설정 하나를 학습하고 dev threshold와 점수를 반환한다.
def train_experiment(
    experiment: dict,
    features: dict[str, np.ndarray],
    labels: dict[str, np.ndarray],
    dev_group_sizes: list[int],
    test_group_sizes: list[int],
) -> dict:
    seed_everything()
    training.HIDDEN_UNITS = experiment["hidden_units"]
    training.DROPOUT = experiment["dropout"]
    training.LEARNING_RATE = experiment["learning_rate"]

    model = training.make_model(features["train"].shape[1])
    candidate_file = training.ARTIFACT_PATH / f"candidate_{experiment['name']}.keras"
    stop = EarlyStopping(
        monitor="val_loss",
        patience=training.EARLY_STOPPING_PATIENCE,
        restore_best_weights=True,
        verbose=0,
    )
    checkpoint = ModelCheckpoint(
        filepath=candidate_file,
        monitor="val_loss",
        save_best_only=True,
        verbose=0,
    )
    started_at = time.time()
    history = model.fit(
        features["train"],
        labels["train"],
        validation_data=(features["dev"], labels["dev"]),
        epochs=training.EPOCHS,
        batch_size=training.BATCH_SIZE,
        callbacks=[stop, checkpoint],
        verbose=training.VERBOSE,
    )
    dev_probabilities = model.predict(features["dev"], verbose=0).reshape(-1)
    dev_probabilities = aggregate_grouped_probabilities(dev_probabilities, dev_group_sizes)
    dev_labels = aggregate_grouped_labels(labels["dev"], dev_group_sizes)
    threshold, dev_metrics = find_best_binary_threshold(dev_labels, dev_probabilities)
    return {
        "name": experiment["name"],
        "config": experiment,
        "candidate_file": str(candidate_file),
        "epochs_run": len(history.history["loss"]),
        "duration_seconds": round(time.time() - started_at, 2),
        "decision_threshold": threshold,
        "dev_result": dev_metrics,
    }


# dev F1, dev recall, 낮은 threshold 순서로 최종 후보를 선택한다.
def choose_best_experiment(results: list[dict]) -> dict:
    return max(
        results,
        key=lambda result: (
            result["dev_result"]["f1"],
            result["dev_result"]["recall"],
            -result["decision_threshold"],
        ),
    )


# 전체 KCDD 파일을 읽고 후보들이 공유할 임베딩을 준비한다.
# 원본 대화별 창 데이터와 원본 대화별 그룹 크기를 준비한다.
def prepare_features() -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], object, object]:
    processed = training.PROCESSED_PATH
    train_balanced = np_load_csv(processed / f"kcdd_train_balanced_{training.VERSION}.csv")
    train_full = np_load_csv(processed / f"kcdd_train_full_{training.VERSION}.csv")
    dev = np_load_csv(processed / f"kcdd_dev_{training.VERSION}.csv")
    test = np_load_csv(processed / f"kcdd_test_{training.VERSION}.csv")
    train_balanced_windows, _ = build_window_dataset(train_balanced)
    train_full_windows, _ = build_window_dataset(train_full)
    dev_windows, dev_group_sizes = build_window_dataset(dev)
    test_windows, test_group_sizes = build_window_dataset(test)
    feature_model = None
    features: dict[str, np.ndarray] = {}
    for name, data in (
        ("train_balanced", train_balanced),
        ("train_full", train_full),
        ("dev", dev),
        ("test", test),
        ("train_balanced_windows", train_balanced_windows),
        ("train_full_windows", train_full_windows),
        ("dev_windows", dev_windows),
        ("test_windows", test_windows),
    ):
        features[name], feature_model = training.make_or_load_features(name, data, feature_model)
    labels = {
        "train_balanced": train_balanced["binary_label"].to_numpy(dtype=np.int32),
        "train_full": train_full["binary_label"].to_numpy(dtype=np.int32),
        "dev": dev["binary_label"].to_numpy(dtype=np.int32),
        "test": test["binary_label"].to_numpy(dtype=np.int32),
        "train_balanced_windows": train_balanced_windows["binary_label"].to_numpy(dtype=np.int32),
        "train_full_windows": train_full_windows["binary_label"].to_numpy(dtype=np.int32),
        "dev_windows": dev_windows["binary_label"].to_numpy(dtype=np.int32),
        "test_windows": test_windows["binary_label"].to_numpy(dtype=np.int32),
    }
    feature_model = training.load_feature_model_if_needed(feature_model)
    return features, labels, feature_model, (dev, test, dev_group_sizes, test_group_sizes)


# 저장된 processed CSV를 읽는다.
def np_load_csv(path: Path):
    import pandas as pd

    return pd.read_csv(path)


# 선택된 후보와 평가 결과를 runtime artifact로 저장한다.
def save_selected_artifacts(best: dict, feature_model: object, service_eval_result: dict | None) -> None:
    source = Path(best["candidate_file"])
    training.ARTIFACT_PATH.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, training.BEST_MODEL_FILE)
    config = {
        "version": training.VERSION,
        "feature_model_name": training.FEATURE_MODEL_NAME,
        "selection_metric": "dev_f1_then_recall",
        "selected_experiment": best["config"],
        "decision_threshold": best["decision_threshold"],
        "dev_result": best["dev_result"],
        "test_result": best["test_result"],
        "service_eval_result": service_eval_result,
    }
    training.CONFIG_FILE.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    if training.EXPORT_EMBEDDER_PATH.exists():
        shutil.rmtree(training.EXPORT_EMBEDDER_PATH)
    feature_model.save(str(training.EXPORT_EMBEDDER_PATH))
    export_runtime_bundle(
        training.BEST_MODEL_FILE,
        training.CONFIG_FILE,
        training.EXPORT_EMBEDDER_PATH,
        training.EXPORT_BUNDLE_FILE,
    )


# 코랩에서 만든 재현용 test 임베딩과 결과를 함께 보존한다.
def save_reproduction_artifacts(
    features: dict[str, np.ndarray],
    best: dict,
    test_feature_name: str,
    test_group_sizes: list[int],
) -> None:
    reproduction_dir = training.ARTIFACT_PATH / f"reproduction_{training.VERSION}"
    reproduction_dir.mkdir(parents=True, exist_ok=True)
    np.save(reproduction_dir / "test_embeddings.npy", features[test_feature_name])
    np.save(reproduction_dir / "test_labels.npy", np.asarray(best["test_labels"], dtype=np.int32))
    np.save(
        reproduction_dir / "test_group_sizes.npy",
        np.asarray(test_group_sizes if best["config"].get("window_augmentation", False) else [1] * len(best["test_labels"]), dtype=np.int32),
    )


# 후보 실험을 실행하고 선택 결과를 출력한다.
def main() -> None:
    seed_everything()
    training.ARTIFACT_PATH.mkdir(parents=True, exist_ok=True)
    needed_csv = training.PROCESSED_PATH / f"kcdd_train_balanced_{training.VERSION}.csv"
    if training.FORCE_REBUILD_DATA or not needed_csv.exists():
        training.build_processed_csv()

    all_features, all_labels, feature_model, datasets = prepare_features()
    _, _, dev_group_sizes, test_group_sizes = datasets
    results = []
    for experiment in EXPERIMENTS:
        train_name = "train_balanced" if experiment["use_balanced_train"] else "train_full"
        if experiment.get("window_augmentation", False):
            train_name = f"{train_name}_windows"
            eval_name = "windows"
            current_dev_group_sizes = dev_group_sizes
            current_test_group_sizes = test_group_sizes
            dev_feature_name = "dev_windows"
            test_feature_name = "test_windows"
            dev_label_name = "dev_windows"
            test_label_name = "test_windows"
        else:
            eval_name = "conversation"
            current_dev_group_sizes = [1] * len(all_labels["dev"])
            current_test_group_sizes = [1] * len(all_labels["test"])
            dev_feature_name = "dev"
            test_feature_name = "test"
            dev_label_name = "dev"
            test_label_name = "test"
        result = train_experiment(
            experiment,
            {"train": all_features[train_name], "dev": all_features[dev_feature_name], "test": all_features[test_feature_name]},
            {"train": all_labels[train_name], "dev": all_labels[dev_label_name], "test": all_labels[test_label_name]},
            current_dev_group_sizes,
            current_test_group_sizes,
        )
        results.append(result)
        print(f"{result['name']}: dev_f1={result['dev_result']['f1']:.4f}")

    best = choose_best_experiment(results)
    selected_model = tf.keras.models.load_model(best["candidate_file"], compile=False)
    selected_windows = best["config"].get("window_augmentation", False)
    test_feature_name = "test_windows" if selected_windows else "test"
    selected_test_groups = test_group_sizes if selected_windows else [1] * len(all_labels["test"])
    test_probabilities = selected_model.predict(all_features[test_feature_name], verbose=0).reshape(-1)
    test_probabilities = aggregate_grouped_probabilities(test_probabilities, selected_test_groups)
    test_predictions = (test_probabilities >= best["decision_threshold"]).astype(np.int32)
    test_labels = (
        aggregate_grouped_labels(all_labels["test_windows"], selected_test_groups)
        if selected_windows
        else all_labels["test"]
    )
    best["test_result"] = calculate_binary_metrics(test_labels, test_predictions)
    best["test_labels"] = test_labels.tolist()
    results_file = training.ARTIFACT_PATH / f"experiment_results_{training.VERSION}.json"
    results_file.write_text(
        json.dumps({"experiments": results, "selected": best["name"]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    service_eval_result = None
    if training.SERVICE_EVAL_FILE:
        service_csv = training.load_service_eval_csv(training.SERVICE_EVAL_FILE)
        service_eval_input = service_csv
        service_group_sizes = [1] * len(service_csv)
        if selected_windows:
            service_eval_input, service_group_sizes = build_window_dataset(service_csv)
        service_features, feature_model = training.make_or_load_features(
            "service_eval_windows" if selected_windows else "service_eval",
            service_eval_input,
            feature_model,
        )
        probabilities = selected_model.predict(service_features, verbose=0).reshape(-1)
        if selected_windows:
            probabilities = aggregate_grouped_probabilities(probabilities, service_group_sizes)
        service_eval_result = evaluate_service_levels(
            service_csv["expected_risk_level"].to_numpy(), probabilities
        )
    save_selected_artifacts(best, feature_model, service_eval_result)
    save_reproduction_artifacts(all_features, best, test_feature_name, test_group_sizes)
    print(f"selected: {best['name']}")
    print(f"runtime bundle: {training.EXPORT_BUNDLE_FILE}")


if __name__ == "__main__":
    main()
