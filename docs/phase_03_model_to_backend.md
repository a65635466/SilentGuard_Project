# Phase 03: 모델 -> 백엔드

## 전달 방향

```text
모델 -> 백엔드
```

## 넘겨야 하는 데이터

```json
{
  "bullying_probability": 0.91
}
```

## 필드 기준

| 필드 | 타입 | 필수 | 범위 |
| --- | --- | --- | --- |
| `bullying_probability` | number | 예 | 0 이상 1 이하 |

## 만들지 않는 값

- `risk_level`
- `risk_segments`
- `incident`
- `manager_summary`
- `notification_delivery`

