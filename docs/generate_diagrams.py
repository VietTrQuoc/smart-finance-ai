"""
Generate architecture & database diagrams for AI Transaction Analyzer.
Output: PNG images in docs/diagrams/
"""
import os
import sys

# Add Graphviz to PATH (Windows)
graphviz_bin = r"C:\Program Files\Graphviz\bin"
if os.path.isdir(graphviz_bin) and graphviz_bin not in os.environ.get("PATH", ""):
    os.environ["PATH"] = graphviz_bin + os.pathsep + os.environ.get("PATH", "")
    os.add_dll_directory(graphviz_bin)

import graphviz

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "diagrams")
os.makedirs(OUT_DIR, exist_ok=True)

# ─── Color palette ───
C_DATASOURCE  = "#1a1a2e"
C_DATA        = "#0f3460"
C_FRAUD       = "#533483"
C_REC         = "#1b7a4a"
C_LEAD        = "#b8860b"
C_LLM         = "#c0392b"
C_AGENT       = "#2c3e50"
C_API         = "#2471a3"
C_DASH        = "#17202a"
C_DB          = "#34495e"
C_DECISION    = "#e67e22"
C_BLOCK       = "#c0392b"
C_FONT        = "#e0e0e0"
C_FONT_DARK   = "#2c3e50"


def make_style(g, name, fill, font_color="#e0e0e0", shape="box", style="filled,rounded"):
    """Create a node style and return its attribute dict."""
    attrs = {
        "shape": shape,
        "style": style,
        "fillcolor": fill,
        "fontcolor": font_color,
        "fontname": "Segoe UI",
        "fontsize": "10",
        "margin": "0.15,0.1",
    }
    return attrs


def style_node(g, name, fill, font_color="#e0e0e0", shape="box", style_extra="filled,rounded"):
    """Apply inline style to a single node."""
    g.node(name, style=style_extra, fillcolor=fill, fontcolor=font_color,
           fontname="Segoe UI", fontsize="10", margin="0.12,0.08", shape=shape)


# ═══════════════════════════════════════════════════════════════
# DIAGRAM 1 — Architecture Overview
# ═══════════════════════════════════════════════════════════════
def draw_architecture_overview():
    g = graphviz.Digraph("ArchitectureOverview", format="png",
                         engine="dot")
    g.attr(rankdir="TB", compound="true", nodesep="0.4", ranksep="0.6",
           bgcolor="#0d1117", fontname="Segoe UI", fontcolor="#e0e0e0")
    g.attr("node", fontname="Segoe UI", fontsize="10", margin="0.12,0.08")
    g.attr("edge", color="#586069", fontcolor="#8b949e", fontsize="9")

    # ── Data Source ──
    with g.subgraph(name="cluster_source") as c:
        c.attr(label="📦 DATA SOURCE", style="filled,rounded", fillcolor="#1a1a2e",
               fontcolor="#e0e0e0", fontsize="12", penwidth="0")
        style_node(c, "raw_db", C_DATASOURCE, shape="cylinder", style_extra="filled")
        c.node("raw_db", "Raw Transaction DB\n(transaction_id, user_id,\namount, merchant_category,\ndevice_id, ip_address...)")

    # ── Layer 1: Data Prep ──
    with g.subgraph(name="cluster_l1") as c:
        c.attr(label="🔧 LAYER 1 — Data Preparation", style="filled,rounded",
               fillcolor="#0d1117", fontcolor="#58a6ff", fontsize="11", color="#58a6ff", penwidth="1")
        style_node(c, "cleaning", C_DATA)
        c.node("cleaning", "🧹 Data Cleaning\n(drop duplicates, normalize,\nhandle missing)")
        style_node(c, "feat_eng", C_DATA)
        c.node("feat_eng", "⚙ Recommendation Features\n(RFM + Category Ratio\n+ Cashflow + Cycle)")
        style_node(c, "fraud_feat", C_DATA)
        c.node("fraud_feat", "⚙ Fraud Features\n(Velocity + Behavioral\n+ Device/Channel + Graph)")

    # ── Feature Store ──
    with g.subgraph(name="cluster_fs") as c:
        c.attr(label="🗂️ FEATURE STORE", style="filled,rounded",
               fillcolor="#0d1117", fontcolor="#58a6ff", fontsize="11", color="#58a6ff", penwidth="1")
        style_node(c, "user_feat", C_DB, shape="folder")
        c.node("user_feat", "📊 User-Feature Matrix")
        style_node(c, "fraud_feat_store", C_DB, shape="folder")
        c.node("fraud_feat_store", "🔴 Fraud-Feature Matrix")

    # ── Layer 2: Fraud Detection ──
    with g.subgraph(name="cluster_l2") as c:
        c.attr(label="🚨 LAYER 2 — Fraud Detection Engine", style="filled,rounded",
               fillcolor="#0d1117", fontcolor="#e74c3c", fontsize="11", color="#533483", penwidth="1")
        style_node(c, "rule_fraud", C_FRAUD)
        c.node("rule_fraud", "📏 Rule-based Filter\n(7 Hard Rules)")
        style_node(c, "iso_forest", C_FRAUD)
        c.node("iso_forest", "🌲 Isolation Forest\n(Unsupervised)")
        style_node(c, "xgboost", C_FRAUD)
        c.node("xgboost", "🚀 XGBoost Classifier\n(+SMOTE)")
        style_node(c, "decision", C_FRAUD)
        c.node("decision", "⚡ Decision Engine\n(Weighted Ensemble)")
        style_node(c, "shap", C_FRAUD)
        c.node("shap", "🔍 SHAP Explainer\n(Explainable AI)")

    # ── Decision Gate ──
    style_node(g, "gate", C_DECISION, "#fff", shape="diamond", style_extra="filled")
    g.node("gate", "FRAUD\nGATE?\nfraud_score")

    # ── Layer 3: Recommendation ──
    with g.subgraph(name="cluster_l3") as c:
        c.attr(label="🎯 LAYER 3 — Recommendation Engine", style="filled,rounded",
               fillcolor="#0d1117", fontcolor="#2ecc71", fontsize="11", color="#1b7a4a", penwidth="1")
        style_node(c, "rec_scorer", C_REC)
        c.node("rec_scorer", "📐 Rule-based Scorer\n(Score fromng product\nby behavior)")
        style_node(c, "rec_filter", C_REC)
        c.node("rec_filter", "🔎 Fraud + Risk Filter\n(Loại SP rủi ro cao\nnếu fraud > 0.3)")
        style_node(c, "top3", C_REC)
        c.node("top3", "🏆 Top-3 Products\n(+ Reason + Score)")

    # ── Layer 3.5: Lead Scoring ──
    with g.subgraph(name="cluster_l35") as c:
        c.attr(label="⭐ LAYER 3.5 — Lead Scoring & Prioritization", style="filled,rounded",
               fillcolor="#0d1117", fontcolor="#f1c40f", fontsize="11", color="#b8860b", penwidth="1")
        style_node(c, "lead_calc", C_LEAD, "#fff")
        c.node("lead_calc", "📊 Lead Score Calculator\n(5 Components:\nMatch + Propensity + Recency\n+ Value − Fatigue)")
        style_node(c, "lead_queue", C_LEAD, "#fff")
        c.node("lead_queue", "📋 Lead Queue Builder\n(Sort + Filter + Paginate\nHot/Warm/Cold)")

    # ── Layer 4: Agent Orchestration ──
    with g.subgraph(name="cluster_l4") as c:
        c.attr(label="🤖 LAYER 4 — Agentic Orchestration (LangGraph)", style="filled,rounded",
               fillcolor="#0d1117", fontcolor="#3498db", fontsize="11", color="#2c3e50", penwidth="1")
        style_node(c, "data_agent", C_AGENT)
        c.node("data_agent", "📡 Data Agent\nFetch profile + history")
        style_node(c, "fraud_agent", C_AGENT)
        c.node("fraud_agent", "🚨 Fraud Agent\nScore + Flag + SHAP")
        style_node(c, "rec_agent", C_AGENT)
        c.node("rec_agent", "🎯 Rec Agent\nTop-3 + Reason")
        style_node(c, "lead_agent", C_AGENT)
        c.node("lead_agent", "⭐ Lead Score Agent\nCalculate + Update")
        style_node(c, "pitch_agent", C_AGENT)
        c.node("pitch_agent", "💬 Pitching Agent\nGenerate script")
        style_node(c, "format_agent", C_AGENT)
        c.node("format_agent", "📝 Response Formatter\nNormalize JSON")

    # ── Layer 5: LLM ──
    with g.subgraph(name="cluster_l5") as c:
        c.attr(label="🧠 LAYER 5 — LLM Pitching Bot", style="filled,rounded",
               fillcolor="#0d1117", fontcolor="#e74c3c", fontsize="11", color="#c0392b", penwidth="1")
        style_node(c, "guardrail", C_LLM)
        c.node("guardrail", "🛡️ Safety Guardrail\n(Fraud check + Content filter)")
        style_node(c, "prompt_tpl", C_LLM)
        c.node("prompt_tpl", "📝 Prompt Template\n(Customer + Product + Reason)")
        style_node(c, "llm_api", C_LLM, shape="cylinder")
        c.node("llm_api", "🌐 Gemini / Groq API\n(80-120 words)")
        style_node(c, "fallback", C_LLM)
        c.node("fallback", "🔄 Fallback Template\n(if LLM timeout)")

    # ── Layer 6: API ──
    with g.subgraph(name="cluster_l6") as c:
        c.attr(label="🔌 LAYER 6 — FastAPI Backend", style="filled,rounded",
               fillcolor="#0d1117", fontcolor="#3498db", fontsize="11", color="#2471a3", penwidth="1")
        for name, label in [
            ("api_fraud", "POST /fraud/score"),
            ("api_rec", "GET /recommendations/{uid}"),
            ("api_lead", "GET /recommendations/lead-queue"),
            ("api_mark", "POST /recommendations/mark-consulted"),
            ("api_pitch", "POST /users/{uid}/generate-pitch"),
            ("api_feedback", "POST /fraud/feedback"),
        ]:
            style_node(c, name, C_API)
            c.node(name, label)

    # ── Databases ──
    with g.subgraph(name="cluster_db") as c:
        c.attr(label="💾 DATABASES (PostgreSQL + Redis)", style="filled,rounded",
               fillcolor="#0d1117", fontcolor="#58a6ff", fontsize="11", color="#34495e", penwidth="1")
        for name, label in [
            ("db_txn", "transactions"),
            ("db_user", "user_features"),
            ("db_fraud", "fraud_alerts\nfraud_model_scores"),
            ("db_prod", "product_catalog"),
            ("db_consult", "consultation_log\nlead_scores\nmarketing_campaigns"),
            ("db_pitch", "pitch_logs\nrecommendation_logs"),
            ("db_cache", "⚡ Redis Cache\n(velocity features)"),
        ]:
            shape = "cylinder" if "Redis" not in label else "box"
            style_node(c, name, C_DB, shape=shape, style_extra="filled")
            c.node(name, label)

    # ── Dashboard ──
    with g.subgraph(name="cluster_dash") as c:
        c.attr(label="🖥️ DASHBOARD (Streamlit / React)", style="filled,rounded",
               fillcolor="#0d1117", fontcolor="#8b949e", fontsize="11", color="#30363d", penwidth="1")
        with c.subgraph(name="cluster_tab1") as t:
            t.attr(label="🚨 Tab: Fraud Detection", style="filled,rounded",
                   fillcolor="#1a1a2e", fontcolor="#e74c3c", fontsize="10", color="#533483", penwidth="1")
            for name, label in [
                ("gauge", "⭕ Fraud Score Gauge"),
                ("alerts_panel", "🔔 Fraud Alerts Panel"),
                ("shap_chart", "📊 SHAP Waterfall"),
                ("timeline", "📅 Suspicious TX Timeline"),
                ("confirm_btn", "✅ Confirm / ❌ False+"),
            ]:
                style_node(t, name, "#1a1a2e", C_FONT)
                t.node(name, label, fontsize="9")
        with c.subgraph(name="cluster_tab2") as t:
            t.attr(label="🎯 Tab: Recommendation", style="filled,rounded",
                   fillcolor="#1a1a2e", fontcolor="#2ecc71", fontsize="10", color="#1b7a4a", penwidth="1")
            for name, label in [
                ("lead_table", "📋 Lead Queue Table"),
                ("camp_filter", "🔽 Campaign Filter"),
                ("insights_panel", "💡 Customer Insights"),
                ("top3_card", "🏆 Top-3 Products Card"),
                ("pitch_btn", "🎤 Generate Pitch"),
                ("mark_btn", "✔️ Mark Consulted"),
            ]:
                style_node(t, name, "#1a1a2e", C_FONT)
                t.node(name, label, fontsize="9")

    # ── Users ──
    style_node(g, "fraud_analyst", "#1a1a2e", C_FONT, shape="component")
    g.node("fraud_analyst", "👨‍💻 Fraud Analyst\n(Review alerts,\nconfirm/false-positive)")
    style_node(g, "marketer", "#1a1a2e", C_FONT, shape="component")
    g.node("marketer", "👩‍💼 Marketer / Telesales\n(View Lead Queue,\ncall customers)")

    # ── Block node ──
    style_node(g, "block_rec", C_BLOCK, "#fff")
    g.node("block_rec", "🚫 BLOCK\nKhông gợi ý\nsản phẩm")

    # ── Edges ──
    g.edge("raw_db", "cleaning")
    g.edge("cleaning", "feat_eng")
    g.edge("cleaning", "fraud_feat")
    g.edge("feat_eng", "user_feat")
    g.edge("fraud_feat", "fraud_feat_store")
    g.edge("fraud_feat_store", "rule_fraud")
    g.edge("fraud_feat_store", "iso_forest")
    g.edge("fraud_feat_store", "xgboost")
    g.edge("rule_fraud", "decision")
    g.edge("iso_forest", "decision")
    g.edge("xgboost", "decision")
    g.edge("decision", "shap")
    g.edge("decision", "gate")
    g.edge("user_feat", "rec_scorer")
    g.edge("gate", "rec_filter", label="fraud < 0.7", color="#2ecc71", fontcolor="#2ecc71")
    g.edge("gate", "block_rec", label="fraud ≥ 0.7", color="#e74c3c", fontcolor="#e74c3c")
    g.edge("rec_scorer", "rec_filter")
    g.edge("rec_filter", "top3")
    g.edge("top3", "lead_calc")
    g.edge("user_feat", "lead_calc", style="dashed", color="#b8860b")
    g.edge("lead_calc", "lead_queue")
    g.edge("data_agent", "fraud_agent")
    g.edge("fraud_agent", "rec_agent")
    g.edge("rec_agent", "lead_agent")
    g.edge("lead_agent", "pitch_agent")
    g.edge("pitch_agent", "format_agent")
    g.edge("gate", "pitch_agent", label="fraud < 0.3", color="#2ecc71", fontcolor="#2ecc71")
    g.edge("gate", "format_agent", label="fraud ≥ 0.3", color="#e67e22", fontcolor="#e67e22")
    g.edge("pitch_agent", "guardrail")
    g.edge("guardrail", "prompt_tpl")
    g.edge("prompt_tpl", "llm_api")
    g.edge("llm_api", "fallback", style="dashed", color="#e74c3c", label="timeout")
    g.edge("top3", "api_rec")
    g.edge("lead_queue", "api_lead")
    g.edge("lead_queue", "api_mark")
    g.edge("format_agent", "api_pitch")
    g.edge("format_agent", "api_feedback")
    g.edge("decision", "api_fraud")
    g.edge("api_fraud", "gauge")
    g.edge("api_fraud", "alerts_panel")
    g.edge("api_fraud", "shap_chart")
    g.edge("api_fraud", "timeline")
    g.edge("api_feedback", "confirm_btn")
    g.edge("api_lead", "lead_table")
    g.edge("api_lead", "camp_filter")
    g.edge("api_rec", "insights_panel")
    g.edge("api_rec", "top3_card")
    g.edge("api_pitch", "pitch_btn")
    g.edge("api_mark", "mark_btn")
    g.edge("fraud_analyst", "gauge", style="dashed", color="#e74c3c")
    g.edge("marketer", "lead_table", style="dashed", color="#2ecc71")

    out = os.path.join(OUT_DIR, "01_architecture_overview")
    g.render(out, cleanup=True)
    print(f"✅ Saved: {out}.png")


# ═══════════════════════════════════════════════════════════════
# DIAGRAM 2 — Fraud Detection Flow (detailed)
# ═══════════════════════════════════════════════════════════════
def draw_fraud_detection_flow():
    g = graphviz.Digraph("FraudDetectionFlow", format="png", engine="dot")
    g.attr(rankdir="TB", compound="true", nodesep="0.3", ranksep="0.4",
           bgcolor="#0d1117", fontname="Segoe UI", fontcolor="#e0e0e0")
    g.attr("node", fontname="Segoe UI", fontsize="10", margin="0.1,0.08")
    g.attr("edge", color="#586069", fontcolor="#8b949e", fontsize="9")

    # Input
    style_node(g, "tx_in", "#1a1a2e", C_FONT, shape="component")
    g.node("tx_in", "🔄 New Transaction Arrives")
    style_node(g, "extract", C_DATA)
    g.node("extract", "⚙ Feature Extraction\n(Velocity + Behavioral\n+ Device + Sequence)")

    # Layer 1: Rule-based
    with g.subgraph(name="cluster_rule") as c:
        c.attr(label="📏 LAYER 1 — Rule-based Filter (< 5ms)", style="filled,rounded",
               fillcolor="#0d1117", fontcolor="#2ecc71", fontsize="11", color="#2ecc71", penwidth="1")
        for i, (name, label) in enumerate([
            ("r1", "Rule 1: Amount Spike\n(amount > 5×avg)"),
            ("r2", "Rule 2: Velocity\n(>10 tx/hour)"),
            ("r3", "Rule 3: Device Change\n(+ large tx)"),
            ("r4", "Rule 4: Night Large TX\n(>20M VND, 22h-6h)"),
            ("r5", "Rule 5: Fast Cash-out\n(<10 min after deposit)"),
            ("r6", "Rule 6: Many-to-One\n(>10 senders/24h)"),
            ("r7", "Rule 7: Circular TX\n(A→B→C→A)"),
        ]):
            style_node(c, name, C_FRAUD)
            c.node(name, label, fontsize="9")
        style_node(c, "rule_score", "#2ecc71", "#fff")
        c.node("rule_score", "Rule Score\n(0.1 / 0.6 / 0.9)")

    # Layer 2: Isolation Forest
    with g.subgraph(name="cluster_if") as c:
        c.attr(label="🌲 LAYER 2 — Isolation Forest (< 10ms)", style="filled,rounded",
               fillcolor="#0d1117", fontcolor="#3498db", fontsize="11", color="#3498db", penwidth="1")
        style_node(c, "if_model", C_FRAUD)
        c.node("if_model", "Isolation Forest\n(200 trees,\ncontamination=0.01)")
        style_node(c, "anomaly", C_FRAUD)
        c.node("anomaly", "Anomaly Score\n(normalized 0-1)")

    # Layer 3: XGBoost
    with g.subgraph(name="cluster_xgb") as c:
        c.attr(label="🚀 LAYER 3 — XGBoost Classifier (< 10ms)", style="filled,rounded",
               fillcolor="#0d1117", fontcolor="#e67e22", fontsize="11", color="#e67e22", penwidth="1")
        style_node(c, "xgb_model", C_FRAUD)
        c.node("xgb_model", "XGBoost Classifier\n(300 trees, depth=6,\n+SMOTE oversampling)")
        style_node(c, "fraud_prob", C_FRAUD)
        c.node("fraud_prob", "Fraud Probability\n(0-1)")

    # Ensemble
    with g.subgraph(name="cluster_ens") as c:
        c.attr(label="⚡ FINAL DECISION ENGINE", style="filled,rounded",
               fillcolor="#0d1117", fontcolor="#9b59b6", fontsize="11", color="#9b59b6", penwidth="1")
        style_node(c, "ensemble", "#9b59b6", "#fff")
        c.node("ensemble", "Weighted Ensemble\n0.2×Rule + 0.3×IF + 0.5×XGB")
        style_node(c, "final_gate", C_DECISION, "#fff", shape="diamond")
        c.node("final_gate", "fraud_score?")

    # Output
    style_node(g, "pass_out", "#2ecc71", "#fff", shape="signature")
    g.node("pass_out", "✅ PASS\n(< 0.3)\nAllow all")
    style_node(g, "review_out", "#f39c12", "#fff", shape="signature")
    g.node("review_out", "⚠️ REVIEW\n(0.3 - 0.7)\nManual check")
    style_node(g, "block_out", "#e74c3c", "#fff", shape="signature")
    g.node("block_out", "🚫 BLOCK\n(> 0.7)\nAlert + Deny")

    # SHAP
    with g.subgraph(name="cluster_shap") as c:
        c.attr(label="🔍 SHAP EXPLAINABILITY (< 50ms)", style="filled,rounded",
               fillcolor="#0d1117", fontcolor="#e67e22", fontsize="11", color="#e67e22", penwidth="1")
        style_node(c, "shap_calc", C_FRAUD)
        c.node("shap_calc", "SHAP TreeExplainer")
        style_node(c, "shap_out", C_FRAUD)
        c.node("shap_out", "Top Features:\namount_zscore: +0.35\ndevice_change: +0.28\ntx_count_1h: +0.22")

    # Edges
    g.edge("tx_in", "extract")
    g.edge("extract", "r1")
    g.edge("extract", "r2")
    g.edge("extract", "r3")
    g.edge("extract", "r4")
    g.edge("extract", "r5")
    g.edge("extract", "r6")
    g.edge("extract", "r7")
    for r in ["r1","r2","r3","r4","r5","r6","r7"]:
        g.edge(r, "rule_score")
    g.edge("extract", "if_model")
    g.edge("if_model", "anomaly")
    g.edge("extract", "xgb_model")
    g.edge("xgb_model", "fraud_prob")
    g.edge("rule_score", "ensemble")
    g.edge("anomaly", "ensemble")
    g.edge("fraud_prob", "ensemble")
    g.edge("ensemble", "final_gate")
    g.edge("final_gate", "pass_out", label="< 0.3", color="#2ecc71", fontcolor="#2ecc71")
    g.edge("final_gate", "review_out", label="0.3 - 0.7", color="#f39c12", fontcolor="#f39c12")
    g.edge("final_gate", "block_out", label="> 0.7", color="#e74c3c", fontcolor="#e74c3c")
    g.edge("block_out", "shap_calc", style="dashed", color="#e74c3c")
    g.edge("shap_calc", "shap_out")

    out = os.path.join(OUT_DIR, "02_fraud_detection_flow")
    g.render(out, cleanup=True)
    print(f"✅ Saved: {out}.png")


# ═══════════════════════════════════════════════════════════════
# DIAGRAM 3 — Recommendation + Lead Scoring Flow
# ═══════════════════════════════════════════════════════════════
def draw_recommendation_lead_flow():
    g = graphviz.Digraph("RecLeadFlow", format="png", engine="dot")
    g.attr(rankdir="TB", compound="true", nodesep="0.3", ranksep="0.5",
           bgcolor="#0d1117", fontname="Segoe UI", fontcolor="#e0e0e0")
    g.attr("node", fontname="Segoe UI", fontsize="10", margin="0.1,0.08")
    g.attr("edge", color="#586069", fontcolor="#8b949e", fontsize="9")

    # Input + Gate
    style_node(g, "user_in", "#1a1a2e", C_FONT, shape="component")
    g.node("user_in", "👤 User Profile + Features")
    style_node(g, "fraud_gate", C_DECISION, "#fff", shape="diamond")
    g.node("fraud_gate", "Fraud\nCheck?")
    style_node(g, "blocked", C_BLOCK, "#fff", shape="signature")
    g.node("blocked", "🚫 BLOCKED\nNo recommendation")
    style_node(g, "risk_gate", "#f39c12", "#fff", shape="diamond")
    g.node("risk_gate", "Risk\nFilter?")

    # Products
    with g.subgraph(name="cluster_prods") as c:
        c.attr(label="🎯 RECOMMENDATION — Rule-based Scorer", style="filled,rounded",
               fillcolor="#0d1117", fontcolor="#2ecc71", fontsize="11", color="#1b7a4a", penwidth="1")
        for name, label in [
            ("p1", "Thẻ TD hoàn tiền\n0.4×shop + 0.2×freq"),
            ("p2", "Bảo hiểm du lịch\n0.5×travel + 0.3×flight"),
            ("p3", "Vay tiêu dùng\n0.4×cashflow + 0.3×balance"),
            ("p4", "Vay thấu chi\n0.5×end_month + 0.3×vol"),
            ("p5", "Tiết kiệm linh hoạt\n0.6×pos_cf + 0.4×balance"),
            ("p6", "Bảo hiểm sức khỏe\n0.5×health + 0.3×medical"),
        ]:
            style_node(c, name, C_REC)
            c.node(name, label, fontsize="9")
        style_node(c, "rank", C_REC)
        c.node("rank", "🏆 Rank + Filter\n→ Top-3")

    # Lead Scoring
    with g.subgraph(name="cluster_lead") as c:
        c.attr(label="⭐ LEAD SCORING ENGINE", style="filled,rounded",
               fillcolor="#0d1117", fontcolor="#f1c40f", fontsize="11", color="#b8860b", penwidth="1")
        for name, label, clr in [
            ("ls1", "Product Match\n(max top-3 score)", C_LEAD),
            ("ls2", "Propensity Score\n(need signals)", C_LEAD),
            ("ls3", "Recency Boost\n(days since contact)", C_LEAD),
            ("ls4", "Customer Value\n(monetary pct)", C_LEAD),
            ("ls5", "Fatigue Penalty\n(contact freq)", "#c0392b"),
        ]:
            style_node(c, name, clr, "#fff" if clr == C_LEAD else C_FONT)
            c.node(name, label, fontsize="9")
        style_node(c, "ls_calc", C_LEAD, "#fff")
        c.node("ls_calc", "LEAD_SCORE =\n0.30×Match + 0.25×Propensity\n+ 0.20×Recency + 0.15×Value\n− 0.10×Fatigue")

    # Tiers
    style_node(g, "tier_gate", C_DECISION, "#fff", shape="diamond")
    g.node("tier_gate", "Lead\nTier?")
    style_node(g, "hot", "#e74c3c", "#fff", shape="signature")
    g.node("hot", "🔥 Hot\n(> 0.85)")
    style_node(g, "warm", "#f39c12", "#fff", shape="signature")
    g.node("warm", "🟡 Warm\n(0.6-0.85)")
    style_node(g, "cold", "#3498db", "#fff", shape="signature")
    g.node("cold", "🔵 Cold\n(< 0.6)")
    style_node(g, "queue", C_LEAD, "#fff", shape="folder")
    g.node("queue", "📋 LEAD QUEUE\nSorted by lead_score DESC\n→ Marketer calls top users")

    # Edges
    g.edge("user_in", "fraud_gate")
    g.edge("fraud_gate", "blocked", label="fraud ≥ 0.7", color="#e74c3c", fontcolor="#e74c3c")
    g.edge("fraud_gate", "risk_gate", label="fraud < 0.7", color="#2ecc71", fontcolor="#2ecc71")
    for p in ["p1","p2","p3","p4","p5","p6"]:
        g.edge("risk_gate", p, style="dashed", color="#1b7a4a")
        g.edge(p, "rank")
    g.edge("rank", "ls1")
    g.edge("user_in", "ls2", style="dashed")
    g.edge("user_in", "ls3", style="dashed")
    g.edge("user_in", "ls4", style="dashed")
    g.edge("user_in", "ls5", style="dashed")
    for ls in ["ls1","ls2","ls3","ls4","ls5"]:
        g.edge(ls, "ls_calc")
    g.edge("ls_calc", "tier_gate")
    g.edge("tier_gate", "hot", label="> 0.85", color="#e74c3c", fontcolor="#e74c3c")
    g.edge("tier_gate", "warm", label="0.6-0.85", color="#f39c12", fontcolor="#f39c12")
    g.edge("tier_gate", "cold", label="< 0.6", color="#3498db", fontcolor="#3498db")
    g.edge("hot", "queue")
    g.edge("warm", "queue")
    g.edge("cold", "queue")

    out = os.path.join(OUT_DIR, "03_recommendation_lead_flow")
    g.render(out, cleanup=True)
    print(f"✅ Saved: {out}.png")


# ═══════════════════════════════════════════════════════════════
# DIAGRAM 4 — Database ERD
# ═══════════════════════════════════════════════════════════════
def draw_database_erd():
    g = graphviz.Digraph("DatabaseERD", format="png", engine="dot")
    g.attr(rankdir="LR", compound="true", nodesep="0.3", ranksep="0.5",
           bgcolor="#0d1117", fontname="Segoe UI", fontcolor="#e0e0e0")
    g.attr("node", fontname="Segoe UI", fontsize="9", margin="0.08,0.06")
    g.attr("edge", color="#586069", fontcolor="#8b949e", fontsize="8", arrowsize="0.7")

    tables = {
        "transactions": ("transactions", [
            "transaction_id PK",
            "user_id FK",
            "transaction_time",
            "amount",
            "merchant_category",
            "device_id",
            "ip_address",
            "status",
        ], C_DATA),
        "user_features": ("user_features", [
            "user_id PK",
            "recency_days",
            "frequency_30d",
            "monetary_30d",
            "shopping_ratio",
            "travel_ratio",
            "risk_score",
            "...",
        ], "#0f3460"),
        "fraud_alerts": ("fraud_alerts", [
            "alert_id PK",
            "user_id FK",
            "transaction_id FK",
            "fraud_type",
            "fraud_score",
            "severity",
            "alert_status",
        ], C_FRAUD),
        "fraud_model_scores": ("fraud_model_scores", [
            "score_id PK",
            "user_id FK",
            "transaction_id FK",
            "rule_based_score",
            "isolation_forest_score",
            "xgboost_score",
            "final_fraud_score",
            "shap_values",
        ], C_FRAUD),
        "fraud_rules": ("fraud_rules", [
            "rule_id PK",
            "rule_name",
            "rule_type",
            "threshold",
            "severity",
            "is_active",
        ], C_FRAUD),
        "product_catalog": ("product_catalog", [
            "product_id PK",
            "product_name",
            "product_type",
            "target_behavior",
            "risk_allowed",
        ], C_REC),
        "recommendation_logs": ("recommendation_logs", [
            "log_id PK",
            "user_id FK",
            "product_id FK",
            "score",
            "reason",
        ], C_REC),
        "pitch_logs": ("pitch_logs", [
            "pitch_id PK",
            "user_id FK",
            "product_id FK",
            "prompt",
            "generated_script",
            "llm_model",
            "tokens_used",
        ], C_LLM),
        "consultation_log": ("consultation_log", [
            "consultation_id PK",
            "user_id FK",
            "marketer_id",
            "product_id FK",
            "consultation_status",
            "contact_channel",
            "contacted_at",
            "next_follow_up_at",
        ], C_LEAD),
        "lead_scores": ("lead_scores", [
            "user_id PK",
            "lead_score",
            "lead_tier",
            "top_product_id FK",
            "product_match_score",
            "propensity_score",
            "recency_boost",
            "customer_value_score",
            "fatigue_penalty",
            "days_since_last_contact",
            "contact_count_30d",
            "eligibility_status",
        ], C_LEAD),
        "marketing_campaigns": ("marketing_campaigns", [
            "campaign_id PK",
            "campaign_name",
            "target_product_type",
            "target_behavior",
            "min_lead_score",
            "is_active",
            "start_date",
            "end_date",
        ], C_LEAD),
    }

    for key, (label, fields, color) in tables.items():
        table_html = f'''<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">
        <TR><TD BGCOLOR="{color}" COLSPAN="1"><FONT COLOR="white"><B>{label}</B></FONT></TD></TR>'''
        for f in fields:
            bg = "#1a1a2e"
            fc = "#c9d1d9"
            if "PK" in f:
                fc = "#f1c40f"
            table_html += f'<TR><TD BGCOLOR="{bg}" ALIGN="LEFT"><FONT COLOR="{fc}" POINT-SIZE="9">{f}</FONT></TD></TR>'
        table_html += '</TABLE>>'
        g.node(key, table_html, shape="plaintext")

    # Relationships
    g.edge("transactions", "fraud_alerts", label="triggers", style="dashed")
    g.edge("transactions", "fraud_model_scores", label="scored as", style="dashed")
    g.edge("fraud_rules", "fraud_alerts", label="triggers", style="dotted")
    g.edge("user_features", "fraud_alerts", label="has")
    g.edge("user_features", "recommendation_logs", label="receives")
    g.edge("user_features", "pitch_logs", label="receives pitch")
    g.edge("user_features", "consultation_log", label="consulted for")
    g.edge("user_features", "lead_scores", label="has", color="#b8860b", fontcolor="#b8860b")
    g.edge("product_catalog", "recommendation_logs", label="recommended")
    g.edge("product_catalog", "pitch_logs", label="pitched")
    g.edge("product_catalog", "consultation_log", label="consulted")
    g.edge("lead_scores", "product_catalog", label="top_product", color="#b8860b", fontcolor="#b8860b",
           style="dashed")
    g.edge("consultation_log", "lead_scores", label="feeds into", color="#b8860b",
           fontcolor="#b8860b", style="dashed")
    g.edge("marketing_campaigns", "lead_scores", label="filters", color="#b8860b",
           fontcolor="#b8860b", style="dotted")

    out = os.path.join(OUT_DIR, "04_database_erd")
    g.render(out, cleanup=True)
    print(f"✅ Saved: {out}.png")


# ═══════════════════════════════════════════════════════════════
# DIAGRAM 5 — Deployment Architecture
# ═══════════════════════════════════════════════════════════════
def draw_deployment():
    g = graphviz.Digraph("Deployment", format="png", engine="dot")
    g.attr(rankdir="TB", compound="true", nodesep="0.3", ranksep="0.3",
           bgcolor="#0d1117", fontname="Segoe UI", fontcolor="#e0e0e0")
    g.attr("node", fontname="Segoe UI", fontsize="10", margin="0.1,0.08")
    g.attr("edge", color="#586069", fontsize="9")

    with g.subgraph(name="cluster_docker") as c:
        c.attr(label="🐳 Docker Compose Environment", style="filled,rounded",
               fillcolor="#0d1117", fontcolor="#58a6ff", fontsize="13", color="#58a6ff", penwidth="2")

        with c.subgraph(name="cluster_frontend") as f:
            f.attr(label="🖥️ Frontend (Port 8501/3000)", style="filled,rounded",
                   fillcolor="#1a1a2e", fontcolor="#8b949e", fontsize="11")
            style_node(f, "fe", "#1a1a2e", C_FONT)
            f.node("fe", "Streamlit / React\n2-Tab Dashboard")

        with c.subgraph(name="cluster_backend") as b:
            b.attr(label="🔌 Backend (Port 8000)", style="filled,rounded",
                   fillcolor="#1a1a2e", fontcolor="#3498db", fontsize="11")
            style_node(b, "be", C_API)
            b.node("be", "FastAPI\nREST + WebSocket")
            style_node(b, "sw", C_API)
            b.node("sw", "Swagger UI\nAuto Docs")

        with c.subgraph(name="cluster_models") as m:
            m.attr(label="🧠 Model Services", style="filled,rounded",
                   fillcolor="#1a1a2e", fontcolor="#9b59b6", fontsize="11")
            for name, label, clr in [
                ("svc_fraud", "Fraud Detection\n(scikit-learn+XGBoost)", C_FRAUD),
                ("svc_rec", "Recommendation\n(scikit-learn/PyTorch)", C_REC),
                ("svc_lead", "Lead Scoring\n(Custom Python)", C_LEAD),
                ("svc_pitch", "LLM Pitching\n(Gemini/Groq)", C_LLM),
            ]:
                style_node(m, name, clr, "#fff" if clr == C_LEAD else C_FONT)
                m.node(name, label)

        with c.subgraph(name="cluster_agents") as a:
            a.attr(label="🤖 Agent Orchestration", style="filled,rounded",
                   fillcolor="#1a1a2e", fontcolor="#3498db", fontsize="11")
            style_node(a, "ag", C_AGENT)
            a.node("ag", "LangGraph\nWorkflow Engine")

        with c.subgraph(name="cluster_data") as d:
            d.attr(label="💾 Data Layer", style="filled,rounded",
                   fillcolor="#1a1a2e", fontcolor="#58a6ff", fontsize="11")
            style_node(d, "pg", C_DB, shape="cylinder")
            d.node("pg", "PostgreSQL 15\n(Port 5432)")
            style_node(d, "rd", "#c0392b", C_FONT, shape="cylinder")
            d.node("rd", "Redis 7\n(Port 6379)")
            style_node(d, "pgv", C_DB, shape="folder")
            d.node("pgv", "📁 pg_data\nVolume")
            style_node(d, "rdv", "#c0392b", C_FONT, shape="folder")
            d.node("rdv", "📁 redis_data\nVolume")

    # External
    style_node(g, "gemini", "#c0392b", C_FONT, shape="cylinder")
    g.node("gemini", "🌐 Google Gemini API\ngemini-1.5-flash")
    style_node(g, "groq", "#c0392b", C_FONT, shape="cylinder")
    g.node("groq", "🌐 Groq API\nllama-3.1-70b")

    # Connections
    g.edge("fe", "be", dir="both")
    g.edge("be", "sw")
    g.edge("be", "svc_fraud")
    g.edge("be", "svc_rec")
    g.edge("be", "svc_lead")
    g.edge("be", "svc_pitch")
    g.edge("be", "ag")
    g.edge("svc_fraud", "pg")
    g.edge("svc_fraud", "rd")
    g.edge("svc_rec", "pg")
    g.edge("svc_lead", "pg")
    g.edge("svc_pitch", "pg")
    g.edge("ag", "svc_fraud", style="dashed")
    g.edge("ag", "svc_rec", style="dashed")
    g.edge("ag", "svc_lead", style="dashed")
    g.edge("ag", "svc_pitch", style="dashed")
    g.edge("svc_pitch", "gemini")
    g.edge("svc_pitch", "groq")
    g.edge("pg", "pgv")
    g.edge("rd", "rdv")

    out = os.path.join(OUT_DIR, "05_deployment")
    g.render(out, cleanup=True)
    print(f"✅ Saved: {out}.png")


# ═══════════════════════════════════════════════════════════════
# DIAGRAM 6 — Marketer Daily Workflow
# ═══════════════════════════════════════════════════════════════
def draw_marketer_workflow():
    g = graphviz.Digraph("MarketerWorkflow", format="png", engine="dot")
    g.attr(rankdir="TB", compound="true", nodesep="0.4", ranksep="0.5",
           bgcolor="#0d1117", fontname="Segoe UI", fontcolor="#e0e0e0")
    g.attr("node", fontname="Segoe UI", fontsize="10", margin="0.12,0.1")
    g.attr("edge", color="#586069", fontcolor="#8b949e", fontsize="9")

    style_node(g, "start", "#1a1a2e", C_FONT, shape="component")
    g.node("start", "👩‍💼 Marketer opens Dashboard\n→ Tab Recommendation")
    style_node(g, "queue_view", C_LEAD, "#fff")
    g.node("queue_view", "📋 View Lead Queue\n(Users ranked by lead_score)")
    style_node(g, "filter", C_API)
    g.node("filter", "🔽 Optional: Filter by\nCampaign / Product Type / Tier")
    style_node(g, "select", C_REC)
    g.node("select", "👆 Click top user\n(highest lead_score)")
    style_node(g, "insights", C_REC)
    g.node("insights", "💡 View:\n• Customer Insights\n• Top-3 Products + Reason\n• Lead Score Breakdown\n• Consultation History")
    style_node(g, "gen_pitch", "#c0392b", C_FONT, shape="diamond")
    g.node("gen_pitch", "Generate\nPitch?")
    style_node(g, "script", C_LLM)
    g.node("script", "📝 LLM generates\npersonalized script\n(80-120 words)")
    style_node(g, "call", "#2ecc71", "#fff", shape="component")
    g.node("call", "📞 Marketer calls\ncustomer using script")
    style_node(g, "result", C_DECISION, "#fff", shape="diamond")
    g.node("result", "Call\nResult?")
    style_node(g, "interested", "#2ecc71", "#fff", shape="signature")
    g.node("interested", "✅ Interested\n→ Set follow-up")
    style_node(g, "converted", "#f1c40f", "#2c3e50", shape="signature")
    g.node("converted", "🎉 Converted!\n→ Sale closed")
    style_node(g, "not_int", "#e74c3c", "#fff", shape="signature")
    g.node("not_int", "❌ Not Interested\n→ Skip 30 days")
    style_node(g, "no_ans", "#95a5a6", "#fff", shape="signature")
    g.node("no_ans", "📵 No Answer\n→ Retry in 3 days")
    style_node(g, "mark", C_LEAD, "#fff")
    g.node("mark", "✔️ Click [Mark Consulted]\n→ Status + Notes saved")
    style_node(g, "update", C_LEAD, "#fff")
    g.node("update", "🔄 Lead Score auto-updates\n→ User drops in queue")
    style_node(g, "next", C_REC)
    g.node("next", "➡️ Next user in queue\nappears automatically")

    # Edges
    g.edge("start", "queue_view")
    g.edge("queue_view", "filter", style="dashed")
    g.edge("filter", "select")
    g.edge("queue_view", "select")
    g.edge("select", "insights")
    g.edge("insights", "gen_pitch")
    g.edge("gen_pitch", "script", label="Yes", color="#2ecc71", fontcolor="#2ecc71")
    g.edge("gen_pitch", "call", label="Skip (manual)", color="#f39c12", fontcolor="#f39c12")
    g.edge("script", "call")
    g.edge("call", "result")
    g.edge("result", "interested")
    g.edge("result", "converted")
    g.edge("result", "not_int")
    g.edge("result", "no_ans")
    g.edge("interested", "mark")
    g.edge("converted", "mark")
    g.edge("not_int", "mark")
    g.edge("no_ans", "mark")
    g.edge("mark", "update")
    g.edge("update", "next")
    g.edge("next", "select", style="dashed", color="#2ecc71")

    out = os.path.join(OUT_DIR, "06_marketer_workflow")
    g.render(out, cleanup=True)
    print(f"✅ Saved: {out}.png")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Generating architecture diagrams...\n")
    draw_architecture_overview()
    draw_fraud_detection_flow()
    draw_recommendation_lead_flow()
    draw_database_erd()
    draw_deployment()
    draw_marketer_workflow()
    print(f"\n🎉 All 6 diagrams saved to: {OUT_DIR}")
