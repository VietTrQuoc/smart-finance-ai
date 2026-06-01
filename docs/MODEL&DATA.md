# Mô hình cần huấn luyện & Dữ liệu cần thu thập

> **Dự án:** AI Transaction Analyzer — Phát hiện Gian lận & Khuyến nghị Sản phẩm Tài chính
> **Ngày tổng hợp:** 01/06/2026

---

## 1. TỔNG QUAN MÔ HÌNH CẦN CHUẨN BỊ

| # | Mô hình | Loại | Thư viện | Cần huấn luyện? | Độ ưu tiên |
|---|---|---|---|---|---|
| 1 | **Rule-based Fraud Filter** (7 luật) | Deterministic | Custom Python | ❌ (cấu hình thủ công) | 🔴 Bắt buộc |
| 2 | **Isolation Forest** | Unsupervised Anomaly Detection | scikit-learn | ✅ Train trên data sạch | 🔴 Bắt buộc |
| 3 | **XGBoost Classifier** | Supervised Classification | XGBoost | ✅ Cần label fraud 0/1 | 🔴 Bắt buộc |
| 4 | **SHAP Explainer** | Explainable AI | SHAP | ❌ (dùng kèm XGBoost) | 🟡 Khuyến nghị |
| 5 | **Rule-based Recommender** | Scoring engine | Custom Python | ❌ (cấu hình rule) | 🔴 Bắt buộc |
| 6 | **Lead Score Calculator** | Weighted formula | Custom Python (NumPy) | ❌ (cấu hình trọng số) | 🔴 Bắt buộc |
| 7 | **Two-Tower PyTorch** | Deep Learning Recommender | PyTorch | ✅ Cần dữ liệu tương tác | 🔵 Out of scope (MVP) |
| 8 | **Deepseek API** | LLM Pitching | deepseek | ❌ (API bên ngoài) | 🔴 Bắt buộc |
| 9 | **Gemini API** | LLM Pitching (fallback) | google-generativeai | ❌ (API bên ngoài) | 🟡 Khuyến nghị |

---

## 2. CHI TIẾT TỪNG MÔ HÌNH

### 2.1. Fraud Detection — Kiến trúc 3 tầng

```
Giao dịch mới
      │
      ▼
┌─────────────────────────────────┐
│ Layer 1: Rule-based Filter      │  < 5ms
│ 7 luật cứng, block ngay nếu     │
│ vi phạm severity = high         │
└──────────────┬──────────────────┘
               ▼
┌─────────────────────────────────┐
│ Layer 2: Isolation Forest       │  < 10ms
│ 200 trees, contamination=0.01   │
│ → anomaly_score (0-1)           │
└──────────────┬──────────────────┘
               ▼
┌─────────────────────────────────┐
│ Layer 3: XGBoost Classifier     │  < 10ms
│ 300 trees, max_depth=6          │
│ + SMOTE oversampling            │
│ → fraud_probability (0-1)       │
└──────────────┬──────────────────┘
               ▼
┌─────────────────────────────────┐
│ Final Decision Engine           │
│ 0.2×Rule + 0.3×IF + 0.5×XGB    │
│ → fraud_score cuối cùng         │
└──────────────┬──────────────────┘
               ▼
    PASS (<0.3) | REVIEW (0.3-0.7) | BLOCK (>0.7)
```

#### 2.1.1. Rule-based Filter — 7 luật

| Rule ID | Tên luật | Loại | Ngưỡng | Severity |
|---|---|---|---|---|
| R01 | Amount Spike | amount | `amount > 5×avg_30d AND amount > 10M` | high |
| R02 | High Velocity | velocity | `tx_count_1h > 10 OR tx_amount_1h > 50M` | high |
| R03 | Device Change Risk | device | `new_device AND amount > 3×avg_30d` | medium |
| R04 | Night Large TX | amount | `is_night AND amount > 20M` | medium |
| R05 | Fast Cash-out | velocity | `time_since_deposit < 10min AND amount > 0.9×deposit` | high |
| R06 | Money Mule Suspect | network | `unique_senders_24h > 10 AND received_24h > 100M` | high |
| R07 | Circular Transaction | circular | `circular_score > 0.8` | high |

> **Rule score:** `high` → 0.9 | `medium` → 0.6 | không trigger → 0.1

#### 2.1.2. Isolation Forest

```python
from sklearn.ensemble import IsolationForest

model = IsolationForest(
    n_estimators=200,
    contamination=0.01,      # tỷ lệ fraud ước tính ~1%
    random_state=42,
    n_jobs=-1
)
# Train trên TOÀN BỘ dữ liệu (không cần label)
# Output: anomaly_score chuẩn hóa về 0-1
```

#### 2.1.3. XGBoost Classifier

```python
import xgboost as xgb
from imblearn.over_sampling import SMOTE

# Cân bằng dữ liệu với SMOTE
smote = SMOTE(random_state=42)
X_resampled, y_resampled = smote.fit_resample(X_train, y_train)

model = xgb.XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    scale_pos_weight=1,      # điều chỉnh nếu imbalance sau SMOTE
    random_state=42,
    eval_metric='aucpr'      # AUPRC quan trọng hơn Accuracy với fraud
)
# Train trên dữ liệu CÓ label fraud 0/1
# Output: fraud_probability (0-1)
```

#### 2.1.4. SHAP Explainer

```python
import shap

explainer = shap.TreeExplainer(xgb_model)
shap_values = explainer.shap_values(fraud_features)
# Output: top features đóng góp (vd: amount_zscore: +0.35, device_change: +0.28)
```

---

### 2.2. Recommendation Engine — Rule-based Scorer (MVP)

Chấm điểm từng sản phẩm trong `product_catalog` dựa trên `user_features`:

| Product ID | Sản phẩm | Công thức tính score |
|---|---|---|
| P001 | Thẻ tín dụng hoàn tiền | `0.4×shopping_ratio + 0.2×frequency_30d_norm + 0.2×monetary_30d_norm + 0.2×(1-risk_score)` |
| P002 | Bảo hiểm du lịch | `0.5×travel_ratio + 0.3×travel_frequency_90d_norm + 0.2×(1-risk_score)` |
| P003 | Vay tiêu dùng | `0.4×neg_cashflow_signal + 0.3×(1-balance_volatility_norm) + 0.3×(1-risk_score)` |
| P004 | Vay thấu chi | `0.5×end_month_negative_flag + 0.3×neg_cashflow_days_norm + 0.2×(1-risk_score)` |
| P005 | Gói tiết kiệm linh hoạt | `0.6×positive_cf_signal + 0.4×(1-risk_score)` |
| P006 | Bảo hiểm sức khỏe | `0.5×healthcare_ratio + 0.3×healthcare_freq_norm + 0.2×(1-risk_score)` |

> **Output:** Top 3 sản phẩm có score cao nhất + `reason` (VD: "Hay mua sắm online", "Thường xuyên đi du lịch")

**Filter bổ sung:**
- `fraud_score ≥ 0.7` → Không gợi ý sản phẩm nào
- `0.3 ≤ fraud_score < 0.7` → Chỉ gợi ý sản phẩm rủi ro thấp (`saving`, `insurance`)

---

### 2.3. Lead Scoring Engine

Công thức:

```
LEAD_SCORE = 0.30 × product_match_score
           + 0.25 × propensity_score
           + 0.20 × recency_boost
           + 0.15 × customer_value_score
           − 0.10 × fatigue_penalty
```

| Thành phần | Trọng số | Cách tính | Input |
|---|---|---|---|
| **Product Match** | 0.30 | `max(top_3_scores)` | `recommendation_logs` |
| **Propensity Score** | 0.25 | Tín hiệu nhu cầu (cashflow âm, tăng chi tiêu, v.v.) | `user_features` |
| **Recency Boost** | 0.20 | `sigmoid(days_since_last_contact / 30)` | `consultation_log` |
| **Customer Value** | 0.15 | `percentile(monetary_90d)` | `user_features` |
| **Fatigue Penalty** | −0.10 | `min(contact_count_30d / 5, 1.0)` | `consultation_log` |

**Lead Tier:**

| Tier | Điều kiện | Hành động |
|---|---|---|
| 🔥 Hot | `> 0.85` | Gọi ngay — ưu tiên cao nhất |
| 🟡 Warm | `0.6 – 0.85` | Gọi trong tuần |
| 🔵 Cold | `< 0.6` | Gọi khi rảnh / chiến dịch đặc biệt |

---

### 2.4. LLM Pitching Bot

| Model | Nhà cung cấp | Dùng cho | Latency mục tiêu |
|---|---|---|---|
| `deepseek-chat` | Deepseek | Sinh kịch bản chính | < 10s |
| `gemini-1.5-flash` | Google | Fallback khi Deepseek lỗi | < 10s |

> **Safety Guardrail:** Không sinh kịch bản nếu `fraud_score > 0.3`. Lọc từ khóa cấm: "thiếu tiền", "AI phát hiện", "gian lận".

---

## 3. DỮ LIỆU CẦN THU THẬP

### 3.1. Dữ liệu giao dịch thô — `transactions`

| # | Trường | Kiểu | Bắt buộc? | Dùng cho |
|---|---|---|---|---|
| 1 | `transaction_id` | TEXT | ✅ | Khóa chính |
| 2 | `user_id` | TEXT | ✅ | Gộp nhóm theo user |
| 3 | `transaction_time` | TIMESTAMP | ✅ | Tính recency, velocity, sequence |
| 4 | `amount` | FLOAT | ✅ | Core feature cho fraud + rec |
| 5 | `transaction_type` | TEXT | ✅ | `transfer`, `payment`, `deposit`, `withdrawal`, `refund` |
| 6 | `merchant_category` | TEXT | ✅ | `shopping`, `travel`, `food`, `healthcare`, `education`, `entertainment` |
| 7 | `merchant_name` | TEXT | Khuyến khích | Phân tích chi tiết merchant |
| 8 | `balance_before` | FLOAT | Khuyến khích | Tính `amount_to_balance_ratio`, phát hiện cash-out |
| 9 | `balance_after` | FLOAT | Khuyến khích | Tính `balance_change`, phát hiện rút cạn tài khoản |
| 10 | `channel` | TEXT | Khuyến khích | `mobile_app`, `web`, `atm`, `pos`, `bank_counter` |
| 11 | `device_id` | TEXT | Khuyến khích | Phát hiện device change, multi-account |
| 12 | `ip_address` | TEXT | Khuyến khích | Phát hiện IP lạ, geo-anomaly |
| 13 | `status` | TEXT | Khuyến khích | `completed`, `pending`, `failed`, `reversed` |

> ⚠️ **Demo tối thiểu:** Chỉ cần 6 trường đầu (`transaction_id` → `merchant_category`) là có thể chạy được MVP.

---

### 3.2. User Features — `user_features` (tổng hợp từ `transactions`)

#### A. RFM Features (10 features)

| # | Feature | Mô tả | Cách tính |
|---|---|---|---|
| 1 | `recency_days` | Số ngày từ giao dịch gần nhất | `today - max(transaction_time)` |
| 2 | `frequency_7d` | Số giao dịch 7 ngày | `COUNT WHERE time >= today-7d` |
| 3 | `frequency_30d` | Số giao dịch 30 ngày | `COUNT WHERE time >= today-30d` |
| 4 | `frequency_90d` | Số giao dịch 90 ngày | `COUNT WHERE time >= today-90d` |
| 5 | `monetary_7d` | Tổng tiền 7 ngày | `SUM(amount) WHERE time >= today-7d` |
| 6 | `monetary_30d` | Tổng tiền 30 ngày | `SUM(amount) WHERE time >= today-30d` |
| 7 | `monetary_90d` | Tổng tiền 90 ngày | `SUM(amount) WHERE time >= today-90d` |
| 8 | `avg_transaction_amount` | Giá trị giao dịch trung bình | `AVG(amount)` |
| 9 | `max_transaction_amount` | Giá trị giao dịch lớn nhất | `MAX(amount)` |
| 10 | `std_transaction_amount` | Độ lệch chuẩn giá trị | `STDDEV(amount)` |

#### B. Category Ratios (9 features — tỷ trọng 0-1)

| # | Feature | Mô tả |
|---|---|---|
| 11 | `shopping_ratio` | Tỷ trọng chi tiêu mua sắm |
| 12 | `travel_ratio` | Tỷ trọng chi tiêu du lịch |
| 13 | `food_ratio` | Tỷ trọng chi tiêu ăn uống |
| 14 | `education_ratio` | Tỷ trọng chi tiêu giáo dục |
| 15 | `healthcare_ratio` | Tỷ trọng chi tiêu y tế |
| 16 | `entertainment_ratio` | Tỷ trọng chi tiêu giải trí |
| 17 | `cashout_ratio` | Tỷ trọng rút tiền mặt |
| 18 | `transfer_ratio` | Tỷ trọng chuyển khoản |
| 19 | `loan_payment_ratio` | Tỷ trọng trả góp/vay |

```python
# Cách tính
category_amount = df.pivot_table(index="user_id", columns="merchant_category",
                                  values="amount", aggfunc="sum", fill_value=0)
category_ratio = category_amount.div(category_amount.sum(axis=1), axis=0)
```

#### C. Cashflow Features (7 features)

| # | Feature | Mô tả |
|---|---|---|
| 20 | `income_total_30d` | Tổng tiền nhận vào 30 ngày |
| 21 | `expense_total_30d` | Tổng tiền chi ra 30 ngày |
| 22 | `net_cashflow_30d` | `income - expense` |
| 23 | `negative_cashflow_days` | Số ngày dòng tiền âm |
| 24 | `end_month_negative_cashflow_flag` | 0/1: 5 ngày cuối tháng âm tiền |
| 25 | `balance_volatility` | Độ biến động số dư |
| 26 | `salary_detected_flag` | 0/1: phát hiện lương (tiền vào đều hàng tháng) |

#### D. Behavior Cycle Features (4 features)

| # | Feature | Mô tả |
|---|---|---|
| 27 | `weekend_spending_ratio` | Tỷ trọng chi tiêu cuối tuần |
| 28 | `night_transaction_ratio` | Tỷ trọng giao dịch ban đêm (22h-6h) |
| 29 | `travel_frequency_90d` | Số giao dịch du lịch 90 ngày |
| 30 | `shopping_frequency_30d` | Số giao dịch mua sắm 30 ngày |

#### E. Risk (1 feature)

| # | Feature | Mô tả |
|---|---|---|
| 31 | `risk_score` | Điểm rủi ro tín dụng (0-1) |

> **Tổng: 31 features cho mỗi user** → Dùng cho Recommendation + Lead Scoring

---

### 3.3. Fraud Features — theo từng giao dịch

Những feature này được tính **real-time tại thời điểm giao dịch mới đến**.

#### A. Core Transaction (5 features)

| # | Feature | Mô tả |
|---|---|---|
| F1 | `amount` | Số tiền giao dịch |
| F2 | `balance_before` | Số dư trước giao dịch |
| F3 | `balance_after` | Số dư sau giao dịch |
| F4 | `balance_change` | `balance_after - balance_before` |
| F5 | `amount_to_balance_ratio` | `amount / balance_before` |

#### B. Velocity Features (8 features)

| # | Feature | Mô tả |
|---|---|---|
| F6 | `tx_count_1h` | Số giao dịch trong 1 giờ qua |
| F7 | `tx_count_6h` | Số giao dịch trong 6 giờ qua |
| F8 | `tx_count_24h` | Số giao dịch trong 24 giờ qua |
| F9 | `tx_amount_sum_1h` | Tổng tiền giao dịch trong 1 giờ |
| F10 | `tx_amount_sum_24h` | Tổng tiền giao dịch trong 24 giờ |
| F11 | `amount_zscore` | Z-score của amount so với trung bình user |
| F12 | `amount_vs_avg_ratio` | `amount / avg_amount_30d` |
| F13 | `frequency_deviation` | Độ lệch tần suất hiện tại vs trung bình |

#### C. Device & Channel (5 features)

| # | Feature | Mô tả |
|---|---|---|
| F14 | `device_change_count_7d` | Số lần đổi thiết bị trong 7 ngày |
| F15 | `ip_change_count_7d` | Số lần đổi IP trong 7 ngày |
| F16 | `new_device_flag` | 0/1: thiết bị chưa từng dùng |
| F17 | `channel_switch_flag` | 0/1: đổi kênh giao dịch bất thường |
| F18 | `multiple_accounts_same_device` | Số tài khoản khác cùng thiết bị |

#### D. Sequence / Time Features (7 features)

| # | Feature | Mô tả |
|---|---|---|
| F19 | `time_since_last_tx` | Giây từ giao dịch trước |
| F20 | `hour_of_day` | Giờ giao dịch (0-23) |
| F21 | `day_of_week` | Thứ trong tuần (0-6) |
| F22 | `is_night_transaction` | 0/1: giao dịch 22h-6h |
| F23 | `is_weekend` | 0/1: giao dịch cuối tuần |
| F24 | `tx_sequence_position` | Vị trí trong chuỗi giao dịch ngày |
| F25 | `avg_time_between_txs` | Khoảng cách trung bình giữa các giao dịch (giây) |

#### E. Graph / Network Features (6 features)

| # | Feature | Mô tả |
|---|---|---|
| F26 | `many_sources_to_one_user` | Số nguồn khác nhau nạp vào 1 ví (24h) |
| F27 | `one_user_to_many_targets` | Số đích khác nhau 1 user chuyển đến (24h) |
| F28 | `circular_transaction_score` | Điểm giao dịch vòng tròn (A→B→C→A) |
| F29 | `shared_device_cluster_size` | Số ví dùng chung thiết bị |
| F30 | `recipient_is_new_flag` | 0/1: người nhận chưa từng giao dịch |
| F31 | `recipient_fraud_history` | 0/1: người nhận có lịch sử fraud |

> **Tổng: 31 fraud features cho mỗi giao dịch** → Input cho Isolation Forest + XGBoost

---

### 3.4. Dữ liệu Label (cần cho Supervised Learning)

| Dữ liệu | Nguồn | Dùng cho |
|---|---|---|
| `isFraud` (0/1) | Dataset PaySim / hệ thống tagging thủ công | Train XGBoost Classifier |
| `fraud_type` | Phân loại của Fraud Analyst | Phân loại 9 loại gian lận |
| `alert_status` (confirmed/false_positive) | Feedback từ Analyst trên dashboard | Cải thiện model theo thời gian |
| `consultation_status` (converted/interested/not_interested) | Marketer đánh dấu sau gọi | Train Lead Scoring (tương lai) |

---

### 3.5. Dữ liệu cấu hình tĩnh

| Bảng | Số bản ghi | Mô tả |
|---|---|---|
| `product_catalog` | 6+ | Danh mục sản phẩm tài chính + `target_behavior` + `risk_allowed` |
| `fraud_rules` | 7 | Luật fraud + ngưỡng + severity |
| `marketing_campaigns` | 3+ | Chiến dịch marketing + filter |

**Dữ liệu mẫu `product_catalog`:**

| product_id | product_name | product_type | target_behavior | risk_allowed |
|---|---|---|---|---|
| P001 | Thẻ tín dụng hoàn tiền | credit_card | shopping_high | medium |
| P002 | Bảo hiểm du lịch | insurance | travel_high | low |
| P003 | Vay tiêu dùng | loan | negative_cashflow | medium |
| P004 | Vay thấu chi | loan | end_month_cash_shortage | medium |
| P005 | Gói tiết kiệm linh hoạt | saving | positive_cashflow | low |
| P006 | Bảo hiểm sức khỏe | insurance | healthcare_high | low |

**Dữ liệu mẫu `fraud_rules`:**

| rule_id | rule_name | rule_type | threshold | severity |
|---|---|---|---|---|
| R01 | Amount Spike | amount | 5.0 | high |
| R02 | High Velocity | velocity | 10 tx/h | high |
| R03 | Device Change Risk | device | 1 | medium |
| R04 | Night Large TX | amount | 20M VND | medium |
| R05 | Fast Cash-out | velocity | 10 min | high |
| R06 | Money Mule Suspect | network | 10 senders | high |
| R07 | Circular Transaction | circular | 0.8 | high |

---

## 4. DATASET ĐỀ XUẤT

| # | Dataset | Dùng cho | Có label? | Link |
|---|---|---|---|---|
| 1 | **PaySim** | Fraud Detection (train Isolation Forest + XGBoost) | ✅ `isFraud`, `isFlaggedFraud` | [Kaggle](https://www.kaggle.com/datasets/ealaxi/paysim1/) |
| 2 | **Transaction Dataset** | Recommendation + Behavior Analysis + Feature Engineering | ✅ `fraud` label + `merchant_category` | [Kaggle](https://www.kaggle.com/datasets/ismetsemedov/transactions/) |

### PaySim — Ưu điểm

- Mô phỏng từ dữ liệu thật của mobile money service
- Đầy đủ `oldbalanceOrg`, `newbalanceOrig`, `oldbalanceDest`, `newbalanceDest`
- Phù hợp tính `balance_change`, `amount_to_balance_ratio`, cash-out detection
- Có sẵn label `isFraud` để train supervised model

### Transaction Dataset — Ưu điểm

- Có `merchant_category`, `city`, `country`, `card_type`
- Phù hợp phân tích hành vi, tỷ trọng chi tiêu theo category
- Hỗ trợ cả fraud detection + recommendation

---

## 5. MA TRẬN FEATURE ⇄ MÔ HÌNH

| Nhóm feature | Rule Filter | Isolation Forest | XGBoost | Recommender | Lead Score |
|---|---|---|---|---|---|
| **Core TX** (amount, balance) | ✅ | ✅ | ✅ | | |
| **Velocity** (tx_count, amount_sum) | ✅ | ✅ | ✅ | | |
| **Device/Channel** | ✅ | ✅ | ✅ | | |
| **Sequence/Time** | ✅ | ✅ | ✅ | | |
| **Graph/Network** | ✅ | | ✅ | | |
| **RFM** (recency, freq, monetary) | | | | ✅ | ✅ |
| **Category Ratios** | | | | ✅ | |
| **Cashflow** (income, expense, net) | | | | ✅ | ✅ |
| **Behavior Cycle** | | | | ✅ | |
| **Risk Score** | | | | ✅ | ✅ |
| **Consultation History** | | | | | ✅ |

---

## 6. THỨ TỰ TRIỂN KHAI DỮ LIỆU

| Tuần | Đầu việc | Output |
|---|---|---|
| **Tuần 1** | Tải PaySim, EDA, làm sạch dữ liệu | `transactions` table sẵn sàng |
| **Tuần 1-2** | Feature Engineering cho Fraud (31 features) | `fraud_features` matrix |
| **Tuần 2** | Train Isolation Forest + XGBoost với SMOTE | `isolation_forest.pkl`, `xgboost_fraud.json` |
| **Tuần 2-3** | Feature Engineering cho User (31 features) | `user_features` table |
| **Tuần 3** | Xây dựng Rule-based Recommender | `product_catalog` + scoring rules |
| **Tuần 3-4** | Xây dựng Lead Score Calculator | `lead_scores` table |
| **Tuần 4** | Tích hợp SHAP Explainer | Explainability pipeline |
| **Tuần 4-5** | Tạo dữ liệu mẫu `consultation_log` | Dữ liệu giả lập để test Lead Queue |
| **Tuần 5** | Tích hợp Deepseek/Gemini API | LLM Pitching pipeline |
| **Tuần 6** | Integration test toàn bộ pipeline | End-to-end system hoạt động |

---

## 7. KIẾN TRÚC THƯ MỤC DỮ LIỆU & MODEL

```text
ai-transaction-analyzer/
│
├── data/
│   ├── raw/                          # PaySim.csv, transactions.csv (gốc)
│   ├── processed/                    # cleaned_transactions.parquet
│   ├── features/                     # user_features.parquet, fraud_features.parquet
│   ├── product_catalog.csv           # 6 sản phẩm mẫu
│   └── fraud_labels.csv              # Label fraud 0/1
│
├── models/                           # Model đã train
│   ├── isolation_forest.pkl
│   ├── xgboost_fraud.json
│   └── scaler.pkl                    # StandardScaler cho feature normalization
│
├── configs/
│   ├── fraud_rules.json              # 7 luật + ngưỡng
│   ├── product_catalog.json          # Danh mục + công thức score
│   ├── lead_score_weights.json       # Trọng số 5 thành phần
│   └── campaigns.json                # Cấu hình chiến dịch
│
└── notebooks/
    ├── 01_eda.ipynb                  # Khám phá dữ liệu
    ├── 02_feature_engineering.ipynb  # Tạo toàn bộ feature
    ├── 03_fraud_model_training.ipynb # Train Isolation Forest + XGBoost
    ├── 04_recommender_build.ipynb    # Xây dựng rule-based recommender
    └── 05_lead_scoring.ipynb         # Lead Score Calculator
```

---

## 8. TÓM TẮT NHANH

| Hạng mục | Số lượng |
|---|---|
| **Mô hình cần train** | 2 (Isolation Forest + XGBoost) |
| **Mô hình cần code** | 3 (Rule Filter + Rule Recommender + Lead Score) |
| **API bên ngoài** | 2 (Deepseek + Gemini) |
| **Tổng feature User** | 31 |
| **Tổng feature Fraud** | 31 |
| **Số luật Fraud** | 7 |
| **Số sản phẩm gợi ý** | 6 |
| **Dataset khởi đầu** | PaySim + Transaction Dataset |
| **Bảng DB tối thiểu** | 6 (`transactions`, `user_features`, `product_catalog`, `fraud_alerts`, `fraud_model_scores`, `consultation_log`) |
