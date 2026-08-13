# SilentGuard 모델 학습

모델 학습은 `model/train_model.py`, 후보 비교와 export는 `model/run_experiments.py`에서 한다.

```text
KCDD 데이터
-> BAAI/bge-m3 특징 추출
-> Keras 분류기
-> bullying_probability
```

실행:

```bash
MPLCONFIGDIR=/Users/mac/Desktop/Team/silentguard/model/.cache/matplotlib \
  /Users/mac/venvs/silentguard-model/bin/python -m model.train_model
```

여러 학습 설정을 자동 비교하려면 아래를 실행한다. 코랩에서는 이 명령 하나만 실행하면 된다.

```bash
cd /content/drive/MyDrive/NVIDIA/Team/silentguard
MPLCONFIGDIR=/content/drive/MyDrive/NVIDIA/Team/silentguard/model/.cache/matplotlib \
  python -m model.run_experiments
```

자동 비교 후보:

```text
balanced/full train
hidden layer 구조
dropout
learning rate
1·2발화 window 증강 학습
```

후보 선택 기준은 `dev F1 -> dev recall -> 낮은 decision threshold` 순서다. KCDD `test`는 후보 선택에 사용하지 않고 선택 후 최종 확인용으로만 기록한다.

export된 모델을 맥에서 다시 검증할 때:

```bash
MPLCONFIGDIR=/Users/mac/Desktop/Team/silentguard/model/.cache/matplotlib \
  /Users/mac/venvs/silentguard-model/bin/python -m model.evaluate_runtime
```

코랩에서 함께 export한 test 임베딩으로는 BGE-M3 재계산 없이 분류기 재현만 확인할 수 있다.

```bash
/Users/mac/venvs/silentguard-model/bin/python -m model.evaluate_runtime \
  --test-embeddings model/artifacts/reproduction_v001/test_embeddings.npy \
  --test-group-sizes model/artifacts/reproduction_v001/test_group_sizes.npy
```

`model/train_model.py` 맨 위 config만 바꿔서 실험한다.

```text
EPOCHS
BATCH_SIZE
LEARNING_RATE
DROPOUT
EARLY_STOPPING_PATIENCE
KFOLD_SPLITS
DEBUG_SAMPLE_SIZE
RUN_SAMPLE_PREDICT
```

터미널에 나오는 것:

```text
데이터 shape
컬럼 설명
라벨 개수
feature shape
model.summary()
epoch별 loss / val_loss
early stopping 결과
accuracy / precision / recall / f1
confusion matrix
예측 예시
```

저장되는 것:

```text
model/datasets/kcdd/processed/*.csv: KCDD 원본 txt를 학습하기 쉬운 표 형태로 바꾼 파일
model/features/*.npy: BAAI/bge-m3가 대화 문장을 숫자 특징으로 바꿔 저장한 파일
model/artifacts/best_model_v001.keras: 학습 중 val_loss가 가장 좋았던 Keras 모델 파일
model/artifacts/best_model_config_v001.json: 학습 설정과 평가 결과를 간단히 기록한 파일
model/artifacts/silentguard_runtime_v001.zip: 맥에서 바로 사용하는 분류기·설정·BGE-M3 묶음
model/artifacts/experiment_results_v001.json: 후보별 dev/test 결과와 선택 결과
model/artifacts/reproduction_v001/test_embeddings.npy: 코랩에서 생성한 KCDD test 임베딩
model/artifacts/reproduction_v001/test_labels.npy: KCDD test 정답 라벨
model/artifacts/reproduction_v001/test_group_sizes.npy: window 임베딩을 원본 대화별로 합치는 정보
```

코랩에서 특징 추출을 끝낸 뒤 아래 파일을 맥북의 같은 위치로 가져오면, 맥북에서는 BAAI 특징 추출을 다시 하지 않고 바로 분류기 학습으로 넘어간다.

```text
model/features/train_balanced_BAAI_bge-m3_v001.npy
model/features/dev_BAAI_bge-m3_v001.npy
model/features/test_BAAI_bge-m3_v001.npy
```

`RUN_SAMPLE_PREDICT = True`로 바꾸면 마지막 예측 예시까지 실행한다. 기본값은 `False`라서 학습/평가만 한다.

코랩에서 export한 test 임베딩으로 맥에서 BGE-M3 재계산 없이 분류기 재현을 확인한다.

```bash
/Users/mac/venvs/silentguard-model/bin/python -m model.evaluate_runtime \
  --test-embeddings model/artifacts/reproduction_v001/test_embeddings.npy \
  --test-group-sizes model/artifacts/reproduction_v001/test_group_sizes.npy
```

실제 서비스 추론은 전체 대화 하나의 임베딩만 사용하지 않고, 1개·2개 메시지 창을 각각 평가한 뒤 가장 높은 확률을 반환한다. 학습 데이터나 라벨을 변경하는 기능이 아니며, KCDD test 재현 결과와 함께 검증해야 한다.

## 별도 서비스 평가셋

KCDD `train/dev/test`에는 없는 실제 서비스 입력 형식을 점검할 때만 별도 CSV를 사용한다. 이 파일은 학습에 섞지 않고 `SERVICE_EVAL_FILE`에 경로를 지정한다.

필수 컬럼:

```text
conversation_text,binary_label,expected_risk_level
```

`expected_risk_level`은 `normal`, `caution`, `warning`, `immediate` 중 하나여야 한다. 라벨 근거가 없는 문장을 임의로 추가하지 않는다. `test` 결과는 이 평가셋으로 대체하지 않는다.

학습이 끝나면 다음을 자동으로 출력하고 저장한다.

```text
dev 최적 decision threshold
dev/test 평가 결과
별도 service_eval 평가 결과 (설정했을 때만)
silentguard_runtime_v001.zip
```
