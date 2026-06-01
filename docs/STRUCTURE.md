# Kiến trúc hệ thống — AI Phân tích Giao dịch Toàn diện

> **Phát hiện Gian lận, Dự báo Rủi ro Tín dụng và Khuyến nghị Sản phẩm Tài chính Cá nhân hóa**

---

## 1. Sơ đồ kiến trúc tổng thể (High-Level Architecture)

```mermaid
flowchart TB
    %% ── Styles ──
    classDef datasource fill:#1a1a2e,stroke:#16213e,color:#e0e0e0
    classDef datalayer fill:#0f3460,stroke:#16213e,color:#e0e0e0
    classDef fraudlayer fill:#533483,stroke:#3a2568,color:#e0e0e0
    classDef reclayer fill:#1b7a4a,stroke:#145c38,color:#e0e0e0
    classDef leadlayer fill:#b8860b,stroke:#8b6508,color:#fff
    classDef llmlayer fill:#c0392b,stroke:#922b21,color:#e0e0e0
    classDef agentlayer fill:#2c3e50,stroke:#1a252f,color:#e0e0e0
    classDef apilayer fill:#2471a3,stroke:#1a5276,color:#e0e0e0
    classDef dashboard fill:#1a1a2e,stroke:#16213e,color:#e0e0e0
    classDef db fill:#34495e,stroke:#2c3e50,color:#e0e0e0
    classDef decision fill:#e67e22,stroke:#d35400,color:#fff
    classDef block fill:#c0392b,stroke:#922b21,color:#fff

    %% ── Data Sources ──
    subgraph DATA_SRC["📦 DATA SOURCES"]
        direction TB
        raw_db[("🗄️ Raw Transaction DB<br/>(transaction_id, user_id,<br/>amount, merchant_category,<br/>device_id, ip_address, ...)")]
    end

    %% ── Layer 1: Data Preparation ──
    subgraph L1["🔧 LAYER 1 — Data Preparation"]
        direction TB
        cleaning["🧹 Data Cleaning<br/><i>Drop duplicates, normalize<br/>categories, handle missing</i>"]
        feat_eng["⚙️ Feature Engineering<br/><i>RFM + Category Ratio<br/>+ Cashflow + Cycle</i>"]
        fraud_feat["⚙️ Fraud Feature Engineering<br/><i>Velocity + Behavioral Deviation<br/>+ Device/Channel + Graph</i>"]

        cleaning --> feat_eng
        cleaning --> fraud_feat
    end

    %% ── Feature Stores ──
    subgraph FEAT_STORE["🗂️ FEATURE STORES"]
        direction LR
        user_feat[("📊 User-Feature<br/>Matrix")]
        fraud_feat_store[("🔴 Fraud-Feature<br/>Matrix")]
    end

    feat_eng --> user_feat
    fraud_feat --> fraud_feat_store

    %% ── Layer 2: Fraud Detection ──
    subgraph L2["🚨 LAYER 2 — Fraud Detection Engine"]
        direction TB
        rule_fraud["📏 Rule-based Filter<br/><i>7 Hard Rules<br/>(Amount Spike, Velocity,<br/>Device Change, Fast Cash-out,<br/>Many-to-One, Circular...)</i>"]
        iso_forest["🌲 Isolation Forest<br/><i>Unsupervised Anomaly<br/>Detection</i>"]
        xgboost["🚀 XGBoost Classifier<br/><i>Supervised Fraud<br/>Classification + SMOTE</i>"]
        shap["🔍 SHAP Explainer<br/><i>Explainable AI —<br/>Top Contributing Features</i>"]
        decision["⚡ Final Decision Engine<br/><i>Weighted Ensemble<br/>(Rule + IF + XGBoost)</i>"]

        rule_fraud --> decision
        iso_forest --> decision
        xgboost --> decision
        decision --> shap
    end

    fraud_feat_store --> rule_fraud
    fraud_feat_store --> iso_forest
    fraud_feat_store --> xgboost

    %% ── Decision Gate ──
    decision_gate{"🛑 FRAUD GATE<br/>fraud_score?"}
    decision --> decision_gate

    %% ── Layer 3: Recommendation ──
    subgraph L3["🎯 LAYER 3 — Recommendation Engine"]
        direction TB
        rec_rule["📐 Rule-based Scorer<br/><i>Score từng product<br/>theo behavior</i>"]
        rec_filter["🔎 Fraud + Risk Filter<br/><i>Loại sản phẩm rủi ro cao<br/>nếu fraud_score > 0.3</i>"]
        top3["🏆 Top-3 Products<br/><i>+ Reason + Score</i>"]

        rec_rule --> rec_filter --> top3
    end

    user_feat --> rec_rule
    decision_gate -- "fraud < 0.7" --> rec_filter
    decision_gate -- "fraud ≥ 0.7" --> block_rec["🚫 BLOCK<br/>Không gợi ý<br/>sản phẩm"]

    %% ── Layer 3.5: Lead Scoring ──
    subgraph L35["⭐ LAYER 3.5 — Lead Scoring & Prioritization"]
        direction TB
        lead_calc["📊 Lead Score Calculator<br/><i>5 Components Weighted<br/>ProductMatch + Propensity<br/>+ Recency + Value − Fatigue</i>"]
        lead_queue["📋 Lead Queue Builder<br/><i>Sort + Filter + Paginate<br/>Hot / Warm / Cold Tiers</i>"]
        campaign["📢 Campaign Filter<br/><i>product_type, tier,<br/>min_lead_score</i>"]

        lead_calc --> lead_queue
        campaign --> lead_queue
    end

    top3 --> lead_calc
    user_feat --> lead_calc

    %% ── Layer 4: Agent Orchestration ──
    subgraph L4["🤖 LAYER 4 — Agentic Orchestration (LangGraph)"]
        direction TB
        data_agent["📡 Data Agent<br/><i>Fetch user profile<br/>+ transaction history</i>"]
        fraud_agent["🚨 Fraud Detection Agent<br/><i>Score + Flag + SHAP</i>"]
        rec_agent["🎯 Recommendation Agent<br/><i>Top-3 + Reason</i>"]
        lead_agent["⭐ Lead Score Agent<br/><i>Calculate + Update<br/>lead_score</i>"]
        pitch_agent["💬 Pitching Agent<br/><i>Generate script<br/>via Deepseek/Gemini</i>"]
        format_agent["📝 Response Formatter<br/><i>Normalize JSON<br/>for Frontend</i>"]

        data_agent --> fraud_agent
        fraud_agent --> rec_agent
        rec_agent --> lead_agent
        lead_agent --> pitch_agent
        pitch_agent --> format_agent
    end

    decision_gate -- "fraud < 0.3" --> pitch_agent
    decision_gate -- "fraud ≥ 0.3" --> format_agent

    %% ── Layer 5: LLM ──
    subgraph L5["🧠 LAYER 5 — LLM Pitching Bot"]
        direction TB
        guardrail["🛡️ Safety Guardrail<br/><i>Fraud check + content filter<br/>No sensitive info</i>"]
        prompt["📝 Prompt Template<br/><i>Customer insights<br/>+ Product + Reason</i>"]
        llm_api[("🌐 Deepseek / Gemini API<br/><i>80-120 words<br/>Natural + Professional</i>")]
        fallback["🔄 Fallback Template<br/><i>Rule-based script<br/>if LLM timeout</i>"]

        guardrail --> prompt
        prompt --> llm_api
        llm_api -- "timeout" --> fallback
    end

    pitch_agent --> guardrail

    %% ── Layer 6: API ──
    subgraph L6["🔌 LAYER 6 — FastAPI Backend"]
        direction LR
        api_fraud["POST /fraud/score"]
        api_rec["GET /recommendations/{user_id}"]
        api_lead["GET /recommendations/lead-queue"]
        api_mark["POST /recommendations/mark-consulted"]
        api_pitch["POST /users/{user_id}/generate-pitch"]
        api_feedback["POST /fraud/feedback"]
    end

    decision --> api_fraud
    top3 --> api_rec
    lead_queue --> api_lead
    lead_queue --> api_mark
    format_agent --> api_pitch
    format_agent --> api_feedback

    %% ── Databases ──
    subgraph DATABASES["💾 DATABASES (PostgreSQL + Redis Cache)"]
        direction LR
        db_txn[("transactions")]
        db_user[("user_features")]
        db_fraud[("fraud_alerts<br/>fraud_model_scores")]
        db_prod[("product_catalog")]
        db_consult[("consultation_log<br/>lead_scores<br/>marketing_campaigns")]
        db_pitch[("pitch_logs<br/>recommendation_logs")]
        cache[("⚡ Redis Cache<br/>(real-time velocity<br/>features)")]
    end

    raw_db --> db_txn
    user_feat --> db_user
    decision --> db_fraud
    top3 --> db_prod
    lead_queue --> db_consult
    llm_api --> db_pitch
    fraud_feat_store --> cache

    %% ── Dashboard ──
    subgraph DASH["🖥️ DASHBOARD (Streamlit / React)"]
        direction LR
        subgraph TAB1["🚨 Tab: Fraud Detection"]
            direction TB
            gauge["⭕ Fraud Score Gauge<br/><i>Green / Yellow / Red</i>"]
            alerts_panel["🔔 Fraud Alerts Panel<br/><i>severity-coded list</i>"]
            shap_chart["📊 SHAP Waterfall Chart<br/><i>Feature contribution</i>"]
            timeline["📅 Suspicious TX Timeline"]
            confirm_btn["✅ Confirm Fraud / ❌ False Positive"]
        end

        subgraph TAB2["🎯 Tab: Recommendation"]
            direction TB
            lead_table["📋 Lead Queue Table<br/><i>Ranked by Lead Score</i>"]
            campaign_filter["🔽 Campaign / Product Filter"]
            insights["💡 Customer Insights<br/><i>Spending chart + Risk</i>"]
            top3_card["🏆 Top-3 Products Card<br/><i>+ Score + Reason</i>"]
            pitch_btn["🎤 Generate Pitch Button"]
            mark_btn["✔️ Mark as Consulted<br/><i>interested / not / converted</i>"]
        end
    end

    api_fraud --> gauge
    api_fraud --> alerts_panel
    api_fraud --> shap_chart
    api_fraud --> timeline
    api_feedback --> confirm_btn
    api_lead --> lead_table
    api_lead --> campaign_filter
    api_rec --> insights
    api_rec --> top3_card
    api_pitch --> pitch_btn
    api_mark --> mark_btn

    %% ── Users ──
    fraud_analyst["👨‍💻 Fraud Analyst<br/><i>Review alerts,<br/>confirm/false-positive</i>"]
    marketer["👩‍💼 Marketer / Telesales<br/><i>View Lead Queue,<br/>call customers,<br/>mark consulted</i>"]

    fraud_analyst --> TAB1
    marketer --> TAB2

    %% ── Apply styles ──
    class raw_db datasource
    class cleaning,feat_eng,fraud_feat datalayer
    class user_feat,fraud_feat_store db
    class rule_fraud,iso_forest,xgboost,shap,decision fraudlayer
    class rec_rule,rec_filter,top3 reclayer
    class lead_calc,lead_queue,campaign leadlayer
    class guardrail,prompt,llm_api,fallback llmlayer
    class data_agent,fraud_agent,rec_agent,lead_agent,pitch_agent,format_agent agentlayer
    class api_fraud,api_rec,api_lead,api_mark,api_pitch,api_feedback apilayer
    class decision_gate decision
    class block_rec block
    class db_txn,db_user,db_fraud,db_prod,db_consult,db_pitch,cache db
    class TAB1,TAB2 dashboard
```

---

## 2. Sơ đồ luồng dữ liệu (Data Flow)

### 2.1. Luồng Fraud Detection (Real-time)

```mermaid
sequenceDiagram
    actor A as 👨‍💻 Fraud Analyst
    participant D as 🖥️ Dashboard
    participant FR as 🚨 Fraud Engine
    participant C as ⚡ Redis
    participant DB as 💾 PostgreSQL

    rect rgb(83, 52, 131, 0.15)
        Note over A,DB: 🚨 FLOW 1 — Real-time Fraud Detection
        DB->>FR: New transaction arrives
        FR->>C: Get velocity features (cached)
        FR->>FR: Rule-based check (< 5ms)
        FR->>FR: Isolation Forest (< 10ms)
        FR->>FR: XGBoost classify (< 10ms)
        FR->>FR: SHAP explain (< 50ms)
        FR->>FR: Final Decision (weighted ensemble)
        FR->>DB: Save fraud_alerts + fraud_model_scores
        FR->>D: Push alert to dashboard (WebSocket)
        D->>A: Show fraud alert ❌ + SHAP chart
        A->>D: Confirm fraud / False positive
        D->>DB: Update alert_status
    end
```

### 2.2. Luồng Recommendation + Lead Queue + Pitching

```mermaid
sequenceDiagram
    actor M as 👩‍💼 Marketer
    participant D as 🖥️ Dashboard
    participant API as 🔌 FastAPI
    participant AG as 🤖 LangGraph Agents
    participant FR as 🚨 Fraud Engine
    participant RC as 🎯 Recommender
    participant LS as ⭐ Lead Scorer
    participant LLM as 🧠 Deepseek/Gemini
    participant DB as 💾 PostgreSQL

    rect rgb(184, 134, 11, 0.15)
        Note over M,DB: ⭐ FLOW 2 — Lead Queue
        M->>D: Open Tab Recommendation
        D->>API: GET /recommendations/lead-queue?tier=hot_leads
        API->>DB: Query lead_scores (sorted DESC)
        API->>DB: JOIN consultation_log (contact status)
        DB->>API: Return ranked user list
        API->>D: Lead Queue (ranked by lead_score)
        D->>M: Display: Rank, User, Score, Top Product
    end

    rect rgb(27, 122, 74, 0.15)
        Note over M,LLM: 🎯 FLOW 3 — Recommendation + Pitch
        M->>D: Click user U0042 (lead_score=0.94)
        D->>API: GET /users/U0042/recommendations
        API->>AG: Trigger LangGraph workflow
        AG->>FR: Fraud check user
        FR->>AG: fraud_score=0.12 ✅ PASS
        AG->>RC: Get recommendations
        RC->>AG: Top-3 products + reasons
        AG->>LS: Calculate lead_score
        LS->>AG: lead_score=0.94 (breakdown)
        AG->>D: Return insights + top-3 + lead_score
        D->>M: Show customer insights + products
    end

    rect rgb(192, 57, 43, 0.15)
        Note over M,LLM: 💬 FLOW 4 — LLM Pitch Generation
        M->>D: Click [Tạo kịch bản tư vấn]
        D->>API: POST /users/U0042/generate-pitch
        API->>AG: Pitching Agent
        AG->>AG: Guardrail: fraud_score OK? ✅
        AG->>LLM: Prompt + insights + product
        LLM->>AG: Generated script
        AG->>DB: Save to pitch_logs
        AG->>D: Return script
        D->>M: Display: "Dạ em chào anh/chị..."
    end

    rect rgb(46, 204, 113, 0.15)
        Note over M,DB: ✔️ FLOW 5 — Mark Consultation
        M->>D: After call, click [Đánh dấu đã tư vấn]
        M->>D: Select status: "interested"
        D->>API: POST /recommendations/mark-consulted
        API->>DB: INSERT consultation_log
        API->>LS: Recalculate lead_score
        LS->>DB: UPDATE lead_scores (new score: 0.34)
        API->>D: Success ✅ + new lead_score
        D->>M: Show next user in queue ⟶
    end
```

---

## 3. Sơ đồ Fraud Detection (Chi tiết)

```mermaid
flowchart TB
    classDef rule fill:#2ecc71,stroke:#27ae60,color:#fff
    classDef ml fill:#3498db,stroke:#2980b9,color:#fff
    classDef ensemble fill:#9b59b6,stroke:#8e44ad,color:#fff
    classDef explain fill:#e67e22,stroke:#d35400,color:#fff
    classDef output fill:#e74c3c,stroke:#c0392b,color:#fff
    classDef block fill:#c0392b,stroke:#922b21,color:#fff

    tx["🔄 New Transaction"] --> extract["⚙️ Feature Extraction<br/><i>Velocity + Behavioral +<br/>Device + Sequence</i>"]
    extract --> rule_check

    subgraph RULE["📏 LAYER 1 — Rule-based (MVP)"]
        rule_check["Evaluate 7 Rules"]
        r1["Rule 1: Amount Spike"]
        r2["Rule 2: Velocity Check"]
        r3["Rule 3: Device Change"]
        r4["Rule 4: Night Large TX"]
        r5["Rule 5: Fast Cash-out"]
        r6["Rule 6: Many-to-One"]
        r7["Rule 7: Circular TX"]

        rule_check --> r1 & r2 & r3 & r4 & r5 & r6 & r7
        r1 & r2 & r3 & r4 & r5 & r6 & r7 --> rule_score["Rule Score<br/>(0.1 / 0.6 / 0.9)"]
    end

    subgraph IF["🌲 LAYER 2 — Isolation Forest (Unsupervised)"]
        if_model["Isolation Forest<br/>200 trees, contamination=0.01"]
        if_model --> anomaly_score["Anomaly Score<br/>(normalized 0-1)"]
    end

    subgraph XGB["🚀 LAYER 3 — XGBoost (Supervised)"]
        xgb_model["XGBoost Classifier<br/>300 trees, max_depth=6<br/>+ SMOTE oversampling"]
        xgb_model --> fraud_prob["Fraud Probability<br/>(0-1)"]
    end

    extract --> if_model
    extract --> xgb_model

    subgraph ENSEMBLE["⚡ FINAL DECISION ENGINE"]
        rule_score --> ensemble_calc["Weighted Ensemble<br/>0.2 × Rule + 0.3 × IF + 0.5 × XGB"]
        anomaly_score --> ensemble_calc
        fraud_prob --> ensemble_calc
        ensemble_calc --> final_score{"fraud_score?"}
    end

    final_score -- "< 0.3" --> pass["✅ PASS<br/>Normal transaction"]
    final_score -- "0.3 - 0.7" --> review["⚠️ REVIEW<br/>Manual check needed"]
    final_score -- "> 0.7" --> flag["🚫 FLAG<br/>Block + Alert"]

    subgraph EXPLAIN["🔍 SHAP EXPLAINABILITY"]
        shap_calc["SHAP TreeExplainer"]
        shap_output["Top Contributing Features<br/>amount_zscore: +0.35<br/>device_change: +0.28<br/>tx_count_1h: +0.22"]
    end

    flag --> shap_calc
    shap_calc --> shap_output

    class r1,r2,r3,r4,r5,r6,r7,rule_check,rule_score rule
    class if_model,anomaly_score ml
    class xgb_model,fraud_prob ml
    class ensemble_calc,final_score ensemble
    class shap_calc,shap_output explain
    class pass,review,flag output
```

---

## 4. Sơ đồ Recommendation + Lead Scoring (Chi tiết)

```mermaid
flowchart TB
    classDef rec fill:#1b7a4a,stroke:#145c38,color:#e0e0e0
    classDef lead fill:#b8860b,stroke:#8b6508,color:#fff
    classDef filter fill:#2471a3,stroke:#1a5276,color:#e0e0e0
    classDef output fill:#2ecc71,stroke:#27ae60,color:#fff

    user[("👤 User Profile<br/>+ Features")] --> fraud_check{"🛑 Fraud<br/>Check"}

    fraud_check -- "fraud ≥ 0.7" --> blocked["🚫 BLOCKED<br/>No recommendation"]
    fraud_check -- "fraud < 0.7" --> risk_filter{"🔎 Risk<br/>Filter"}

    risk_filter -- "fraud 0.3-0.7" --> low_risk["⚠️ Low-risk only<br/>Saving + Insurance"]
    risk_filter -- "fraud < 0.3" --> all["✅ All products"]

    low_risk --> scorer
    all --> scorer

    subgraph REC["🎯 RECOMMENDATION ENGINE"]
        scorer["📐 Rule-based Scorer"]
        p1["Thẻ tín dụng hoàn tiền<br/>0.4×shopping + 0.2×freq + ..."]
        p2["Bảo hiểm du lịch<br/>0.5×travel + 0.3×flight + ..."]
        p3["Vay tiêu dùng<br/>0.4×cashflow + 0.3×balance + ..."]
        p4["Vay thấu chi<br/>0.5×end_month + 0.3×volatility + ..."]
        p5["Tiết kiệm linh hoạt<br/>0.6×positive_cf + 0.4×balance + ..."]
        p6["Bảo hiểm sức khỏe<br/>0.5×healthcare + 0.3×medical + ..."]

        scorer --> p1 & p2 & p3 & p4 & p5 & p6
        p1 & p2 & p3 & p4 & p5 & p6 --> rank["🏆 Rank + Filter<br/>Top-3 Products"]
    end

    rank --> top3_out["Top-3 + Score + Reason"]

    subgraph LEAD["⭐ LEAD SCORING ENGINE"]
        top3_out --> l1["Product Match Score<br/>(max top-3 score)"]
        user --> l2["Propensity Score<br/>(need signals)"]
        user --> l3["Recency Boost<br/>(days since last contact)"]
        user --> l4["Customer Value<br/>(monetary percentile)"]
        user --> l5["Fatigue Penalty<br/>(contact frequency)"]

        l1 & l2 & l3 & l4 & l5 --> lead_calc["LEAD_SCORE =<br/>0.30×Match + 0.25×Propensity<br/>+ 0.20×Recency + 0.15×Value<br/>− 0.10×Fatigue"]
    end

    lead_calc --> tier{"Lead Tier?"}
    tier -- "> 0.85" --> hot["🔥 Hot Lead"]
    tier -- "0.6 - 0.85" --> warm["🟡 Warm Lead"]
    tier -- "< 0.6" --> cold["🔵 Cold Lead"]

    hot & warm & cold --> queue["📋 LEAD QUEUE<br/>Sorted by lead_score DESC"]

    class scorer,p1,p2,p3,p4,p5,p6,rank,top3_out rec
    class l1,l2,l3,l4,l5,lead_calc,tier,hot,warm,cold,queue lead
    class fraud_check,risk_filter,low_risk,all filter
    class blocked output
```

---

## 5. Sơ đồ triển khai (Deployment)

```mermaid
flowchart LR
    classDef container fill:#1a1a2e,stroke:#16213e,color:#e0e0e0
    classDef service fill:#0f3460,stroke:#16213e,color:#e0e0e0
    classDef external fill:#c0392b,stroke:#922b21,color:#e0e0e0
    classDef volume fill:#34495e,stroke:#2c3e50,color:#e0e0e0

    subgraph DOCKER["🐳 Docker Compose Environment"]
        direction TB

        subgraph FRONTEND["🖥️ Frontend (Port 8501/3000)"]
            streamlit["Streamlit / React<br/>2-Tab Dashboard"]
        end

        subgraph BACKEND["🔌 Backend (Port 8000)"]
            fastapi["FastAPI<br/>REST API + WebSocket"]
            swagger["Swagger UI<br/>Auto-generated docs"]
        end

        subgraph MODELS["🧠 Model Services"]
            fraud_svc["Fraud Detection<br/>Service<br/>(scikit-learn + XGBoost)"]
            rec_svc["Recommendation<br/>Service<br/>(scikit-learn / PyTorch)"]
            lead_svc["Lead Scoring<br/>Service<br/>(Custom Python)"]
            pitch_svc["LLM Pitching<br/>Service<br/>(Deepseek/Gemini client)"]
        end

        subgraph AGENTS["🤖 Agent Orchestration"]
            langgraph["LangGraph<br/>Workflow Engine"]
        end

        subgraph DATA["💾 Data Layer"]
            postgres[("PostgreSQL 15<br/>Port 5432")]
            redis[("Redis 7<br/>Port 6379")]
            pg_vol[("📁 pg_data<br/>Persistent Volume")]
            redis_vol[("📁 redis_data<br/>Persistent Volume")]
        end
    end

    subgraph EXTERNAL["🌐 External APIs"]
        deepseek["Deepseek API<br/>deepseek-chat"]
        gemini["Google Gemini API<br/>gemini-1.5-flash"]
    end

    %% Connections
    streamlit <--> fastapi
    fastapi <--> swagger
    fastapi --> fraud_svc
    fastapi --> rec_svc
    fastapi --> lead_svc
    fastapi --> pitch_svc
    fastapi --> langgraph

    fraud_svc --> postgres
    fraud_svc --> redis
    rec_svc --> postgres
    lead_svc --> postgres
    pitch_svc --> postgres
    langgraph --> fraud_svc
    langgraph --> rec_svc
    langgraph --> lead_svc
    langgraph --> pitch_svc

    pitch_svc --> deepseek
    pitch_svc --> gemini

    postgres --> pg_vol
    redis --> redis_vol

    class streamlit,fastapi,swagger container
    class fraud_svc,rec_svc,lead_svc,pitch_svc,langgraph service
    class deepseek,gemini external
    class postgres,redis,pg_vol,redis_vol volume
```

---

## 6. Quy trình làm việc của Marketer (Marketer Workflow)

```mermaid
flowchart TB
    classDef start fill:#1a1a2e,stroke:#16213e,color:#e0e0e0
    classDef lead fill:#b8860b,stroke:#8b6508,color:#fff
    classDef rec fill:#1b7a4a,stroke:#145c38,color:#e0e0e0
    classDef decision fill:#e67e22,stroke:#d35400,color:#fff
    classDef llm fill:#c0392b,stroke:#922b21,color:#e0e0e0
    classDef action fill:#2ecc71,stroke:#27ae60,color:#fff
    classDef result fill:#3498db,stroke:#2980b9,color:#fff
    classDef negative fill:#e74c3c,stroke:#c0392b,color:#fff
    classDef update fill:#9b59b6,stroke:#8e44ad,color:#fff

    start_node["👩‍💼 Marketer opens Dashboard<br/>→ Tab Recommendation"]
    queue["📋 View Lead Queue<br/><i>Users ranked by lead_score</i>"]
    filter["🔽 Optional: Filter by<br/><i>Campaign / Product Type / Tier</i>"]
    select["👆 Click top user<br/><i>highest lead_score</i>"]
    insights["💡 View:<br/>• Customer Insights<br/>• Top-3 Products + Reason<br/>• Lead Score Breakdown<br/>• Consultation History"]
    pitch_q{"🎤 Generate<br/>Pitch?"}
    script["📝 LLM generates<br/>personalized script<br/><i>80-120 words</i>"]
    call_node["📞 Marketer calls<br/>customer using script"]
    result_q{"📊 Call<br/>Result?"}
    interested["✅ Interested<br/>→ Set follow-up"]
    converted["🎉 Converted!<br/>→ Sale closed"]
    not_interested["❌ Not Interested<br/>→ Skip 30 days"]
    no_answer["📵 No Answer<br/>→ Retry in 3 days"]
    mark["✔️ Click Mark Consulted<br/>→ Status + Notes saved"]
    update_score["🔄 Lead Score auto-updates<br/>→ User drops in queue"]
    next_user["➡️ Next user in queue<br/>appears automatically"]

    start_node --> queue
    queue --> filter
    filter --> select
    queue --> select
    select --> insights
    insights --> pitch_q
    pitch_q -->|Yes| script
    pitch_q -->|Skip, call directly| call_node
    script --> call_node
    call_node --> result_q
    result_q --> interested
    result_q --> converted
    result_q --> not_interested
    result_q --> no_answer
    interested --> mark
    converted --> mark
    not_interested --> mark
    no_answer --> mark
    mark --> update_score
    update_score --> next_user
    next_user -.->|back to queue| select

    class start_node start
    class queue,filter lead
    class select,insights rec
    class pitch_q,result_q decision
    class script llm
    class call_node,mark action
    class interested,converted result
    class not_interested,no_answer negative
    class update_score,next_user update
```

---

## 7. Cấu trúc thư mục dự án

```text
ai-transaction-analyzer/
│
├── data/
│   ├── raw/                          # Dữ liệu giao dịch thô
│   ├── processed/                    # Dữ liệu đã làm sạch
│   ├── product_catalog.csv           # Danh mục sản phẩm tài chính
│   └── fraud_labels.csv              # Label gian lận (nếu có)
│
├── notebooks/
│   ├── 01_eda.ipynb                  # Exploratory Data Analysis
│   ├── 02_feature_engineering.ipynb  # Feature engineering
│   ├── 03_model_experiment.ipynb     # Thử nghiệm model
│   └── 04_fraud_detection.ipynb      # Fraud detection analysis
│
├── src/
│   ├── data/
│   │   ├── cleaning.py               # Làm sạch & chuẩn hóa dữ liệu
│   │   └── feature_engineering.py    # Feature engineering chung
│   │
│   ├── fraud/                        # 🚨 Fraud Detection Module
│   │   ├── feature_engineering.py    # Fraud-specific features
│   │   ├── rule_based.py             # Rule-based fraud detector (7 rules)
│   │   ├── model.py                  # ML models (Isolation Forest, XGBoost)
│   │   ├── scoring.py                # Real-time scoring pipeline
│   │   ├── explainer.py              # SHAP-based explainability
│   │   └── service.py                # Fraud detection service
│   │
│   ├── recommender/                  # 🎯 Recommendation Module
│   │   ├── rule_based.py             # Rule-based recommender
│   │   ├── model.py                  # ML ranking model
│   │   └── service.py                # Recommendation service
│   │
│   ├── lead_scoring/                 # ⭐ Lead Scoring Module
│   │   ├── lead_score.py             # Lead Score calculation (5 components)
│   │   ├── propensity.py             # Propensity score estimation
│   │   ├── lead_queue.py             # Lead Queue builder + filter + sort
│   │   └── campaign.py               # Campaign configuration & targeting
│   │
│   ├── risk/
│   │   └── risk_scoring.py           # Credit risk scoring
│   │
│   ├── llm/                          # 🧠 LLM Module
│   │   ├── prompt_template.py        # Prompt templates
│   │   └── llm_service.py            # Deepseek/Gemini API client
│   │
│   ├── agents/                       # 🤖 Agent Orchestration
│   │   ├── graph.py                  # LangGraph workflow definition
│   │   ├── data_agent.py             # Data fetching agent
│   │   ├── fraud_agent.py            # Fraud detection agent
│   │   ├── recommendation_agent.py   # Recommendation agent
│   │   ├── lead_score_agent.py       # Lead scoring agent
│   │   ├── lead_queue_agent.py       # Lead queue agent
│   │   └── pitching_agent.py         # LLM pitching agent
│   │
│   └── api/                          # 🔌 FastAPI Backend
│       ├── main.py                   # App entry point
│       ├── routes.py                 # API route definitions
│       ├── fraud_routes.py           # Fraud detection endpoints
│       ├── lead_routes.py            # Lead Queue + mark-consulted endpoints
│       └── schemas.py                # Pydantic models / request-response schemas
│
├── dashboard/
│   └── app.py                        # 🖥️ Streamlit/React dashboard (2 tabs)
│
├── tests/
│   ├── test_features.py              # Unit test: feature engineering
│   ├── test_fraud.py                 # Unit test: fraud detection
│   ├── test_recommender.py           # Unit test: recommendation
│   ├── test_lead_scoring.py          # Unit test: lead scoring
│   └── test_api.py                   # Integration test: API endpoints
│
├── models/                           # 💾 Saved models
│   ├── isolation_forest.pkl
│   ├── xgboost_fraud.json
│   └── recommender.pkl
│
├── configs/                          # ⚙️ Configuration files
│   ├── fraud_rules.json              # Fraud rule definitions
│   ├── product_catalog.json          # Product catalog
│   ├── lead_score_weights.json       # Lead Score weights (w1-w5)
│   └── campaigns.json                # Campaign configurations
│
├── docker/
│   ├── Dockerfile                    # Application Docker image
│   ├── docker-compose.yml            # Multi-container orchestration
│   └── .env.example                  # Environment variables template
│
├── requirements.txt                  # Python dependencies
├── README.md                         # Project documentation
└── Makefile                          # Common commands (run, test, deploy)
```

---


## 8. Công nghệ sử dụng (Tech Stack)

| Tầng | Công nghệ | Mục đích |
|---|---|---|
| **Data Processing** | Pandas, NumPy | Làm sạch, feature engineering |
| **Fraud Detection** | scikit-learn (Isolation Forest), XGBoost, SHAP | Phát hiện gian lận + giải thích |
| **Recommendation** | scikit-learn / PyTorch | Gợi ý sản phẩm |
| **Lead Scoring** | Custom Python (NumPy) | Tính lead_score, xếp hạng user |
| **LLM Integration** | deepseek / google-generativeai | Sinh kịch bản tư vấn |
| **Agent Orchestration** | LangGraph | Điều phối workflow |
| **Backend API** | FastAPI, Uvicorn | REST API + WebSocket |
| **Database** | PostgreSQL 15, Redis 7 | Lưu trữ + cache |
| **Frontend** | Streamlit / React + Tailwind | Dashboard 2 tab |
| **Visualization** | Plotly, Matplotlib | Biểu đồ SHAP, gauge, timeline |
| **Deployment** | Docker, Docker Compose | Containerization |
| **Monitoring** | Prometheus, Grafana (future) | Giám sát latency, error rate |
