# Model & Data Specification

Tài liệu này mô tả các mô hình và dữ liệu chính của MVP sau khi thống nhất Recommendation v1 theo hướng rule-based personalization. Recommender không dùng dataset sản phẩm theo tháng hoặc mô hình xếp hạng cũ; toàn bộ Top 3 được tính từ `user_features`, `product_catalog`, `user_segments`, `cluster_profiles.product_hints_json` và fraud/risk policy.

---

## 1. Model Inventory

| # | Thành phần | Loại | Công nghệ | Có train? | Vai trò |
|---|---|---|---|---|---|
| 1 | XGBoost Fraud Classifier | Supervised classification | XGBoost | Có | Dự đoán `fraud_score` |
| 2 | SHAP Explainer | Explainability | SHAP | Không | Giải thích top features cho fraud |
| 3 | Rule-based Fraud Guardrail | Policy/audit | Custom Python | Không | Tạo alert/override chính sách nếu cần |
| 4 | Customer Segmentation | Unsupervised clustering | StandardScaler + TruncatedSVD + KMeans | Có | Gán cụm khách hàng |
| 5 | Segment Profiler | Aggregate profiling | Rule map + LLM optional | Không | Đặt tên cụm, mô tả, product hints |
| 6 | Rule-Based Product Scorer + Segment Affinity | Deterministic scoring | Custom Python | Không | Tạo Top 3 sản phẩm |
| 7 | Lead Score Calculator | Deterministic scoring | Custom Python | Không | Xếp hạng lead cho telesales |
| 8 | Pitching Agent | Text generation | LLM + templates | Không | Sinh kịch bản tư vấn có guardrails |

Production Fraud dùng XGBoost probability làm `fraud_score`. Rule guardrail chỉ phục vụ audit/chính sách và không trộn vào model score.

---

## 2. Fraud Detection

### 2.1. Input

Fraud model dùng `fraud_features` từ giao dịch:

```text
amount_zscore
tx_count_1h
tx_count_24h
amount_sum_24h
device_changed
ip_changed
location_distance_km
night_transaction_flag
new_merchant_flag
cashout_velocity
circular_transaction_score
```

### 2.2. Output

```json
{
  "user_id": "U123",
  "transaction_id": "T999",
  "fraud_score": 0.12,
  "fraud_status": "pass",
  "shap_explanation": {
    "amount_zscore": 0.18,
    "device_changed": 0.11,
    "tx_count_1h": 0.08
  }
}
```

Threshold policy:

```text
fraud_score < 0.3       -> PASS
0.3 <= fraud_score < 0.7 -> REVIEW
fraud_score >= 0.7       -> BLOCK
```

---

## 3. User Features

`user_features` là feature store dùng chung cho Segmentation, Recommendation và Lead Scoring.

| Nhóm | Feature ví dụ | Dùng cho |
|---|---|---|
| RFM | `recency_days`, `frequency_30d`, `monetary_30d`, `avg_amount_30d` | Recommendation, Lead Score |
| Cashflow | `income_estimate`, `cashflow_net_30d`, `cashflow_stability`, `balance_proxy` | Affordability, Lead Score |
| Category ratios | `travel_ratio`, `shopping_ratio`, `healthcare_ratio`, `online_ratio` | Behavior match |
| Risk/Fraud | `risk_score`, `fraud_score_latest` | Hard filters, eligibility |
| Ownership | `owned_products_json` | Loại sản phẩm đã sở hữu |
| Interaction | `last_recommendation_at`, `last_reject_at`, `contact_count_30d` | Fatigue/cooldown |

Các feature phải được chuẩn hóa cùng schema khi dùng cho Segmentation để tránh lệch giữa train và serving.

---

## 4. Customer Segmentation

Pipeline:

```text
user_features
  -> stable feature selection
  -> StandardScaler
  -> TruncatedSVD
  -> KMeans
  -> user_segments + cluster_profiles
```

Artifacts:

```text
models/segmentation/<model_version>/scaler.pkl
models/segmentation/<model_version>/svd.pkl
models/segmentation/<model_version>/kmeans.pkl
models/segmentation/<model_version>/feature_schema.json
models/segmentation/<model_version>/cluster_profiles.json
```

Metrics:

| Metric | Mục tiêu |
|---|---|
| Min cluster size | >= 5% tổng user hoặc `needs_review=true` |
| Cluster stability | >= 0.80 similarity qua seed/bootstrap |
| Silhouette / DBI / CH | Dùng để chọn PC/K |
| LLM naming confidence | >= 0.75 trung bình |

`cluster_id` không có ý nghĩa cố định qua các lần retrain. Tên và mô tả cụm luôn đọc từ `cluster_profiles` theo đúng `model_version`.

### 4.1. `cluster_profiles.product_hints_json`

Product hints là prior ở cấp cụm, không phải Top 3 cố định.

```json
[
  {
    "product_id": "P002",
    "affinity": 0.86,
    "confidence": 0.78,
    "positive_signals": ["travel_ratio_high", "online_spend_high"],
    "reason": "Cụm này có chi tiêu du lịch và thanh toán online nổi bật"
  }
]
```

LLM chỉ được nhận aggregate profile: size, ratio, top positive/negative z-score features, centroid similarity và product hints. Không gửi raw transaction, PII, card number, IP hoặc device fingerprint.

---

## 5. Rule-Based Recommendation

### 5.1. Inputs

```text
user_features
product_catalog
user_segments
cluster_profiles
fraud_score_latest
recommendation_logs
consultation_log
```

### 5.2. Product Catalog

`product_catalog` là source of truth cho các sản phẩm được phép tiếp thị:

```text
product_id
product_name
product_type
description
risk_allowed
target_behavior
target_signals_json
eligibility_json
campaign_priority
reason_template
is_active
```

Ví dụ `target_signals_json`:

```json
{
  "travel_ratio": 0.40,
  "online_ratio": 0.20,
  "cashflow_stability": 0.20,
  "income_estimate": 0.20
}
```

### 5.3. Hard Filters

```text
fraud_score >= 0.7                   -> không gợi ý sản phẩm nào
0.3 <= fraud_score < 0.7              -> chỉ giữ sản phẩm risk_allowed = low
product.is_active = false             -> loại
user đã sở hữu sản phẩm               -> loại
không đạt eligibility_json            -> loại
đang cooldown sau reject              -> loại hoặc trừ fatigue
```

### 5.4. Scoring Formula

```text
rec_score =
0.40 * behavior_match
+ 0.25 * segment_affinity
+ 0.20 * affordability_fit
+ 0.10 * timing_need
+ 0.05 * campaign_priority
```

Component definitions:

| Component | Nguồn | Default nếu thiếu dữ liệu |
|---|---|---|
| `behavior_match` | Weighted sum từ `target_signals_json` và `user_features` | 0.00 nếu không có target signals |
| `segment_affinity` | `cluster_profiles.product_hints_json.affinity` | 0.35 nếu không có hint |
| `affordability_fit` | Income, cashflow, risk score, eligibility | 0.50 |
| `timing_need` | Tín hiệu 30-90 ngày gần nhất | 0.40 |
| `campaign_priority` | Priority trong `product_catalog` normalize 0-1 | 0.50 |

Ranking:

```text
1. Chạy hard filters.
2. Tính `rec_score` cho từng candidate còn lại.
3. Sort theo score giảm dần.
4. Tie-break bằng `campaign_priority` giảm dần.
5. Tie-break cuối bằng `product_id` tăng dần.
6. Lấy Top 3.
```

### 5.5. Output

```json
{
  "user_id": "U123",
  "segment": {
    "cluster_id": 2,
    "cluster_name": "Travel Affluent"
  },
  "recommendations": [
    {
      "product_id": "P002",
      "product_name": "Bảo hiểm du lịch",
      "score": 0.87,
      "score_breakdown": {
        "behavior_match": 0.36,
        "segment_affinity": 0.22,
        "affordability_fit": 0.17,
        "timing_need": 0.08,
        "campaign_priority": 0.04
      },
      "reasons": [
        "Chi tiêu du lịch cao",
        "Cụm khách hàng có affinity cao với sản phẩm này"
      ]
    }
  ],
  "eligibility_status": "eligible"
}
```

`recommendation_logs` phải lưu `score_breakdown_json`, `reason_json`, `fraud_score`, `risk_score`, `model_version` để audit và debug.

---

## 6. Lead Scoring

Lead Scoring dùng Top 3 đã được Recommendation trả về, sau đó xếp thứ tự khách hàng cho marketer.

```text
lead_score =
0.30 * product_match_score
+ 0.25 * propensity_score
+ 0.20 * recency_score
+ 0.15 * customer_value_score
- 0.10 * fatigue_score
```

| Component | Định nghĩa |
|---|---|
| `product_match_score` | Score cao nhất trong Top 3 |
| `propensity_score` | Mức phù hợp tổng hợp từ behavior, segment affinity và interaction history |
| `recency_score` | Ưu tiên user lâu chưa được liên hệ |
| `customer_value_score` | Monetary, income estimate, độ sâu quan hệ |
| `fatigue_score` | Contact count, recent reject, cooldown |

Lead tier:

| Tier | Điều kiện |
|---|---|
| Hot | `lead_score > 0.85` |
| Warm | `0.60 <= lead_score <= 0.85` |
| Cold | `lead_score < 0.60` |

---

## 7. Data Contracts

### 7.1. Recommendation Candidate

```json
{
  "product_id": "P002",
  "eligible": true,
  "blocked_reason": null,
  "score": 0.87,
  "score_breakdown": {
    "behavior_match": 0.36,
    "segment_affinity": 0.22,
    "affordability_fit": 0.17,
    "timing_need": 0.08,
    "campaign_priority": 0.04
  },
  "reasons": [
    "Chi tiêu du lịch cao",
    "Cụm khách hàng có affinity cao với sản phẩm này"
  ]
}
```

### 7.2. Interaction Event

```json
{
  "user_id": "U123",
  "product_id": "P002",
  "interaction_type": "accepted",
  "metadata": {
    "source": "dashboard",
    "rank": 1
  }
}
```

Interaction events được dùng để cải thiện score ở các phiên bản sau, không làm thay đổi scoring contract của MVP.

---

## 8. Evaluation

Recommendation MVP đo bằng:

| Metric | Mục tiêu |
|---|---|
| Rule Coverage | > 95% khách hàng hợp lệ có ít nhất 1 gợi ý |
| Top 3 Coverage | > 90% khách hàng hợp lệ có đủ 3 gợi ý |
| Explanation Coverage | 100% sản phẩm trả về có reason |
| Fraud Policy Compliance | 100% user blocked/review được xử lý đúng |
| Conversion uplift | Tăng 15% so với random/control trong A/B test |

Lead Queue đo bằng:

| Metric | Mục tiêu |
|---|---|
| Hot lead precision | Đo theo accepted/converted |
| Queue refresh latency | < 500ms cho query queue |
| Contact fatigue violation | 0 case vượt cooldown policy |

---

## 9. Implementation Artifacts

```text
src/recommender/product_catalog.py
src/recommender/rule_based.py
src/recommender/reason_generator.py
src/recommender/service.py
src/lead_scoring/lead_score.py
src/lead_scoring/propensity.py
src/lead_scoring/campaign.py
configs/product_catalog.json
configs/lead_score_weights.json
tests/test_recommender.py
tests/test_lead_score.py
```

---

## 10. Acceptance Tests

- `fraud_score >= 0.7` trả empty recommendations và `eligibility_status = blocked_fraud`.
- `0.3 <= fraud_score < 0.7` chỉ trả sản phẩm `risk_allowed = low`.
- Sản phẩm đã sở hữu không xuất hiện trong Top 3.
- Product hint có affinity cao làm tăng hạng sản phẩm nhưng không vượt hard filter.
- User thiếu segment vẫn có recommendation bằng default `segment_affinity`.
- Mỗi product trả về có `score_breakdown` và ít nhất một `reason`.
- Lead score lấy `product_match_score` từ score cao nhất trong Top 3.
- Không gửi PII/raw transaction sang LLM khi profiling segment hoặc sinh pitch.
