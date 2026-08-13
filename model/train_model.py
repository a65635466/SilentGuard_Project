import json
import random
import time
from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf
from sentence_transformers import SentenceTransformer
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.layers import Dense, Dropout, Input
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam

from model.evaluation import (
    evaluate_service_levels,
    find_best_binary_threshold,
    load_service_eval_csv,
)
from model.export_runtime_bundle import export_runtime_bundle


############################
# 맨 위 config만 바꿔서 실험한다.
############################
VERSION = "v001"
RANDOM_SEED = 42

PATH = Path("model/datasets/kcdd")
RAW_PATH = PATH / "raw"
PROCESSED_PATH = PATH / "processed"
FEATURE_PATH = Path("model/features")
ARTIFACT_PATH = Path("model/artifacts")
BEST_MODEL_FILE = ARTIFACT_PATH / f"best_model_{VERSION}.keras"
CONFIG_FILE = ARTIFACT_PATH / f"best_model_config_{VERSION}.json"
EXPORT_EMBEDDER_PATH = ARTIFACT_PATH / f"bge-m3_{VERSION}"
EXPORT_BUNDLE_FILE = ARTIFACT_PATH / f"silentguard_runtime_{VERSION}.zip"

FEATURE_MODEL_NAME = "BAAI/bge-m3"
USE_BALANCED_TRAIN = True
FORCE_REBUILD_DATA = False
FORCE_REBUILD_FEATURES = False
RUN_SAMPLE_PREDICT = False  # True면 마지막에 예측 예시까지 실행한다.
SERVICE_EVAL_FILE = None  # 별도 라벨 평가셋 CSV 경로. 학습에는 절대 사용하지 않는다.
EXPORT_RUNTIME_BUNDLE = True

DEBUG_SAMPLE_SIZE = 0  # 빠른 확인만 할 때 200처럼 넣는다. 0이면 전체 데이터 사용.
FEATURE_BATCH_SIZE = 16
EPOCHS = 20
BATCH_SIZE = 32
LEARNING_RATE = 0.001
DROPOUT = 0.3
HIDDEN_UNITS = [256, 128]
EARLY_STOPPING_PATIENCE = 4
KFOLD_SPLITS = 0  # 0이면 dev 데이터로만 검증한다. 3 이상이면 kfold도 같이 출력한다.
VERBOSE = 1


LABEL_MAP = {
    "000001": 0,
    "020121": 1,
    "02051": 1,
    "020811": 1,
    "020819": 1,
}

LABEL_DESCR = {
    "000001": "일반 대화",
    "020121": "심각한 협박",
    "02051": "갈취/협박",
    "020811": "직장 내 괴롭힘",
    "020819": "기타 괴롭힘",
}


# KCDD 원본 라벨을 일반=0, 위험=1로 바꾼다.
def label_to_binary(source_label):
    if source_label not in LABEL_MAP:
        raise ValueError(f"알 수 없는 라벨입니다: {source_label}")
    return LABEL_MAP[source_label]


# [SPEAKER] 기준으로 대화를 보기 좋게 나눈다.
def split_speaker_text(raw_text):
    turns = [turn.strip() for turn in raw_text.split("[SPEAKER]")]
    return [turn for turn in turns if turn]


# KCDD txt 파일 하나를 DataFrame으로 읽는다.
def read_kcdd_txt(path):
    rows = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            raw_text, source_label, speaker_roles = line.rstrip("\n").split("\t")
            turns = split_speaker_text(raw_text)
            rows.append(
                {
                    "raw_text": raw_text,
                    "conversation_text": " | ".join(turns),
                    "source_label": source_label,
                    "speaker_roles": speaker_roles,
                    "binary_label": label_to_binary(source_label),
                    "turn_count": len(turns),
                }
            )
    return pd.DataFrame(rows)


# train 데이터에서 정상 개수만큼 위험 데이터를 뽑아 균형을 맞춘다.
def make_balanced_train(train_csv):
    normal = train_csv[train_csv["binary_label"] == 0]
    risk = train_csv[train_csv["binary_label"] == 1]
    sampled_risk = risk.sample(n=len(normal), random_state=RANDOM_SEED)
    balanced = pd.concat([normal, sampled_risk], axis=0)
    return balanced.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)


# raw txt를 읽어서 processed csv를 만든다.
def build_processed_csv():
    PROCESSED_PATH.mkdir(parents=True, exist_ok=True)

    train_full = read_kcdd_txt(RAW_PATH / "train_kf2c.txt")
    train_balanced = make_balanced_train(train_full)
    dev = read_kcdd_txt(RAW_PATH / "dev_kf2c.txt")
    test = read_kcdd_txt(RAW_PATH / "test_kf2c.txt")

    train_full.to_csv(PROCESSED_PATH / f"kcdd_train_full_{VERSION}.csv", index=False)
    train_balanced.to_csv(PROCESSED_PATH / f"kcdd_train_balanced_{VERSION}.csv", index=False)
    dev.to_csv(PROCESSED_PATH / f"kcdd_dev_{VERSION}.csv", index=False)
    test.to_csv(PROCESSED_PATH / f"kcdd_test_{VERSION}.csv", index=False)

    return train_full, train_balanced, dev, test


# 저장된 processed csv를 읽는다.
def load_processed_csv():
    train_name = "balanced" if USE_BALANCED_TRAIN else "full"
    train_csv = pd.read_csv(PROCESSED_PATH / f"kcdd_train_{train_name}_{VERSION}.csv")
    dev_csv = pd.read_csv(PROCESSED_PATH / f"kcdd_dev_{VERSION}.csv")
    test_csv = pd.read_csv(PROCESSED_PATH / f"kcdd_test_{VERSION}.csv")
    return train_csv, dev_csv, test_csv


# 빠른 확인용으로 데이터 일부만 사용한다.
def use_debug_sample(data_csv, name):
    if DEBUG_SAMPLE_SIZE <= 0 or len(data_csv) <= DEBUG_SAMPLE_SIZE:
        return data_csv
    sampled = data_csv.sample(n=DEBUG_SAMPLE_SIZE, random_state=RANDOM_SEED).reset_index(drop=True)
    print(f"{name} debug sample shape: {sampled.shape}")
    return sampled


# 데이터 shape와 라벨 개수를 출력한다.
def print_data_info(name, data_csv):
    print(f"\n[{name}]")
    print(f"shape: {data_csv.shape}")
    print("columns:", list(data_csv.columns))
    print("binary_label 개수:")
    print(data_csv["binary_label"].value_counts().sort_index())
    print("source_label 개수:")
    print(data_csv["source_label"].value_counts().sort_index())


# 특징 파일 경로를 만든다.
def get_feature_file(name):
    safe_model_name = FEATURE_MODEL_NAME.replace("/", "_")
    return FEATURE_PATH / f"{name}_{safe_model_name}_{VERSION}.npy"


# 저장된 특징 파일이 있으면 바로 읽는다.
def load_feature_if_exists(name, data_csv):
    feature_file = get_feature_file(name)

    if feature_file.exists() and not FORCE_REBUILD_FEATURES:
        x = np.load(feature_file)
        if len(x) == len(data_csv):
            print(f"{name} feature load: {x.shape}")
            return x
        print(f"{name} feature 캐시 길이가 달라서 다시 생성합니다: {x.shape} -> {len(data_csv)}개")
    return None


# 필요할 때만 BAAI 특징 추출기를 켠다.
def load_feature_model_if_needed(feature_model):
    if feature_model is None:
        print("\nBAAI 특징 추출기 로딩 중...")
        return SentenceTransformer(FEATURE_MODEL_NAME)
    return feature_model


# BAAI 모델로 대화 문장을 숫자 특징으로 바꾼다.
def make_or_load_features(name, data_csv, feature_model):
    FEATURE_PATH.mkdir(parents=True, exist_ok=True)
    feature_file = get_feature_file(name)

    saved_feature = load_feature_if_exists(name, data_csv)
    if saved_feature is not None:
        return saved_feature, feature_model

    feature_model = load_feature_model_if_needed(feature_model)
    texts = data_csv["conversation_text"].astype(str).tolist()
    x = feature_model.encode(
        texts,
        batch_size=FEATURE_BATCH_SIZE,
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    x = np.asarray(x, dtype=np.float32)
    np.save(feature_file, x)
    print(f"{name} feature save: {x.shape}")
    return x, feature_model


# Keras 이진 분류기 모델을 만든다.
def make_model(input_dim):
    model = Sequential()
    model.add(Input(shape=(input_dim,)))
    for units in HIDDEN_UNITS:
        model.add(Dense(units, activation="relu"))
        model.add(Dropout(DROPOUT))
    model.add(Dense(1, activation="sigmoid"))

    model.compile(
        loss="binary_crossentropy",
        optimizer=Adam(learning_rate=LEARNING_RATE),
        metrics=[
            tf.keras.metrics.BinaryAccuracy(name="accuracy"),
            tf.keras.metrics.Precision(name="precision"),
            tf.keras.metrics.Recall(name="recall"),
        ],
    )
    return model


# 정답과 예측으로 중요한 평가 지표를 출력한다.
def print_eval_result(title, model, x, y, data_csv, threshold=0.5):
    loss, accuracy, precision, recall = model.evaluate(x, y, verbose=0)
    y_prob = model.predict(x, verbose=0).reshape(-1)
    y_pred = (y_prob >= threshold).astype(int)
    f1 = f1_score(y, y_pred, zero_division=0)
    matrix = confusion_matrix(y, y_pred, labels=[0, 1])

    print(f"\n[{title} 평가]")
    print(f"threshold: {threshold:.2f}")
    print(f"loss: {loss:.4f}")
    print(f"accuracy: {accuracy_score(y, y_pred):.4f}")
    print(f"precision: {precision_score(y, y_pred, zero_division=0):.4f}")
    print(f"recall: {recall_score(y, y_pred, zero_division=0):.4f}")
    print(f"f1: {f1:.4f}")
    print("\nconfusion matrix")
    print("실제\\예측     normal(0)  risk(1)")
    print(f"normal(0)     {matrix[0][0]:9d}  {matrix[0][1]:7d}")
    print(f"risk(1)       {matrix[1][0]:9d}  {matrix[1][1]:7d}")

    wrong_index = np.where(y != y_pred)[0][:3]
    if len(wrong_index) > 0:
        print("\n틀린 예측 예시")
        for index in wrong_index:
            text = data_csv.iloc[index]["conversation_text"]
            print(f"- 실제={y[index]}, 예측={y_pred[index]}, 확률={y_prob[index]:.4f}")
            print(f"  {str(text)[:160]}")

    return {
        "loss": float(loss),
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "confusion_matrix": matrix.tolist(),
    }


# kfold를 켜면 train 데이터 안에서 나눠 검증 점수를 출력한다.
def run_kfold_if_needed(x_train, y_train):
    if KFOLD_SPLITS < 3:
        return

    print(f"\n[kfold 실행: {KFOLD_SPLITS} folds]")
    kfold = StratifiedKFold(n_splits=KFOLD_SPLITS, shuffle=True, random_state=RANDOM_SEED)

    for fold, (train_idx, val_idx) in enumerate(kfold.split(x_train, y_train), start=1):
        print(f"\nfold {fold}/{KFOLD_SPLITS}")
        fold_model = make_model(x_train.shape[1])
        fold_stop = EarlyStopping(
            monitor="val_loss",
            patience=EARLY_STOPPING_PATIENCE,
            restore_best_weights=True,
            verbose=1,
        )
        fold_model.fit(
            x_train[train_idx],
            y_train[train_idx],
            validation_data=(x_train[val_idx], y_train[val_idx]),
            epochs=EPOCHS,
            batch_size=BATCH_SIZE,
            callbacks=[fold_stop],
            verbose=VERBOSE,
        )
        y_prob = fold_model.predict(x_train[val_idx], verbose=0).reshape(-1)
        y_pred = (y_prob >= 0.5).astype(int)
        print(f"fold {fold} f1: {f1_score(y_train[val_idx], y_pred, zero_division=0):.4f}")


# 학습 설정을 json으로 저장한다.
def save_config(dev_result, test_result, threshold, service_eval_result=None):
    ARTIFACT_PATH.mkdir(parents=True, exist_ok=True)
    config = {
        "version": VERSION,
        "feature_model_name": FEATURE_MODEL_NAME,
        "use_balanced_train": USE_BALANCED_TRAIN,
        "epochs": EPOCHS,
        "batch_size": BATCH_SIZE,
        "learning_rate": LEARNING_RATE,
        "dropout": DROPOUT,
        "hidden_units": HIDDEN_UNITS,
        "early_stopping_patience": EARLY_STOPPING_PATIENCE,
        "decision_threshold": threshold,
        "dev_result": dev_result,
        "test_result": test_result,
        "service_eval_result": service_eval_result,
    }
    CONFIG_FILE.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nconfig 저장: {CONFIG_FILE}")


# 학습에 사용한 BGE-M3와 분류기를 로컬 추론용 zip으로 export한다.
def save_runtime_bundle(feature_model):
    if not EXPORT_RUNTIME_BUNDLE:
        return None
    feature_model = load_feature_model_if_needed(feature_model)
    if EXPORT_EMBEDDER_PATH.exists():
        import shutil

        shutil.rmtree(EXPORT_EMBEDDER_PATH)
    feature_model.save(str(EXPORT_EMBEDDER_PATH))
    bundle_path = export_runtime_bundle(
        BEST_MODEL_FILE,
        CONFIG_FILE,
        EXPORT_EMBEDDER_PATH,
        EXPORT_BUNDLE_FILE,
    )
    print(f"runtime bundle 저장: {bundle_path}")
    return bundle_path


# 저장된 모델로 메시지 묶음의 괴롭힘 위험 확률을 계산한다.
def get_bullying_probability(messages):
    texts = [message["text"] for message in messages]
    conversation_text = " | ".join(texts)
    feature_model = SentenceTransformer(FEATURE_MODEL_NAME)
    model = tf.keras.models.load_model(BEST_MODEL_FILE)
    x = feature_model.encode([conversation_text], normalize_embeddings=True)
    probability = model.predict(np.asarray(x, dtype=np.float32), verbose=0)[0][0]
    return float(probability)


# 위에서 만든 함수들을 순서대로 실행한다.
def main():
    ############################
    # 1. 데이터 처리
    ############################
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    tf.random.set_seed(RANDOM_SEED)

    print("SilentGuard KCDD 모델 학습")
    print("=" * 50)
    print(f"path: {PATH}")
    print(f"feature model: {FEATURE_MODEL_NAME}")
    print(f"best model: {BEST_MODEL_FILE}")

    needed_csv = PROCESSED_PATH / f"kcdd_train_balanced_{VERSION}.csv"
    if FORCE_REBUILD_DATA or not needed_csv.exists():
        print("\nprocessed csv 생성")
        build_processed_csv()

    train_csv, dev_csv, test_csv = load_processed_csv()

    train_csv = use_debug_sample(train_csv, "train")
    dev_csv = use_debug_sample(dev_csv, "dev")
    test_csv = use_debug_sample(test_csv, "test")

    print("\n[컬럼 설명]")
    print("raw_text: 원본 KCDD 대화")
    print("conversation_text: 모델에 넣을 대화 묶음")
    print("source_label: KCDD 원본 라벨")
    print("speaker_roles: KCDD 원본 화자 정보")
    print("binary_label: 일반=0, 위험=1")
    print("turn_count: 대화 발화 개수")

    print("\n[라벨 설명]")
    for source_label, binary_label in LABEL_MAP.items():
        print(f"{source_label}: {LABEL_DESCR[source_label]} -> {binary_label}")

    print_data_info("train", train_csv)
    print_data_info("dev", dev_csv)
    print_data_info("test", test_csv)

    ############################
    # 1.1 데이터 분리
    ############################
    y_train = train_csv["binary_label"].to_numpy(dtype=np.int32)
    y_dev = dev_csv["binary_label"].to_numpy(dtype=np.int32)
    y_test = test_csv["binary_label"].to_numpy(dtype=np.int32)

    feature_model = None
    train_feature_name = "train_balanced" if USE_BALANCED_TRAIN else "train_full"
    x_train, feature_model = make_or_load_features(train_feature_name, train_csv, feature_model)
    x_dev, feature_model = make_or_load_features("dev", dev_csv, feature_model)
    x_test, feature_model = make_or_load_features("test", test_csv, feature_model)

    print("\nfeature shape")
    print(f"x_train: {x_train.shape}, y_train: {y_train.shape}")
    print(f"x_dev: {x_dev.shape}, y_dev: {y_dev.shape}")
    print(f"x_test: {x_test.shape}, y_test: {y_test.shape}")

    ############################
    # 2. 모델 구성
    ############################
    model = make_model(input_dim=x_train.shape[1])
    print("\n[model summary]")
    model.summary()

    ############################
    # 3. 컴파일, 훈련
    ############################
    run_kfold_if_needed(x_train, y_train)

    ARTIFACT_PATH.mkdir(parents=True, exist_ok=True)
    early_stop = EarlyStopping(
        monitor="val_loss",
        patience=EARLY_STOPPING_PATIENCE,
        restore_best_weights=True,
        verbose=1,
    )
    checkpoint = ModelCheckpoint(
        filepath=BEST_MODEL_FILE,
        monitor="val_loss",
        save_best_only=True,
        verbose=1,
    )

    start = time.time()
    history = model.fit(
        x_train,
        y_train,
        validation_data=(x_dev, y_dev),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=[early_stop, checkpoint],
        verbose=VERBOSE,
    )
    end = time.time()

    best_epoch = int(np.argmin(history.history["val_loss"]) + 1)
    best_val_loss = float(np.min(history.history["val_loss"]))

    print("\n[훈련 결과]")
    print(f"실행 epoch: {len(history.history['loss'])}")
    print(f"best epoch: {best_epoch}")
    print(f"best val_loss: {best_val_loss:.4f}")
    print(f"훈련 시간: {end - start:.2f}초")

    ############################
    # 4. 평가
    ############################
    dev_probabilities = model.predict(x_dev, verbose=0).reshape(-1)
    decision_threshold, threshold_result = find_best_binary_threshold(y_dev, dev_probabilities)
    print(f"\ndev 최적 decision threshold: {decision_threshold:.2f}")
    print(f"dev threshold f1: {threshold_result['f1']:.4f}")
    dev_result = print_eval_result(
        "dev", model, x_dev, y_dev, dev_csv, threshold=decision_threshold
    )
    test_result = print_eval_result(
        "test", model, x_test, y_test, test_csv, threshold=decision_threshold
    )

    service_eval_result = None
    if SERVICE_EVAL_FILE:
        service_eval_csv = load_service_eval_csv(SERVICE_EVAL_FILE)
        service_x, feature_model = make_or_load_features(
            "service_eval", service_eval_csv.rename(columns={"expected_risk_level": "source_label"}), feature_model
        )
        service_probabilities = model.predict(service_x, verbose=0).reshape(-1)
        service_eval_result = evaluate_service_levels(
            service_eval_csv["expected_risk_level"].to_numpy(), service_probabilities
        )
        print("\n[service_eval 평가]")
        print(f"accuracy: {service_eval_result['accuracy']:.4f}")
        print(f"confusion matrix: {service_eval_result['confusion_matrix']}")

    ############################
    # 5. 예측
    ############################
    if RUN_SAMPLE_PREDICT:
        sample_messages = [
            {"text": "너 왜 또 여기 들어왔냐"},
            {"text": "아무도 너랑 같이 하기 싫어해"},
        ]
        sample_probability = get_bullying_probability(sample_messages)

        print("\n[예측 예시]")
        print(f"bullying_probability: {sample_probability:.4f}")

    save_config(dev_result, test_result, decision_threshold, service_eval_result)
    save_runtime_bundle(feature_model)
    print(f"best model 저장: {BEST_MODEL_FILE}")


if __name__ == "__main__":
    main()
