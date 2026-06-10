PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    transaction_time TEXT NOT NULL,
    amount REAL NOT NULL,
    transaction_type TEXT,
    merchant_name TEXT,
    merchant_category TEXT,
    country TEXT,
    city TEXT,
    card_type TEXT,
    card_present INTEGER,
    balance_before REAL,
    balance_after REAL,
    channel TEXT,
    device_id TEXT,
    device_fingerprint TEXT,
    ip_address TEXT,
    status TEXT DEFAULT 'completed',
    is_fraud INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tx_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_tx_time ON transactions(transaction_time DESC);
CREATE INDEX IF NOT EXISTS idx_tx_user_time ON transactions(user_id, transaction_time DESC);
CREATE INDEX IF NOT EXISTS idx_tx_category ON transactions(merchant_category);
CREATE INDEX IF NOT EXISTS idx_tx_device ON transactions(device_id);
CREATE INDEX IF NOT EXISTS idx_tx_device_fp ON transactions(device_fingerprint);
CREATE INDEX IF NOT EXISTS idx_tx_status ON transactions(status);
CREATE INDEX IF NOT EXISTS idx_tx_fraud ON transactions(is_fraud);

CREATE TABLE IF NOT EXISTS user_features (
    user_id TEXT PRIMARY KEY,
    recency_days REAL,
    frequency_7d INTEGER,
    frequency_30d INTEGER,
    frequency_90d INTEGER,
    monetary_7d REAL,
    monetary_30d REAL,
    monetary_90d REAL,
    avg_transaction_amount REAL,
    max_transaction_amount REAL,
    std_transaction_amount REAL,
    shopping_ratio REAL,
    travel_ratio REAL,
    food_ratio REAL,
    education_ratio REAL,
    healthcare_ratio REAL,
    entertainment_ratio REAL,
    cashout_ratio REAL,
    transfer_ratio REAL,
    loan_payment_ratio REAL,
    income_total_30d REAL,
    expense_total_30d REAL,
    net_cashflow_30d REAL,
    negative_cashflow_days INTEGER,
    end_month_negative_cashflow_flag INTEGER,
    balance_volatility REAL,
    salary_detected_flag INTEGER,
    weekend_spending_ratio REAL,
    night_transaction_ratio REAL,
    travel_frequency_90d INTEGER,
    shopping_frequency_30d INTEGER,
    risk_score REAL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_uf_recency ON user_features(recency_days);
CREATE INDEX IF NOT EXISTS idx_uf_monetary ON user_features(monetary_30d DESC);
CREATE INDEX IF NOT EXISTS idx_uf_risk ON user_features(risk_score);

CREATE TABLE IF NOT EXISTS product_catalog (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    product_type TEXT NOT NULL,
    description TEXT,
    target_behavior TEXT,
    target_signals_json TEXT,
    eligibility_json TEXT,
    risk_allowed TEXT DEFAULT 'low',
    min_risk_score REAL DEFAULT 0.0,
    max_risk_score REAL DEFAULT 1.0,
    campaign_priority REAL DEFAULT 0.5,
    reason_template TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_prod_type ON product_catalog(product_type);
CREATE INDEX IF NOT EXISTS idx_prod_active ON product_catalog(is_active);

CREATE TABLE IF NOT EXISTS fraud_alerts (
    alert_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    transaction_id TEXT,
    fraud_type TEXT,
    fraud_score REAL NOT NULL,
    severity TEXT NOT NULL,
    description TEXT,
    evidence TEXT,
    alert_status TEXT DEFAULT 'open',
    reviewed_by TEXT,
    reviewed_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fa_user ON fraud_alerts(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_fa_status ON fraud_alerts(alert_status, severity);
CREATE INDEX IF NOT EXISTS idx_fa_score ON fraud_alerts(fraud_score DESC);
CREATE INDEX IF NOT EXISTS idx_fa_created ON fraud_alerts(created_at DESC);

CREATE TABLE IF NOT EXISTS fraud_model_scores (
    score_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    transaction_id TEXT,
    xgboost_score REAL NOT NULL,
    final_fraud_score REAL NOT NULL,
    decision_threshold REAL DEFAULT 0.5,
    predicted_fraud INTEGER,
    shap_values TEXT,
    features_used TEXT,
    model_version TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fms_user ON fraud_model_scores(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_fms_tx ON fraud_model_scores(transaction_id);
CREATE INDEX IF NOT EXISTS idx_fms_score ON fraud_model_scores(final_fraud_score DESC);

CREATE TABLE IF NOT EXISTS fraud_rules (
    rule_id TEXT PRIMARY KEY,
    rule_name TEXT NOT NULL,
    rule_type TEXT NOT NULL,
    condition TEXT,
    threshold REAL,
    severity TEXT DEFAULT 'medium',
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recommendation_logs (
    log_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    score REAL,
    score_breakdown_json TEXT,
    reason_json TEXT,
    fraud_score REAL,
    risk_score REAL,
    model_version TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_rec_user ON recommendation_logs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_rec_product ON recommendation_logs(product_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_rec_score ON recommendation_logs(score DESC);

CREATE TABLE IF NOT EXISTS pitch_logs (
    pitch_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    product_id TEXT,
    prompt TEXT,
    generated_script TEXT,
    llm_model TEXT,
    tokens_used INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS consultation_log (
    consultation_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    marketer_id TEXT,
    product_id TEXT,
    top_3_products TEXT,
    lead_score_at_time REAL,
    pitch_script_used TEXT,
    consultation_status TEXT,
    contact_channel TEXT,
    notes TEXT,
    contacted_at TEXT,
    next_follow_up_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cl_user ON consultation_log(user_id, contacted_at DESC);
CREATE INDEX IF NOT EXISTS idx_cl_status ON consultation_log(consultation_status, contacted_at DESC);
CREATE INDEX IF NOT EXISTS idx_cl_followup ON consultation_log(next_follow_up_at);

CREATE TABLE IF NOT EXISTS lead_scores (
    user_id TEXT PRIMARY KEY,
    lead_score REAL NOT NULL,
    lead_tier TEXT,
    top_product_id TEXT,
    top_product_score REAL,
    product_match_score REAL,
    propensity_score REAL,
    recency_score REAL,
    customer_value_score REAL,
    fatigue_score REAL,
    days_since_last_contact INTEGER,
    contact_count_30d INTEGER DEFAULT 0,
    last_contact_status TEXT,
    eligibility_status TEXT DEFAULT 'eligible',
    calculated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ls_score ON lead_scores(lead_score DESC);
CREATE INDEX IF NOT EXISTS idx_ls_tier ON lead_scores(lead_tier, lead_score DESC);
CREATE INDEX IF NOT EXISTS idx_ls_eligibility ON lead_scores(eligibility_status, lead_score DESC);
CREATE INDEX IF NOT EXISTS idx_ls_product ON lead_scores(top_product_id, lead_score DESC);
CREATE INDEX IF NOT EXISTS idx_ls_calculated ON lead_scores(calculated_at DESC);

CREATE TABLE IF NOT EXISTS segmentation_model_versions (
    model_version TEXT PRIMARY KEY,
    n_components INTEGER NOT NULL,
    k INTEGER NOT NULL,
    scaler_path TEXT NOT NULL,
    svd_path TEXT NOT NULL,
    kmeans_path TEXT NOT NULL,
    feature_schema TEXT NOT NULL,
    metrics_json TEXT,
    selection_policy TEXT,
    status TEXT DEFAULT 'candidate',
    trained_at TEXT DEFAULT CURRENT_TIMESTAMP,
    activated_at TEXT,
    created_by TEXT
);

CREATE INDEX IF NOT EXISTS idx_seg_model_status ON segmentation_model_versions(status, trained_at DESC);

CREATE TABLE IF NOT EXISTS user_segments (
    user_id TEXT NOT NULL,
    model_version TEXT NOT NULL,
    cluster_id INTEGER NOT NULL,
    distance_to_centroid REAL,
    assignment_mode TEXT DEFAULT 'predict',
    assigned_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, model_version)
);

CREATE INDEX IF NOT EXISTS idx_user_segments_user ON user_segments(user_id, assigned_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_segments_cluster ON user_segments(model_version, cluster_id);

CREATE TABLE IF NOT EXISTS cluster_profiles (
    model_version TEXT NOT NULL,
    cluster_id INTEGER NOT NULL,
    cluster_name TEXT NOT NULL,
    description TEXT,
    size INTEGER,
    ratio REAL,
    top_features_json TEXT,
    product_hints_json TEXT,
    centroid_json TEXT,
    previous_cluster_id INTEGER,
    previous_similarity REAL,
    llm_model TEXT,
    llm_confidence REAL,
    needs_review INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (model_version, cluster_id)
);

CREATE INDEX IF NOT EXISTS idx_cluster_profiles_version ON cluster_profiles(model_version, cluster_id);
CREATE INDEX IF NOT EXISTS idx_cluster_profiles_review ON cluster_profiles(needs_review, created_at DESC);

CREATE TABLE IF NOT EXISTS segmentation_runs (
    run_id TEXT PRIMARY KEY,
    model_version TEXT,
    mode TEXT NOT NULL,
    status TEXT NOT NULL,
    triggered_by TEXT,
    users_processed INTEGER DEFAULT 0,
    changed_users_count INTEGER DEFAULT 0,
    duration_seconds REAL,
    metrics_json TEXT,
    error_message TEXT,
    started_at TEXT DEFAULT CURRENT_TIMESTAMP,
    finished_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_seg_runs_status ON segmentation_runs(status, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_seg_runs_mode ON segmentation_runs(mode, started_at DESC);

CREATE TABLE IF NOT EXISTS marketing_campaigns (
    campaign_id TEXT PRIMARY KEY,
    campaign_name TEXT NOT NULL,
    description TEXT,
    target_product_type TEXT,
    target_behavior TEXT,
    min_lead_score REAL DEFAULT 0.6,
    is_active INTEGER DEFAULT 1,
    start_date TEXT,
    end_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_camp_active ON marketing_campaigns(is_active, start_date, end_date);
