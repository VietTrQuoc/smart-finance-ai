# Thiết kế cơ sở dữ liệu — AI Transaction Analyzer

> **Hệ thống: AI Phân tích Giao dịch Toàn diện — Phát hiện Gian lận & Khuyến nghị Sản phẩm Tài chính**

---

## 1. Sơ đồ quan hệ (ERD)

```mermaid
erDiagram
    TRANSACTIONS ||--o{ USER_FEATURES : "aggregates to"
    TRANSACTIONS ||--o{ FRAUD_ALERTS : "triggers"
    TRANSACTIONS ||--o{ FRAUD_MODEL_SCORES : "scored as"
    
    USER_FEATURES ||--o{ RECOMMENDATION_LOGS : "receives"
    USER_FEATURES ||--o{ PITCH_LOGS : "receives pitch for"
    USER_FEATURES ||--o{ FRAUD_ALERTS : "has"
    USER_FEATURES ||--o{ CONSULTATION_LOG : "consulted for"
    USER_FEATURES ||--|| LEAD_SCORES : "has"
    USER_FEATURES ||--o{ USER_SEGMENTS : "assigned to"
    SEGMENTATION_MODEL_VERSIONS ||--o{ USER_SEGMENTS : "assigns"
    SEGMENTATION_MODEL_VERSIONS ||--o{ CLUSTER_PROFILES : "defines"
    SEGMENTATION_MODEL_VERSIONS ||--o{ SEGMENTATION_RUNS : "produces"
    
    PRODUCT_CATALOG ||--o{ RECOMMENDATION_LOGS : "recommended in"
    PRODUCT_CATALOG ||--o{ PITCH_LOGS : "pitched in"
    PRODUCT_CATALOG ||--o{ CONSULTATION_LOG : "consulted for"
    
    MARKETING_CAMPAIGNS ||--o{ LEAD_SCORES : "filters"
    
    FRAUD_RULES ||--o{ FRAUD_ALERTS : "triggers"

    TRANSACTIONS {
        text transaction_id PK
        text user_id FK
        timestamp transaction_time
        float amount
        text transaction_type
        text merchant_name
        text merchant_category
        text country
        text city
        text card_type
        boolean card_present
        float balance_before
        float balance_after
        text channel
        text device_id
        text device_fingerprint
        text ip_address
        text status
        boolean is_fraud
    }

    USER_FEATURES {
        text user_id PK
        float recency_days
        float frequency_7d
        float frequency_30d
        float frequency_90d
        float monetary_7d
        float monetary_30d
        float monetary_90d
        float avg_transaction_amount
        float max_transaction_amount
        float std_transaction_amount
        float shopping_ratio
        float travel_ratio
        float food_ratio
        float education_ratio
        float healthcare_ratio
        float entertainment_ratio
        float cashout_ratio
        float transfer_ratio
        float loan_payment_ratio
        float income_total_30d
        float expense_total_30d
        float net_cashflow_30d
        int negative_cashflow_days
        int end_month_negative_cashflow_flag
        float balance_volatility
        int salary_detected_flag
        float weekend_spending_ratio
        float night_transaction_ratio
        int travel_frequency_90d
        int shopping_frequency_30d
        float risk_score
        timestamp updated_at
    }

    PRODUCT_CATALOG {
        text product_id PK
        text product_name
        text product_type
        text description
        text target_behavior
        text target_signals_json
        text eligibility_json
        text risk_allowed
        float campaign_priority
        text reason_template
        boolean is_active
        timestamp created_at
    }

    FRAUD_ALERTS {
        text alert_id PK
        text user_id FK
        text transaction_id FK
        text fraud_type
        float fraud_score
        text severity
        text description
        text evidence
        text alert_status
        text reviewed_by
        timestamp reviewed_at
        timestamp created_at
    }

    FRAUD_MODEL_SCORES {
        text score_id PK
        text user_id FK
        text transaction_id FK
        float xgboost_score
        float final_fraud_score
        float decision_threshold
        boolean predicted_fraud
        text shap_values
        text features_used
        text model_version
        timestamp created_at
    }

    FRAUD_RULES {
        text rule_id PK
        text rule_name
        text rule_type
        text condition
        float threshold
        text severity
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    RECOMMENDATION_LOGS {
        text log_id PK
        text user_id FK
        text product_id FK
        float score
        text score_breakdown_json
        text reason_json
        float fraud_score
        float risk_score
        text model_version
        timestamp created_at
    }

    PITCH_LOGS {
        text pitch_id PK
        text user_id FK
        text product_id FK
        text prompt
        text generated_script
        text llm_model
        int tokens_used
        timestamp created_at
    }

    CONSULTATION_LOG {
        text consultation_id PK
        text user_id FK
        text marketer_id
        text product_id FK
        text top_3_products
        float lead_score_at_time
        text pitch_script_used
        text consultation_status
        text contact_channel
        text notes
        timestamp contacted_at
        timestamp next_follow_up_at
        timestamp created_at
    }

    LEAD_SCORES {
        text user_id PK
        float lead_score
        text lead_tier
        text top_product_id FK
        float top_product_score
        float product_match_score
        float propensity_score
        float recency_score
        float customer_value_score
        float fatigue_score
        int days_since_last_contact
        int contact_count_30d
        text last_contact_status
        text eligibility_status
        timestamp calculated_at
    }

    SEGMENTATION_MODEL_VERSIONS {
        text model_version PK
        int n_components
        int k
        text scaler_path
        text svd_path
        text kmeans_path
        text feature_schema
        text metrics_json
        text selection_policy
        text status
        timestamp trained_at
        timestamp activated_at
        text created_by
    }

    USER_SEGMENTS {
        text user_id PK
        int cluster_id
        text model_version FK
        float distance_to_centroid
        text assignment_mode
        timestamp assigned_at
    }

    CLUSTER_PROFILES {
        text model_version FK
        int cluster_id
        text cluster_name
        text description
        int size
        float ratio
        text top_features_json
        text product_hints_json
        float llm_confidence
    }

    SEGMENTATION_RUNS {
        text run_id PK
        text model_version FK
        text mode
        text status
        int users_processed
        float duration_seconds
        text error_message
        timestamp started_at
        timestamp finished_at
    }

    MARKETING_CAMPAIGNS {
        text campaign_id PK
        text campaign_name
        text description
        text target_product_type
        text target_behavior
        float min_lead_score
        boolean is_active
        date start_date
        date end_date
        timestamp created_at
    }
```

---

## 2. Chi tiết từng bảng

### 2.1. Bảng `transactions`

Bảng gốc — lưu toàn bộ giao dịch của hệ thống.

```sql
CREATE TABLE transactions (
    transaction_id      TEXT PRIMARY KEY,
    user_id             TEXT NOT NULL,
    transaction_time    TIMESTAMP NOT NULL,
    amount              FLOAT NOT NULL,
    transaction_type    TEXT,               -- 'transfer', 'payment', 'deposit', 'withdrawal', 'refund'
    merchant_name       TEXT,
    merchant_category   TEXT,               -- 'shopping', 'travel', 'food', 'healthcare', 'education', ...
    country             TEXT,               -- Quốc gia giao dịch (từ CSV)
    city                TEXT,               -- Thành phố giao dịch (từ CSV)
    card_type           TEXT,               -- 'credit', 'debit', 'prepaid' (từ CSV)
    card_present        BOOLEAN,            -- Thẻ có mặt tại POS? (từ CSV, dùng cho fraud)
    balance_before      FLOAT,              -- ⚠️ Dataset thiếu — ước lượng từ amount + transaction_type
    balance_after       FLOAT,              -- ⚠️ Dataset thiếu — ước lượng từ amount + transaction_type
    channel             TEXT,               -- 'mobile_app', 'web', 'atm', 'pos', 'bank_counter'
    device_id           TEXT,
    device_fingerprint  TEXT,               -- Vân tay thiết bị (từ CSV, dùng cho Account Takeover detection)
    ip_address          TEXT,
    status              TEXT DEFAULT 'completed',  -- 'completed', 'pending', 'failed', 'reversed'
    is_fraud            BOOLEAN DEFAULT FALSE,     -- Nhãn fraud 0/1 — bắt buộc cho XGBoost training
    
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_tx_user_id ON transactions(user_id);
CREATE INDEX idx_tx_time ON transactions(transaction_time DESC);
CREATE INDEX idx_tx_user_time ON transactions(user_id, transaction_time DESC);
CREATE INDEX idx_tx_category ON transactions(merchant_category);
CREATE INDEX idx_tx_device ON transactions(device_id);
CREATE INDEX idx_tx_device_fp ON transactions(device_fingerprint);
CREATE INDEX idx_tx_status ON transactions(status);
CREATE INDEX idx_tx_fraud ON transactions(is_fraud);
```

| Cột | Kiểu | Mô tả |
|---|---|---|
| `transaction_id` | TEXT PK | Mã giao dịch duy nhất |
| `user_id` | TEXT NOT NULL | Mã khách hàng |
| `transaction_time` | TIMESTAMP | Thời gian giao dịch |
| `amount` | FLOAT | Số tiền giao dịch |
| `transaction_type` | TEXT | Loại giao dịch |
| `merchant_name` | TEXT | Tên merchant |
| `merchant_category` | TEXT | Danh mục chi tiêu |
| `country` | TEXT | Quốc gia giao dịch |
| `city` | TEXT | Thành phố giao dịch |
| `card_type` | TEXT | Loại thẻ (credit/debit/prepaid) |
| `card_present` | BOOLEAN | Thẻ có mặt tại POS? |
| `balance_before` | FLOAT | Số dư trước giao dịch ⚠️ ước lượng |
| `balance_after` | FLOAT | Số dư sau giao dịch ⚠️ ước lượng |
| `channel` | TEXT | Kênh giao dịch |
| `device_id` | TEXT | Mã thiết bị |
| `device_fingerprint` | TEXT | Vân tay thiết bị (Account Takeover) |
| `ip_address` | TEXT | Địa chỉ IP |
| `status` | TEXT | Trạng thái giao dịch |
| `is_fraud` | BOOLEAN | Nhãn fraud 0/1 (dùng cho training) |

---

### 2.2. Bảng `user_features`

Bảng feature đã được tính sẵn cho mỗi user — dùng cho Recommendation + Lead Scoring.

```sql
CREATE TABLE user_features (
    user_id                         TEXT PRIMARY KEY,
    
    -- RFM Features
    recency_days                    FLOAT,      -- Số ngày từ giao dịch gần nhất
    frequency_7d                    INTEGER,    -- Số giao dịch 7 ngày
    frequency_30d                   INTEGER,    -- Số giao dịch 30 ngày
    frequency_90d                   INTEGER,    -- Số giao dịch 90 ngày
    monetary_7d                     FLOAT,      -- Tổng tiền 7 ngày
    monetary_30d                    FLOAT,      -- Tổng tiền 30 ngày
    monetary_90d                    FLOAT,      -- Tổng tiền 90 ngày
    avg_transaction_amount          FLOAT,      -- Giá trị giao dịch trung bình
    max_transaction_amount          FLOAT,      -- Giá trị giao dịch lớn nhất
    std_transaction_amount          FLOAT,      -- Độ lệch chuẩn giá trị
    
    -- Category Ratios (tỷ trọng 0-1)
    shopping_ratio                  FLOAT,
    travel_ratio                    FLOAT,
    food_ratio                      FLOAT,
    education_ratio                 FLOAT,
    healthcare_ratio                FLOAT,
    entertainment_ratio             FLOAT,
    cashout_ratio                   FLOAT,
    transfer_ratio                  FLOAT,
    loan_payment_ratio              FLOAT,
    
    -- Cashflow Features
    income_total_30d                FLOAT,
    expense_total_30d               FLOAT,
    net_cashflow_30d                FLOAT,      -- income - expense
    negative_cashflow_days          INTEGER,    -- Số ngày dòng tiền âm
    end_month_negative_cashflow_flag INTEGER,   -- 0/1: cuối tháng thiếu tiền
    balance_volatility              FLOAT,      -- Độ biến động số dư
    salary_detected_flag            INTEGER,    -- 0/1: phát hiện lương
    
    -- Behavior Cycle Features
    weekend_spending_ratio          FLOAT,
    night_transaction_ratio         FLOAT,
    travel_frequency_90d            INTEGER,    -- Số giao dịch du lịch 90 ngày
    shopping_frequency_30d          INTEGER,    -- Số giao dịch mua sắm 30 ngày
    
    -- Risk
    risk_score                      FLOAT,      -- Điểm rủi ro tín dụng (0-1)
    
    updated_at                      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_uf_recency ON user_features(recency_days);
CREATE INDEX idx_uf_monetary ON user_features(monetary_30d DESC);
CREATE INDEX idx_uf_risk ON user_features(risk_score);
```

---

### 2.3. Bảng `product_catalog`

Danh mục sản phẩm tài chính có thể gợi ý.

```sql
CREATE TABLE product_catalog (
    product_id          TEXT PRIMARY KEY,
    product_name        TEXT NOT NULL,
    product_type        TEXT NOT NULL,          -- 'credit_card', 'insurance', 'loan', 'saving'
    description         TEXT,
    target_behavior     TEXT,                   -- 'shopping_high', 'travel_high', 'negative_cashflow', ...
    target_signals_json TEXT,                   -- JSON: feature weights for behavior_match
    eligibility_json    TEXT,                   -- JSON: min income, age, KYC, ownership, cooldown rules
    risk_allowed        TEXT DEFAULT 'low',     -- 'low', 'medium', 'high'
    min_risk_score      FLOAT DEFAULT 0.0,
    max_risk_score      FLOAT DEFAULT 1.0,
    campaign_priority   FLOAT DEFAULT 0.5,      -- normalized business priority (0-1)
    reason_template     TEXT,                   -- reusable reason copy for recommendation output
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_prod_type ON product_catalog(product_type);
CREATE INDEX idx_prod_active ON product_catalog(is_active);
```

**Dữ liệu mẫu:**

| product_id | product_name | product_type | target_behavior | risk_allowed |
|---|---|---|---|---|
| P001 | Thẻ tín dụng hoàn tiền | credit_card | shopping_high | medium |
| P002 | Bảo hiểm du lịch | insurance | travel_high | low |
| P003 | Vay tiêu dùng | loan | negative_cashflow | medium |
| P004 | Vay thấu chi | loan | end_month_cash_shortage | medium |
| P005 | Gói tiết kiệm linh hoạt | saving | positive_cashflow | low |
| P006 | Bảo hiểm sức khỏe | insurance | healthcare_high | low |

---

### 2.4. Bảng `fraud_alerts`

Lưu các cảnh báo gian lận được sinh ra từ Fraud Detection Engine.

```sql
CREATE TABLE fraud_alerts (
    alert_id            TEXT PRIMARY KEY,
    user_id             TEXT NOT NULL,
    transaction_id      TEXT,
    fraud_type          TEXT,                   -- 'account_takeover', 'money_mule', 'fake_identity', ...
    fraud_score         FLOAT NOT NULL,         -- 0-1
    severity            TEXT NOT NULL,          -- 'high', 'medium', 'low'
    description         TEXT,
    evidence            TEXT,                   -- JSON: danh sách bằng chứng ["device_change", "amount_spike", ...]
    alert_status        TEXT DEFAULT 'open',    -- 'open', 'confirmed', 'false_positive', 'resolved'
    reviewed_by         TEXT,                   -- Mã fraud analyst
    reviewed_at         TIMESTAMP,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES user_features(user_id),
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
);

CREATE INDEX idx_fa_user ON fraud_alerts(user_id, created_at DESC);
CREATE INDEX idx_fa_status ON fraud_alerts(alert_status, severity);
CREATE INDEX idx_fa_score ON fraud_alerts(fraud_score DESC);
CREATE INDEX idx_fa_created ON fraud_alerts(created_at DESC);
```

---

### 2.5. Bảng `fraud_model_scores`

Lưu điểm dự đoán từ XGBoost Fraud Classifier để audit và debug. Production fraud prediction hiện dùng XGBoost-only; rule guardrail nếu có chỉ lưu ở `fraud_rules`/`fraud_alerts`, không tham gia model score.

```sql
CREATE TABLE fraud_model_scores (
    score_id                TEXT PRIMARY KEY,
    user_id                 TEXT NOT NULL,
    transaction_id          TEXT,
    xgboost_score           FLOAT NOT NULL,     -- Probability từ XGBoost (0-1)
    final_fraud_score       FLOAT NOT NULL,     -- Bằng xgboost_score hoặc calibrated score
    decision_threshold      FLOAT DEFAULT 0.5,  -- Threshold đang dùng tại thời điểm score
    predicted_fraud         BOOLEAN,            -- final_fraud_score >= decision_threshold
    shap_values             TEXT,               -- JSON: {"amount_zscore": 0.35, "device_change": 0.28, ...}
    features_used           TEXT,               -- JSON: giá trị các feature đã dùng
    model_version           TEXT,               -- Phiên bản model
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES user_features(user_id),
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
);

CREATE INDEX idx_fms_user ON fraud_model_scores(user_id, created_at DESC);
CREATE INDEX idx_fms_tx ON fraud_model_scores(transaction_id);
CREATE INDEX idx_fms_score ON fraud_model_scores(final_fraud_score DESC);
```

---

### 2.6. Bảng `fraud_rules`

Cấu hình các rule phát hiện gian lận.

```sql
CREATE TABLE fraud_rules (
    rule_id         TEXT PRIMARY KEY,
    rule_name       TEXT NOT NULL,
    rule_type       TEXT NOT NULL,           -- 'velocity', 'amount', 'device', 'network', 'circular'
    condition       TEXT,                     -- Mô tả điều kiện (human-readable)
    threshold       FLOAT,                    -- Ngưỡng kích hoạt
    severity        TEXT DEFAULT 'medium',    -- 'high', 'medium', 'low'
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Dữ liệu mẫu:**

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

### 2.7. Bảng `recommendation_logs`

Ghi nhận mỗi lần hệ thống gợi ý sản phẩm cho user.

```sql
CREATE TABLE recommendation_logs (
    log_id          TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL,
    product_id      TEXT NOT NULL,
    score           FLOAT NOT NULL,            -- Điểm phù hợp (0-1)
    score_breakdown_json TEXT,                  -- JSON: behavior_match, segment_affinity, affordability_fit, ...
    reason_json     TEXT,                       -- JSON: 2-3 reasons shown to marketer
    fraud_score     FLOAT,                      -- Fraud score tại thời điểm gợi ý
    risk_score      FLOAT,                      -- Risk score tại thời điểm gợi ý
    model_version   TEXT,                       -- Segmentation/model version used for context
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES user_features(user_id),
    FOREIGN KEY (product_id) REFERENCES product_catalog(product_id)
);

CREATE INDEX idx_rl_user ON recommendation_logs(user_id, created_at DESC);
CREATE INDEX idx_rl_product ON recommendation_logs(product_id, created_at DESC);
```

---

### 2.8. Bảng `pitch_logs`

Ghi nhận mỗi lần LLM sinh kịch bản tư vấn.

```sql
CREATE TABLE pitch_logs (
    pitch_id            TEXT PRIMARY KEY,
    user_id             TEXT NOT NULL,
    product_id          TEXT NOT NULL,
    prompt              TEXT,                   -- Prompt đã gửi cho LLM
    generated_script    TEXT,                   -- Kịch bản LLM sinh ra
    llm_model           TEXT,                   -- 'deepseek-chat', 'gemini-1.5-flash', ...
    tokens_used         INTEGER,                -- Số token đã dùng
    latency_ms          INTEGER,                -- Thời gian phản hồi (ms)
    fraud_score         FLOAT,                  -- Fraud score tại thời điểm sinh
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES user_features(user_id),
    FOREIGN KEY (product_id) REFERENCES product_catalog(product_id)
);

CREATE INDEX idx_pl_user ON pitch_logs(user_id, created_at DESC);
CREATE INDEX idx_pl_model ON pitch_logs(llm_model, created_at DESC);
```

---

### 2.9. Bảng `consultation_log` ⭐

**Bảng quan trọng nhất cho Lead Scoring** — ghi nhận mỗi lần marketer tư vấn khách hàng.

```sql
CREATE TABLE consultation_log (
    consultation_id         TEXT PRIMARY KEY,
    user_id                 TEXT NOT NULL,
    marketer_id             TEXT,               -- Mã nhân viên tiếp thị
    product_id              TEXT,               -- Sản phẩm được tư vấn
    top_3_products          TEXT,               -- JSON: ["P002", "P001", "P005"]
    lead_score_at_time      FLOAT,              -- Lead score tại thời điểm tư vấn
    pitch_script_used       TEXT,               -- Kịch bản đã dùng
    consultation_status     TEXT DEFAULT 'pending',  -- 'pending', 'contacted', 'interested', 'not_interested', 'converted', 'no_answer'
    contact_channel         TEXT,               -- 'phone', 'email', 'sms', 'in_person'
    notes                   TEXT,               -- Ghi chú từ marketer
    contacted_at            TIMESTAMP,          -- Thời điểm liên hệ thực tế
    next_follow_up_at       TIMESTAMP,          -- Lịch follow-up
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES user_features(user_id),
    FOREIGN KEY (product_id) REFERENCES product_catalog(product_id)
);

-- Indexes quan trọng cho Lead Scoring
CREATE INDEX idx_cl_user ON consultation_log(user_id, contacted_at DESC);
CREATE INDEX idx_cl_marketer ON consultation_log(marketer_id, contacted_at DESC);
CREATE INDEX idx_cl_status ON consultation_log(consultation_status, contacted_at DESC);
CREATE INDEX idx_cl_followup ON consultation_log(next_follow_up_at) 
    WHERE next_follow_up_at IS NOT NULL;
```

| Cột | Mô tả |
|---|---|
| `consultation_id` | Mã lần tư vấn |
| `user_id` | Khách hàng được tư vấn |
| `marketer_id` | Nhân viên thực hiện |
| `product_id` | Sản phẩm chính được tư vấn |
| `top_3_products` | JSON 3 sản phẩm được gợi ý lúc đó |
| `lead_score_at_time` | Lead score tại thời điểm tư vấn |
| `consultation_status` | Trạng thái sau tư vấn |
| `contact_channel` | Kênh liên hệ |
| `next_follow_up_at` | Lịch hẹn gọi lại |

---

### 2.10. Bảng `lead_scores` ⭐

Bảng tính sẵn lead_score cho từng user — truy vấn nhanh cho Lead Queue.

```sql
CREATE TABLE lead_scores (
    user_id                     TEXT PRIMARY KEY,
    lead_score                  FLOAT NOT NULL,         -- 0-1
    lead_tier                   TEXT,                   -- 'hot' (>0.85), 'warm' (0.6-0.85), 'cold' (<0.6)
    
    -- Top Product
    top_product_id              TEXT,                   -- Sản phẩm có score cao nhất
    top_product_score           FLOAT,                  -- Score của sản phẩm đó
    
    -- Score Components
    product_match_score         FLOAT,                  -- w1 × max(top-3 score)
    propensity_score            FLOAT,                  -- w2 × nhu cầu
    recency_score               FLOAT,                  -- w3 × thời gian chưa liên hệ
    customer_value_score        FLOAT,                  -- w4 × giá trị khách hàng
    fatigue_score               FLOAT,                  -- w5 × tần suất liên hệ
    
    -- Contact Info
    days_since_last_contact     INTEGER,                -- NULL nếu chưa từng
    contact_count_30d           INTEGER DEFAULT 0,
    last_contact_status         TEXT,                   -- Trạng thái lần gần nhất
    
    -- Eligibility
    eligibility_status          TEXT DEFAULT 'eligible', -- 'eligible', 'fraud_blocked', 'recently_rejected', 'over_contacted'
    
    calculated_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES user_features(user_id),
    FOREIGN KEY (top_product_id) REFERENCES product_catalog(product_id)
);

-- Indexes cực kỳ quan trọng cho Lead Queue performance
CREATE INDEX idx_ls_score ON lead_scores(lead_score DESC);
CREATE INDEX idx_ls_tier ON lead_scores(lead_tier, lead_score DESC);
CREATE INDEX idx_ls_eligibility ON lead_scores(eligibility_status, lead_score DESC);
CREATE INDEX idx_ls_product ON lead_scores(top_product_id, lead_score DESC);
CREATE INDEX idx_ls_calculated ON lead_scores(calculated_at DESC);
```

**Công thức Lead Score:**

```text
LEAD_SCORE = 0.30 × product_match_score
           + 0.25 × propensity_score
           + 0.20 × recency_score
           + 0.15 × customer_value_score
           − 0.10 × fatigue_score
```

**Phân loại Lead Tier:**

| Tier | Điều kiện | Hành động |
|---|---|---|
| 🔥 **Hot** | `lead_score > 0.85` | Gọi ngay — ưu tiên cao nhất |
| 🟡 **Warm** | `0.6 ≤ lead_score ≤ 0.85` | Gọi trong tuần |
| 🔵 **Cold** | `lead_score < 0.6` | Gọi khi rảnh / chiến dịch đặc biệt |

---

### 2.11. Bảng `segmentation_model_versions`

Lưu metadata và artifact paths cho mỗi version phân cụm khách hàng. Chỉ một version nên có `status = 'active'` tại một thời điểm; full retrain tạo version `candidate` trước khi promote.

```sql
CREATE TABLE segmentation_model_versions (
    model_version          TEXT PRIMARY KEY,       -- VD: seg_2026_06_04_001
    n_components           INTEGER NOT NULL,       -- Số PC/SVD components được chọn
    k                      INTEGER NOT NULL,       -- Số cụm KMeans
    scaler_path            TEXT NOT NULL,          -- models/segmentation/<version>/scaler.pkl
    svd_path               TEXT NOT NULL,
    kmeans_path            TEXT NOT NULL,
    feature_schema         TEXT NOT NULL,          -- JSON: ordered feature list + preprocessing rules
    metrics_json           TEXT,                   -- JSON: explained variance, silhouette, DBI, CH, stability
    selection_policy       TEXT,                   -- JSON/text: rule chọn PC/K
    status                 TEXT DEFAULT 'candidate', -- 'candidate', 'active', 'archived', 'rejected'
    trained_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activated_at           TIMESTAMP,
    created_by             TEXT
);

CREATE INDEX idx_seg_model_status ON segmentation_model_versions(status, trained_at DESC);
```

---

### 2.12. Bảng `user_segments`

Lưu cụm của từng user theo từng `model_version`. Không được hiểu `cluster_id = 0` là cùng một ý nghĩa giữa các version khác nhau.

```sql
CREATE TABLE user_segments (
    user_id                 TEXT NOT NULL,
    model_version           TEXT NOT NULL,
    cluster_id              INTEGER NOT NULL,
    distance_to_centroid    FLOAT,                 -- Khoảng cách trong không gian SVD
    assignment_mode         TEXT DEFAULT 'predict', -- 'predict', 'full_retrain', 'manual_override'
    assigned_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id, model_version),
    FOREIGN KEY (user_id) REFERENCES user_features(user_id),
    FOREIGN KEY (model_version) REFERENCES segmentation_model_versions(model_version)
);

CREATE INDEX idx_user_segments_user ON user_segments(user_id, assigned_at DESC);
CREATE INDEX idx_user_segments_cluster ON user_segments(model_version, cluster_id);
```

---

### 2.13. Bảng `cluster_profiles`

Lưu tên, mô tả và insight của từng cụm theo version. Tên cụm do LLM gợi ý nhưng phải dựa trên aggregate profile, không dựa trên raw transaction hoặc PII.

```sql
CREATE TABLE cluster_profiles (
    model_version           TEXT NOT NULL,
    cluster_id              INTEGER NOT NULL,
    cluster_name            TEXT NOT NULL,
    description             TEXT,
    size                    INTEGER,
    ratio                   FLOAT,                 -- size / total users
    top_features_json       TEXT,                  -- JSON: top positive/negative z-score features
    product_hints_json      TEXT,                  -- JSON: product hints for recommender context
    centroid_json           TEXT,                  -- JSON: centroid/SVD vector if needed for audit
    previous_cluster_id     INTEGER,               -- Mapping với version trước nếu có
    previous_similarity     FLOAT,
    llm_model               TEXT,
    llm_confidence          FLOAT,
    needs_review            BOOLEAN DEFAULT FALSE,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (model_version, cluster_id),
    FOREIGN KEY (model_version) REFERENCES segmentation_model_versions(model_version)
);

CREATE INDEX idx_cluster_profiles_version ON cluster_profiles(model_version, cluster_id);
CREATE INDEX idx_cluster_profiles_review ON cluster_profiles(needs_review, created_at DESC);
```

`product_hints_json` chuẩn cho recommender:

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

---

### 2.14. Bảng `segmentation_runs`

Audit mỗi lần bấm cập nhật hoặc chạy cron. `changed_users` dùng model active để gán cụm nhanh; `full_retrain` tạo model candidate và không ghi đè active cho đến khi đạt quality threshold.

```sql
CREATE TABLE segmentation_runs (
    run_id                 TEXT PRIMARY KEY,
    model_version          TEXT,
    mode                   TEXT NOT NULL,          -- 'changed_users', 'full_retrain'
    status                 TEXT NOT NULL,          -- 'queued', 'running', 'succeeded', 'failed', 'rejected'
    triggered_by           TEXT,                   -- 'admin', 'cron', 'system'
    users_processed        INTEGER DEFAULT 0,
    changed_users_count    INTEGER DEFAULT 0,
    duration_seconds       FLOAT,
    metrics_json           TEXT,                   -- JSON: run-level metrics and checks
    error_message          TEXT,
    started_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at            TIMESTAMP,

    FOREIGN KEY (model_version) REFERENCES segmentation_model_versions(model_version)
);

CREATE INDEX idx_seg_runs_status ON segmentation_runs(status, started_at DESC);
CREATE INDEX idx_seg_runs_mode ON segmentation_runs(mode, started_at DESC);
```

**Production policy:**

- `cluster_id` chỉ ổn định trong cùng một `model_version`; mọi UI/API phải hiển thị kèm `model_version` hoặc lấy từ active version.
- Không hard-code `cluster_names = {0: ..., 1: ...}` trong code production. Tên cụm đọc từ `cluster_profiles`.
- LLM chỉ được nhận aggregate profile: size, ratio, centroid/profile similarity, top z-score features và product hints. Không gửi raw transaction, card number, IP, device fingerprint hoặc PII.

---

### 2.15. Bảng `marketing_campaigns`

Cấu hình chiến dịch marketing để filter Lead Queue.

```sql
CREATE TABLE marketing_campaigns (
    campaign_id             TEXT PRIMARY KEY,
    campaign_name           TEXT NOT NULL,
    description             TEXT,
    target_product_type     TEXT,                   -- 'insurance', 'credit_card', 'loan', 'saving'
    target_behavior         TEXT,                   -- VD: "travel_ratio > 0.2 AND travel_frequency > 2"
    min_lead_score          FLOAT DEFAULT 0.6,
    is_active               BOOLEAN DEFAULT TRUE,
    start_date              DATE,
    end_date                DATE,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_camp_active ON marketing_campaigns(is_active, start_date, end_date);
```

**Dữ liệu mẫu:**

| campaign_id | campaign_name | target_product_type | min_lead_score |
|---|---|---|---|
| CAMP001 | Du lịch hè 2026 | insurance | 0.70 |
| CAMP002 | Tài chính cuối năm | loan | 0.60 |
| CAMP003 | Back to school | saving | 0.65 |

---

## 3. Sơ đồ luồng dữ liệu giữa các bảng

```mermaid
flowchart LR
    classDef source fill:#1a1a2e,stroke:#16213e,color:#e0e0e0
    classDef feature fill:#0f3460,stroke:#16213e,color:#e0e0e0
    classDef fraud fill:#533483,stroke:#3a2568,color:#e0e0e0
    classDef rec fill:#1b7a4a,stroke:#145c38,color:#e0e0e0
    classDef lead fill:#b8860b,stroke:#8b6508,color:#fff
    classDef seg fill:#6c5ce7,stroke:#4834d4,color:#fff
    classDef log fill:#2c3e50,stroke:#1a252f,color:#e0e0e0

    subgraph RAW["📦 Raw Data"]
        txn[("transactions")]
    end

    subgraph FEAT["🗂️ Feature Stores"]
        uf[("user_features")]
    end

    subgraph SEG["🧩 Customer Segmentation"]
        smv[("segmentation_model_versions")]
        us[("user_segments")]
        cp[("cluster_profiles")]
        sr[("segmentation_runs")]
    end

    subgraph FRAUD["🚨 Fraud Module"]
        fa[("fraud_alerts")]
        fms[("fraud_model_scores")]
        fr[("fraud_rules")]
    end

    subgraph CATALOG["📋 Catalog"]
        pc[("product_catalog")]
    end

    subgraph LEAD["⭐ Lead Scoring"]
        ls[("lead_scores")]
        cl[("consultation_log")]
        mc[("marketing_campaigns")]
    end

    subgraph LOGS["📝 Logs"]
        rl[("recommendation_logs")]
        pl[("pitch_logs")]
    end

    txn -->|"Feature Engineering"| uf
    uf -->|"SVD + KMeans assignment"| us
    smv -->|"Active/candidate model"| us
    smv -->|"Defines cluster names"| cp
    smv -->|"Audit runs"| sr
    cp -->|"Segment context"| rl
    cp -->|"Segment context"| ls

    txn -->|"Fraud Scoring"| fa
    txn -->|"Model Scores"| fms
    fr -->|"Triggers"| fa
    
    uf -->|"Recommendation"| rl
    pc -->|"Product info"| rl
    
    uf -->|"Lead Calculation"| ls
    rl -->|"Top-3 products"| ls
    cl -->|"Contact history"| ls
    mc -->|"Campaign filter"| ls
    
    uf -->|"Consultation"| cl
    pc -->|"Product info"| cl
    
    uf -->|"Pitch generation"| pl
    pc -->|"Product info"| pl

    class txn source
    class uf feature
    class smv,us,cp,sr seg
    class fa,fms,fr fraud
    class pc rec
    class ls,cl,mc lead
    class rl,pl log
```

---

## 4. Các câu truy vấn quan trọng

### 4.1. Lấy Lead Queue (xếp hạng user ưu tiên)

```sql
SELECT 
    ls.user_id,
    ls.lead_score,
    ls.lead_tier,
    ls.product_match_score,
    ls.propensity_score,
    ls.recency_score,
    ls.customer_value_score,
    ls.fatigue_score,
    ls.days_since_last_contact,
    ls.contact_count_30d,
    pc.product_name AS top_product_name,
    pc.product_type AS top_product_type,
    ls.top_product_score
FROM lead_scores ls
LEFT JOIN product_catalog pc ON ls.top_product_id = pc.product_id
WHERE ls.eligibility_status = 'eligible'
  AND ls.lead_score >= 0.6
  AND ls.lead_tier = 'hot'
ORDER BY ls.lead_score DESC
LIMIT 50 OFFSET 0;
```

### 4.2. Lấy lịch sử tư vấn của một user

```sql
SELECT 
    cl.consultation_id,
    cl.consultation_status,
    cl.contact_channel,
    cl.contacted_at,
    cl.next_follow_up_at,
    cl.notes,
    cl.marketer_id,
    pc.product_name,
    cl.lead_score_at_time
FROM consultation_log cl
LEFT JOIN product_catalog pc ON cl.product_id = pc.product_id
WHERE cl.user_id = 'U0042'
ORDER BY cl.contacted_at DESC;
```

### 4.3. Tính contact_count_30d cho Lead Score

```sql
SELECT 
    user_id,
    COUNT(*) AS contact_count_30d
FROM consultation_log
WHERE contacted_at >= NOW() - INTERVAL '30 days'
  AND consultation_status IN ('contacted', 'interested', 'converted', 'not_interested')
GROUP BY user_id;
```

### 4.4. Tính days_since_last_contact cho Lead Score

```sql
SELECT 
    user_id,
    EXTRACT(DAY FROM (NOW() - MAX(contacted_at))) AS days_since_last_contact,
    MAX(contacted_at) AS last_contacted_at
FROM consultation_log
WHERE consultation_status IN ('contacted', 'interested', 'converted', 'not_interested')
GROUP BY user_id;
```

### 4.5. Fraud alerts đang mở (cần analyst xử lý)

```sql
SELECT 
    fa.alert_id,
    fa.user_id,
    fa.fraud_type,
    fa.severity,
    fa.fraud_score,
    fa.description,
    fa.created_at,
    t.amount,
    t.transaction_type
FROM fraud_alerts fa
LEFT JOIN transactions t ON fa.transaction_id = t.transaction_id
WHERE fa.alert_status = 'open'
ORDER BY fa.severity DESC, fa.fraud_score DESC
LIMIT 100;
```

### 4.6. Thống kê hiệu quả Lead Queue

```sql
SELECT 
    ls.lead_tier,
    COUNT(DISTINCT cl.user_id) AS contacted_users,
    COUNT(DISTINCT CASE WHEN cl.consultation_status = 'converted' THEN cl.user_id END) AS converted_users,
    ROUND(
        COUNT(DISTINCT CASE WHEN cl.consultation_status = 'converted' THEN cl.user_id END)::FLOAT 
        / NULLIF(COUNT(DISTINCT cl.user_id), 0) * 100, 1
    ) AS conversion_rate_pct
FROM lead_scores ls
LEFT JOIN consultation_log cl ON ls.user_id = cl.user_id 
    AND cl.contacted_at >= NOW() - INTERVAL '30 days'
WHERE ls.eligibility_status = 'eligible'
GROUP BY ls.lead_tier
ORDER BY ls.lead_tier;
```

### 4.7. Lấy segment active của một user

```sql
SELECT
    us.user_id,
    us.model_version,
    us.cluster_id,
    us.distance_to_centroid,
    us.assignment_mode,
    us.assigned_at,
    cp.cluster_name,
    cp.description,
    cp.top_features_json,
    cp.product_hints_json,
    cp.llm_confidence,
    cp.needs_review
FROM user_segments us
JOIN segmentation_model_versions smv
    ON us.model_version = smv.model_version
JOIN cluster_profiles cp
    ON cp.model_version = us.model_version
   AND cp.cluster_id = us.cluster_id
WHERE us.user_id = 'U0042'
  AND smv.status = 'active';
```

### 4.8. Lấy danh sách cụm của model active

```sql
SELECT
    cp.model_version,
    cp.cluster_id,
    cp.cluster_name,
    cp.description,
    cp.size,
    cp.ratio,
    cp.top_features_json,
    cp.product_hints_json,
    cp.llm_confidence,
    cp.needs_review
FROM cluster_profiles cp
JOIN segmentation_model_versions smv
    ON cp.model_version = smv.model_version
WHERE smv.status = 'active'
ORDER BY cp.cluster_id;
```

---

## 5. Chiến lược Index

| Bảng | Index | Mục đích |
|---|---|---|
| `transactions` | `(user_id, transaction_time DESC)` | Truy vấn lịch sử user |
| `transactions` | `(device_id)` | Phát hiện multi-account |
| `fraud_alerts` | `(alert_status, severity)` | Lọc alert đang mở |
| `fraud_alerts` | `(user_id, created_at DESC)` | Lịch sử fraud của user |
| `fraud_model_scores` | `(final_fraud_score DESC)` | Top giao dịch đáng ngờ |
| `lead_scores` | `(eligibility_status, lead_score DESC)` | **Lead Queue — query chính** |
| `lead_scores` | `(top_product_id, lead_score DESC)` | Lead Queue theo sản phẩm |
| `consultation_log` | `(user_id, contacted_at DESC)` | Lịch sử tư vấn |
| `consultation_log` | `(next_follow_up_at) WHERE NOT NULL` | Nhắc follow-up |
| `segmentation_model_versions` | `(status, trained_at DESC)` | Lấy active/candidate model nhanh |
| `user_segments` | `(user_id, assigned_at DESC)` | Lấy segment của một user |
| `user_segments` | `(model_version, cluster_id)` | Thống kê user theo cụm/version |
| `cluster_profiles` | `(model_version, cluster_id)` | Lấy profile cụm active |
| `segmentation_runs` | `(status, started_at DESC)` | Theo dõi job cập nhật/retrain |

---

## 6. Backup & Retention Policy

| Bảng | Retention | Backup |
|---|---|---|
| `transactions` | 5 năm (quy định tài chính) | Daily incremental + Weekly full |
| `fraud_alerts` | 2 năm | Weekly full |
| `fraud_model_scores` | 1 năm | Weekly full |
| `consultation_log` | 3 năm | Weekly full |
| `lead_scores` | Tính lại mỗi ngày (không cần backup) | — |
| `segmentation_model_versions` | Giữ toàn bộ model metadata | Weekly full |
| `user_segments` | Giữ ít nhất 6 tháng hoặc 5 active versions gần nhất | Weekly full |
| `cluster_profiles` | Giữ theo model_version | Weekly full |
| `segmentation_runs` | 1 năm | Weekly full |
| `pitch_logs` | 1 năm | Weekly full |
| `recommendation_logs` | 1 năm | Weekly full |
