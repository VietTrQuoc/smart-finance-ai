# Hướng dẫn Feature Engineering cho XGBoost Fraud Detection (Đã kiểm chứng)

> **Nguồn dữ liệu:** `data/synthetic_fraud_data.csv`
> **Công cụ profiling:** YData Profiling v4.19.1

---

## 1. Tổng quan Dataset (ĐÃ KIỂM CHỨNG)

| Chỉ số | Giá trị |
|---|---|
| Số dòng (observations) | **7,483,766** |
| Số cột (variables) | **24** |
| Missing cells | **0** (0.0%) |
| Duplicate rows | **0** (0.0%) |
| Total size in memory | 1.1 GiB |
| Average record size | 164.0 B |

### Phân bố kiểu dữ liệu (theo report)

| Kiểu | Số lượng | Các cột |
|---|---|---|
| **Text** | 6 | `transaction_id`, `customer_id`, `merchant`, `device_fingerprint`, `ip_address`, `velocity_last_hour` |
| **Numeric** | 3 | `card_number`, `amount`, `transaction_hour` |
| **DateTime** | 1 | `timestamp` |
| **Categorical** | 10 | `merchant_category`, `merchant_type`, `currency`, `country`, `city`, `city_size`, `card_type`, `device`, `channel`, `distance_from_home` |
| **Boolean** | 4 | `card_present`, `high_risk_merchant`, `weekend_transaction`, `is_fraud` |

---

## 2. Biến mục tiêu: `is_fraud`

| Giá trị | Số lượng | Tỷ lệ |
|---|---|---|
| `False` (không fraud) | 5,989,047 | **80.0%** |
| `True` (fraud) | 1,494,719 | **20.0%** |

- **Mất cân bằng:** 80/20 → dùng `scale_pos_weight ≈ 4.0` khi train XGBoost
- **Kiểu:** Boolean
- **Metric khuyến nghị:** PR-AUC (quan trọng hơn Accuracy với bài toán fraud)

---

## 3. Thống kê từng biến (ĐÃ KIỂM CHỨNG từ report.html)

### 3.1. Biến định danh — KHÔNG dùng trực tiếp

| Biến | Kiểu | Distinct | Distinct % | Khuyến nghị |
|---|---|---|---|---|
| `transaction_id` | Text | 7,477,306 | 99.9% | ❌ Không dùng — gần unique, gây overfit |
| `customer_id` | Text | 4,869 | 0.1% | ⚠️ Chỉ dùng để tạo aggregate features |
| `card_number` | Numeric | 5,000 | 0.1% | ⚠️ Chỉ dùng để tạo aggregate features |
| `ip_address` | Text | 7,477,187 | 99.9% | ⚠️ Chỉ dùng để tạo aggregate features (subnet, count) |
| `device_fingerprint` | Text | 785,462 | 10.5% | ⚠️ Chỉ dùng để tạo aggregate features |
| `velocity_last_hour` | **Text** | **0** | **0.0%** | ❌ **CỘT RỖNG — KHÔNG CÓ DỮ LIỆU THỰC TẾ.** Không dùng! |

> ⚠️ **Cảnh báo quan trọng về `velocity_last_hour`:** Report cho thấy cột này có kiểu Text, Distinct = 0, Missing = 0 — tức là **toàn bộ giá trị giống hệt nhau** (có thể là chuỗi rỗng). Cột này **vô giá trị** và phải bị loại bỏ hoàn toàn.

### 3.2. Biến giao dịch (Numeric)

| Biến | Kiểu | Distinct | Ghi chú |
|---|---|---|---|
| `amount` | Numeric | — | Phân phối lệch mạnh, max >> median. Rất quan trọng cho fraud detection |
| `transaction_hour` | Numeric | 24 | Có 155,759 (2.1%) zeros. Dùng cyclical encoding |

### 3.3. Biến thời gian

| Biến | Kiểu | Distinct |
|---|---|---|
| `timestamp` | DateTime | — |
| `weekend_transaction` | Boolean | 2 |

### 3.4. Biến Merchant

| Biến | Kiểu | Distinct | Ghi chú |
|---|---|---|---|
| `merchant_category` | Categorical | **8** | Phân bố khá đều (~936K mỗi loại cho top 5) |
| `merchant_type` | Categorical | **17** | Phân bố đa dạng, hữu ích cho target encoding |
| `merchant` | Text | **105** | Có thể dùng frequency/target encoding |
| `high_risk_merchant` | Boolean | 2 | Cờ rủi ro trực tiếp |

### 3.5. Biến Vị trí & Tiền tệ

| Biến | Kiểu | Distinct | Ghi chú |
|---|---|---|---|
| `country` | Categorical | **12** | Hữu ích phát hiện giao dịch khác khu vực |
| `city` | Categorical | — | ⚠️ Imbalanced (83.4%) |
| `city_size` | Categorical | 2 | ⚠️ Imbalanced (82.3%) |
| `currency` | Categorical | **11** | Phản ánh giao dịch quốc tế |
| `distance_from_home` | **Categorical** | 2 | Giá trị: `0` (67.8%), `1` (32.2%). **Tương quan mạnh nhất với `is_fraud`** |

### 3.6. Biến Thanh toán & Thiết bị

| Biến | Kiểu | Distinct | Ghi chú |
|---|---|---|---|
| `card_type` | Categorical | **5** | Basic Debit, Premium Debit, Platinum Credit, Gold Credit, Basic Credit |
| `card_present` | Boolean | 2 | ⚠️ Imbalanced (57.4%). False=91.3%, True=8.7% |
| `channel` | Categorical | **3** | `web`, `mobile`, `pos` |
| `device` | Categorical | **9** | Edge, iOS App, Chrome, Android App, Firefox... |

---

## 4. Cảnh báo tương quan (ĐÃ KIỂM CHỨNG từ report.html — 16 alerts)

### 4.1. Tương quan cao (12 alerts)

#### Nhóm 1: `card_present` — `channel` — `device` — `is_fraud`

```
card_present ↔ channel    : HIGH
card_present ↔ device     : HIGH
card_present ↔ is_fraud   : HIGH
channel      ↔ device     : HIGH
channel      ↔ is_fraud   : HIGH
device       ↔ is_fraud   : HIGH
```

> **Hệ quả:** 4 biến này tạo thành một cụm tương quan chặt. Khi dùng XGBoost (có khả năng xử lý đa cộng tuyến tốt hơn hồi quy tuyến tính), vẫn nên giữ tất cả và để model tự học — nhưng cần theo dõi feature importance để phát hiện redundancy.

#### Nhóm 2: `merchant_category` — `merchant_type` — `high_risk_merchant`

```
high_risk_merchant ↔ merchant_category : HIGH
high_risk_merchant ↔ merchant_type    : HIGH
merchant_category  ↔ merchant_type    : HIGH
```

> **Hệ quả:** Cả 3 biến đều mang thông tin về merchant. Nên giữ lại tất cả, dùng target encoding thay vì one-hot để giảm chiều.

#### Nhóm 3: `city_size` là trung tâm (hub)

```
city_size ↔ city      : HIGH
city_size ↔ country   : HIGH
city_size ↔ currency  : HIGH
country   ↔ currency  : HIGH
```

> ⚠️ **Lưu ý quan trọng:** Report **KHÔNG** ghi nhận tương quan trực tiếp giữa `city` ↔ `country` hoặc `city` ↔ `currency`. `city_size` đóng vai trò trung tâm kết nối nhóm này, không phải tất cả đều tương quan với nhau. Không nên loại bỏ hàng loạt các biến trong nhóm này chỉ vì "tương quan chặt chẽ với nhau".

#### Nhóm 4: `distance_from_home` — `is_fraud`

```
distance_from_home ↔ is_fraud : HIGH (tương quan mạnh nhất)
```

> Đây là tín hiệu **mạnh nhất** trong toàn bộ dataset. Cần kiểm tra leakage: liệu `distance_from_home` có được tính từ thông tin sau giao dịch không?

### 4.2. Mất cân bằng (3 alerts)

| Biến | Mức imbalance |
|---|---|
| `city` | 83.4% |
| `city_size` | 82.3% |
| `card_present` | 57.4% |

### 4.3. Zeros (1 alert)

| Biến | Số lượng zeros | Tỷ lệ |
|---|---|---|
| `transaction_hour` | 155,759 | 2.1% |

---

## 5. Chiến lược chọn và xử lý biến (ĐÃ HIỆU CHỈNH)

### 5.1. Biến GIỮ LẠI — dùng trực tiếp

```text
amount
merchant_category
merchant_type
merchant
currency
country
city
city_size
card_type
card_present
device
channel
distance_from_home
high_risk_merchant
transaction_hour
weekend_transaction
```

### 5.2. Biến CHỈ DÙNG để tạo aggregate features

```text
customer_id       → customer-level history features
card_number       → card-level history features
device_fingerprint → device-level behavior features
ip_address        → IP-level behavior features
timestamp         → time-based features (không dùng raw)
```

### 5.3. Biến LOẠI BỎ HOÀN TOÀN

```text
transaction_id      → gần unique, không có ý nghĩa dự đoán
velocity_last_hour  → CỘT RỖNG, không có dữ liệu thực tế
is_fraud            → target, không đưa vào X
```

---

## 6. Feature Engineering đề xuất (theo mức ưu tiên)

### Priority 1 — Làm trước (baseline)

**Amount features:**
```text
log_amount = log1p(amount)
amount_bin (phân nhóm theo quantile)
```

**Time features:**
```text
hour_sin = sin(2π × transaction_hour / 24)
hour_cos = cos(2π × transaction_hour / 24)
day_of_week (từ timestamp)
is_night (22h-6h)
is_weekend (dùng sẵn weekend_transaction)
```

**One-hot encoding (cột ít giá trị):**
```text
merchant_category  (8)
card_type          (5)
channel            (3)
city_size          (2)
card_present       (2)
distance_from_home (2)
high_risk_merchant (2)
weekend_transaction(2)
```

**Frequency encoding (cột nhiều giá trị):**
```text
merchant           (105)
device             (9)
country            (12)
city               (~11)
currency           (11)
```

### Priority 2 — Sau khi baseline chạy được

**Customer-level aggregates (từ `customer_id`):**
```text
customer_txn_count
customer_avg_amount
customer_std_amount
customer_amount_zscore = (amount - customer_avg) / customer_std
customer_unique_merchants
customer_unique_countries
customer_unique_devices
customer_time_since_last_txn
customer_txn_count_last_1h
customer_txn_count_last_24h
```

**Card-level aggregates (từ `card_number`):**
```text
card_txn_count
card_avg_amount
card_unique_devices
card_unique_countries
card_time_since_last_txn
```

**Merchant-level aggregates:**
```text
merchant_avg_amount
merchant_txn_count
amount_ratio_to_merchant_avg = amount / merchant_avg_amount
amount_ratio_to_category_avg = amount / category_avg_amount
```

**Device/Channel interaction features:**
```text
device_group: browser / app / pos
channel_device_match
is_card_not_present
is_online_channel = (channel != 'pos')
```

### Priority 3 — Nâng cao (tăng performance)

**Target Encoding OOF (out-of-fold):**
```text
merchant_fraud_rate_oof
merchant_category_fraud_rate_oof
merchant_type_fraud_rate_oof
country_fraud_rate_oof
city_fraud_rate_oof
device_fraud_rate_oof
channel_fraud_rate_oof
```

**Velocity features (từ timestamp, cần sort theo thời gian):**
```text
customer_txn_count_last_5min
customer_txn_count_last_1h
customer_txn_count_last_24h
card_txn_count_last_1h
device_txn_count_last_1h
customer_amount_sum_last_1h
customer_amount_sum_last_24h
customer_unique_merchants_last_24h
customer_unique_countries_last_24h
```

**Cross-features (tương tác):**
```text
high_risk_merchant × amount
high_risk_merchant × is_online_channel
card_not_present × log_amount
online_channel × distance_from_home
is_night × is_online_channel
```

**Device fingerprint aggregates:**
```text
device_txn_count
device_unique_customers
device_unique_cards
is_shared_device
is_new_device_for_customer
```

**Location/Geo features:**
```text
is_new_country_for_customer
is_new_city_for_customer
num_countries_used_by_customer
num_cities_used_by_customer
is_foreign_currency
```

---

## 7. Cấu hình XGBoost đề xuất

```python
from xgboost import XGBClassifier

model = XGBClassifier(
    n_estimators=500,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective='binary:logistic',
    eval_metric='aucpr',
    scale_pos_weight=4.0,      # 5,989,047 / 1,494,719
    tree_method='hist',
    random_state=42,
    n_jobs=-1
)
```

### Metrics theo dõi

| Metric | Mức độ quan trọng | Lý do |
|---|---|---|
| **PR-AUC** | ⭐⭐⭐ | Quan trọng nhất cho bài toán imbalance |
| ROC-AUC | ⭐⭐ | Bổ trợ |
| Recall @ Precision fixed | ⭐⭐ | Tùy ngưỡng nghiệp vụ |
| Fraud Recall | ⭐⭐⭐ | Không được bỏ sót fraud |
| False Positive Rate | ⭐⭐ | Không được cảnh báo quá nhiễu |

---

## 8. Lưu ý quan trọng — Tránh Data Leakage

1. ❌ **Không** dùng `is_fraud` trong tập feature X.
2. ❌ **Không** dùng `transaction_id` làm feature.
3. ❌ **Không** dùng `velocity_last_hour` (cột rỗng).
4. ⚠️ **Chia train/test theo thời gian** (time-based split), không random split, để mô phỏng production.
5. ⚠️ Khi tạo các feature rolling/velocity, **chỉ dùng dữ liệu trước thời điểm giao dịch hiện tại**.
6. ⚠️ Target encoding phải dùng **out-of-fold (OOF)** — không tính fraud rate trên toàn bộ train rồi áp dụng ngược lại.
7. ⚠️ Kiểm tra `distance_from_home` có bị leakage không — nếu nó được tính từ thông tin sau giao dịch hoặc từ rule fraud có sẵn, phải loại bỏ.
8. ⚠️ Khi tạo `customer_avg_amount`, `merchant_fraud_rate`, `device_fraud_rate` — đảm bảo chỉ dùng dữ liệu lịch sử (trước thời điểm giao dịch).

---

## 9. Tóm tắt các điểm đã hiệu chỉnh so với báo cáo cũ

| Điểm | Báo cáo cũ sai | Đã sửa thành |
|---|---|---|
| `velocity_last_hour` | "Thể hiện hành vi bất thường", khuyến nghị dùng | **Cột rỗng (Distinct=0, kiểu Text) → LOẠI BỎ** |
| Tương quan city/country/currency | "cả 4 tương quan chặt chẽ với nhau" | **Chỉ `city_size` là hub; `city` không tương quan trực tiếp với `country`/`currency`** |
| `distance_from_home` | Boolean (ngầm định) | **Categorical (2 values: 0, 1)** |
| Loại bỏ `merchant_type`, `device` | Đề xuất bỏ | **Giữ lại, dùng target/frequency encoding** |
| Loại bỏ `city`, `currency` | Đề xuất bỏ | **Giữ lại, cân nhắc kỹ trước khi bỏ** |

---

*Tài liệu được tổng hợp và kiểm chứng dựa trên `report.html` (YData Profiling v4.19.1) — ngày 2026-06-02.*
