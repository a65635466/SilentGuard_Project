# Phase 02: 백엔드 -> 모델

## 전달 방향

```text
백엔드 -> 모델
```

## 넘겨야 하는 데이터

```json
{
  "messages": [
    {
      "message_id": "msg_001",
      "sender_id": "A",
      "sender_label": "A",
      "text": "너 왜 또 여기 들어왔냐",
      "created_at": "2026-08-08T14:28:00+09:00"
    }
  ]
}
```

## 필드 기준

| 필드 | 타입 | 필수 |
| --- | --- | --- |
| `messages` | array | 예 |
| `messages[].message_id` | string | 예 |
| `messages[].sender_id` | string | 예 |
| `messages[].sender_label` | string | 예 |
| `messages[].text` | string | 예 |
| `messages[].created_at` | ISO-8601 string | 예 |

## 만들지 않는 값

- `risk_level`
- `risk_segments`
- `incident`
- 관리자용 요약

## 2026-08-13 실제 모델 이식 상태

- 한 일: Colab export 결과의 Keras 분류기와 설정 파일을 `ai/model/artifacts/`로 옮겼고, 실제 추론 함수 `ai/model/predict.py`를 추가했다.
- 바꾼 파일: `ai/model/predict.py`, `back/api.py`, `requirements.txt`
- 입력과 출력: 백엔드 `messages` 배열을 `" | "`로 합쳐 로컬 `bge-m3` 임베딩 후 Keras 모델이 `0~1` 확률을 반환하는 구조다.
- 확인한 결과: `python3 -m ai.model.predict`가 `bullying_probability: 0.8737`을 반환했고, `SILENTGUARD_MODEL_PROVIDER=real` 백엔드 API 확인에서 `risk_level: immediate`를 반환했다.
- 결정된 사항: 백엔드 모델 기본값은 실제 로컬 모델이다. mock 모델은 `SILENTGUARD_MODEL_PROVIDER=mock`으로 명시했을 때만 사용한다.
- 한 일: KCDD `train/dev/test`와 별도 서비스 평가셋을 분리 평가하는 `model/evaluation.py`를 추가했고, dev에서 decision threshold를 찾도록 학습 코드를 연결했다.
- 한 일: `model/export_runtime_bundle.py`로 Keras 분류기, 설정, BGE-M3를 원자적으로 하나의 runtime zip으로 export하도록 추가했다. `safetensors`는 재압축하지 않아 대형 파일 export 중 중간 zip이 최종 파일로 남지 않는다.
- 확인한 결과: 평가·export 테스트 5개 통과, 학습 모듈 import 통과. 현재 실제 모델의 KCDD 전체 test 재현은 맥 CPU 임베딩 생성 시간이 길어 아직 완료하지 못했다.
- 확인한 결과: MPS/CUDA를 사용할 수 없는 맥 환경에서 KCDD test 2,225건의 BGE-M3 재임베딩은 장시간 실행되어 중단했다. 코랩에서 test 임베딩을 함께 export하고 `model.evaluate_runtime --test-embeddings`로 분류기 재현을 확인할 수 있게 했다.
- 확인한 결과: 전체 대화 하나만 임베딩하면 즉시개입 샘플이 `0.3227`이지만, 1·2메시지 창의 최대 확률을 사용하면 `0.9447`이 된다. 창 기반 추론 후 sanity check는 normal `0.3141`, caution `0.6982`, warning `0.0921`, immediate `0.9447`로 warning 오분류가 남아 있다.
- 확인한 결과: 실제 `SILENTGUARD_MODEL_PROVIDER=real` FastAPI 요청에서도 normal `0.3141/normal`, warning `0.0921/normal`, immediate `0.9447/immediate`가 동일하게 재현됐다. 모델 API와 위험 단계 변환은 정상이며 warning 표현의 모델 일반화가 남은 문제다.
- 한 일: 코랩 반복 실험에 1·2발화 window 증강 학습 후보를 추가했다. window 후보는 dev/test도 원본 대화별 최대 확률로 평가하며, 코랩에서 test 임베딩과 group metadata를 함께 export한다.
- 한 일: 선택된 후보의 `window_augmentation` 설정을 config에 저장하고, service_eval·runtime API·test 재현이 동일한 full/window 입력 방식을 사용하도록 연결했다.
- 결정된 사항: 실제 서비스 추론은 위험 신호 희석을 줄이기 위해 1·2메시지 창별 확률 중 최대값을 사용한다. 이 변경은 학습 데이터에 문장을 추가하지 않으며, KCDD test 재현과 별도 검증이 필요하다.
- 남은 문제: `expected_risk_level`이 근거 있는 별도 서비스 평가 CSV가 아직 없고, KCDD는 정상/위험 이진 라벨이라 네 단계 심각도를 직접 학습하지 않는다. 창 기반 추론과 학습 평가의 분포 차이도 코랩에서 재평가해야 한다.
- 남은 문제: 실제 코랩 후보 실행 결과와 window 증강 후보의 KCDD dev/test 수치가 아직 없다. warning 표현의 실제 성능 개선 여부는 그 결과로 판단해야 한다.
- 확인한 결과: window 후보의 임베딩·라벨·group size shape 검증을 추가했고 전체 자동 테스트 42개, 모델 평가/export 테스트 8개가 통과했다.
- 다음 담당자에게 넘길 내용: 코랩에서 `model/train_model.py`를 실행하면 dev threshold, KCDD test, 선택적 service_eval, `silentguard_runtime_v001.zip`을 생성한다.
