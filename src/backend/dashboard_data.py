"""Build dashboard payloads from local data artifacts.

This module is intentionally dependency-light: it reads the local CSV feature
store and product catalog, then produces the same shape consumed by the static
dashboard. It gives us an end-to-end path before the FastAPI/Postgres layer
exists.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


CANONICAL_FEATURE_FILES = (
    "user_features.csv",
    "user_features_sample.csv",
)


@dataclass(frozen=True)
class DashboardPayload:
    leads: list[dict[str, Any]]
    fraud_alerts: list[dict[str, Any]]
    meta: dict[str, Any]

    def to_api(self) -> dict[str, Any]:
        return {
            "leads": self.leads,
            "fraudAlerts": self.fraud_alerts,
            "meta": self.meta,
        }


def load_dashboard_payload(project_root: Path) -> DashboardPayload:
    db_path = project_root / "data" / "smart_finance.db"
    if db_path.exists():
        return load_dashboard_payload_from_db(db_path)

    data_path, features = load_user_features(project_root / "data")
    products = load_product_catalog(project_root / "configs" / "product_catalog.json")
    return build_dashboard_payload(features, products, data_path)


def load_dashboard_payload_from_db(db_path: Path) -> DashboardPayload:
    conn = sqlite3.connect(db_path)
    try:
        conn.row_factory = sqlite3.Row
        leads = load_leads_from_db(conn)
        fraud_alerts = load_fraud_alerts_from_db(conn)
        row_count = conn.execute("SELECT COUNT(*) FROM user_features").fetchone()[0]
    finally:
        conn.close()

    return DashboardPayload(
        leads=leads,
        fraud_alerts=fraud_alerts,
        meta={
            "source": str(db_path),
            "rowCount": int(row_count),
            "generatedAt": datetime.now(timezone.utc).isoformat(),
        },
    )


def load_leads_from_db(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
            ls.*,
            uf.risk_score,
            COALESCE(cp.cluster_name, 'Unsegmented') AS segment_name
        FROM lead_scores ls
        JOIN user_features uf ON uf.user_id = ls.user_id
        LEFT JOIN user_segments us ON us.user_id = ls.user_id
        LEFT JOIN segmentation_model_versions smv
            ON smv.model_version = us.model_version
           AND smv.status = 'active'
        LEFT JOIN cluster_profiles cp
            ON cp.model_version = us.model_version
           AND cp.cluster_id = us.cluster_id
        WHERE ls.eligibility_status != 'archived'
        ORDER BY ls.lead_score DESC
        LIMIT 100
        """
    ).fetchall()

    leads = []
    for row in rows:
        products = load_recommendations_from_db(conn, row["user_id"])
        fraud_score = latest_fraud_score(conn, row["user_id"])
        leads.append(
            {
                "id": row["user_id"],
                "segment": row["segment_name"],
                "tier": row["lead_tier"],
                "leadScore": row["lead_score"],
                "fraudScore": fraud_score,
                "riskScore": row["risk_score"],
                "topProduct": products[0]["name"] if products else "Blocked",
                "eligibility": row["eligibility_status"],
                "breakdown": {
                    "product_match": row["product_match_score"] or 0.0,
                    "propensity": row["propensity_score"] or 0.0,
                    "recency": row["recency_score"] or 0.0,
                    "customer_value": row["customer_value_score"] or 0.0,
                    "fatigue": row["fatigue_score"] or 0.0,
                },
                "products": products,
                "activity": [
                    f"Loaded from SQLite lead_scores at {row['calculated_at']}",
                    f"{len(products)} recommendation candidates in DB",
                    f"Eligibility: {row['eligibility_status']}",
                ],
            }
        )
    return leads


def load_recommendations_from_db(
    conn: sqlite3.Connection, user_id: str
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
            rl.product_id,
            rl.score,
            rl.reason_json,
            pc.product_name,
            pc.product_type
        FROM recommendation_logs rl
        JOIN product_catalog pc ON pc.product_id = rl.product_id
        WHERE rl.user_id = ?
        ORDER BY rl.score DESC, rl.created_at DESC
        LIMIT 3
        """,
        (user_id,),
    ).fetchall()

    products = []
    for row in rows:
        try:
            reasons = json.loads(row["reason_json"] or "[]")
        except json.JSONDecodeError:
            reasons = []
        products.append(
            {
                "id": row["product_id"],
                "name": row["product_name"],
                "type": row["product_type"],
                "score": row["score"],
                "reasons": reasons,
            }
        )
    return products


def latest_fraud_score(conn: sqlite3.Connection, user_id: str) -> float:
    row = conn.execute(
        """
        SELECT final_fraud_score
        FROM fraud_model_scores
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (user_id,),
    ).fetchone()
    return float(row["final_fraud_score"]) if row else 0.0


def load_fraud_alerts_from_db(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT *
        FROM fraud_alerts
        ORDER BY fraud_score DESC, created_at DESC
        LIMIT 50
        """
    ).fetchall()
    alerts = []
    for row in rows:
        try:
            shap = json.loads(row["evidence"] or "{}")
        except json.JSONDecodeError:
            shap = {}
        alerts.append(
            {
                "id": row["alert_id"],
                "userId": row["user_id"],
                "transactionId": row["transaction_id"],
                "severity": row["severity"],
                "score": row["fraud_score"],
                "status": row["fraud_type"] or row["alert_status"],
                "summary": row["description"] or "Fraud alert",
                "shap": shap,
                "timeline": [
                    f"Alert created at {row['created_at']}",
                    f"Status: {row['alert_status']}",
                    f"Severity: {row['severity']}",
                ],
            }
        )
    return alerts


def load_user_features(data_dir: Path) -> tuple[Path, pd.DataFrame]:
    for filename in CANONICAL_FEATURE_FILES:
        path = data_dir / filename
        if path.exists():
            return path, pd.read_csv(path)

    legacy_path = data_dir / "customer_features.csv"
    if legacy_path.exists():
        legacy = pd.read_csv(legacy_path)
        return legacy_path, adapt_legacy_customer_features(legacy)

    raise FileNotFoundError(
        "No feature store found. Expected data/user_features.csv, "
        "data/user_features_sample.csv, or data/customer_features.csv."
    )


def load_product_catalog(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def adapt_legacy_customer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Map the notebook clustering artifact into the canonical dashboard shape."""

    adapted = pd.DataFrame()
    adapted["user_id"] = df["customer_id"]
    adapted["recency_days"] = 0.0
    tx_proxy = _num(df, "distance_from_home_count", 0.0).clip(lower=1)
    adapted["frequency_7d"] = np.ceil(tx_proxy * 0.08)
    adapted["frequency_30d"] = np.ceil(tx_proxy * 0.35)
    adapted["frequency_90d"] = tx_proxy
    adapted["monetary_7d"] = _num(df, "total_amount", 0.0) * 0.08
    adapted["monetary_30d"] = _num(df, "total_amount", 0.0) * 0.35
    adapted["monetary_90d"] = _num(df, "total_amount", 0.0)
    adapted["avg_transaction_amount"] = _num(df, "mean_amount", 0.0)
    adapted["max_transaction_amount"] = _num(df, "max_amount", 0.0)
    adapted["std_transaction_amount"] = _num(df, "std_amount", 0.0)
    adapted["shopping_ratio"] = (_num(df, "merchant_Retail", 0.0) + _num(df, "merchant_Grocery", 0.0)).clip(0, 1)
    adapted["travel_ratio"] = _num(df, "merchant_Travel", 0.0).clip(0, 1)
    adapted["food_ratio"] = (_num(df, "merchant_Restaurant", 0.0) + _num(df, "merchant_Grocery", 0.0)).clip(0, 1)
    adapted["education_ratio"] = _num(df, "merchant_Education", 0.0).clip(0, 1)
    adapted["healthcare_ratio"] = _num(df, "merchant_Healthcare", 0.0).clip(0, 1)
    adapted["entertainment_ratio"] = _num(df, "merchant_Entertainment", 0.0).clip(0, 1)
    adapted["cashout_ratio"] = 0.0
    adapted["transfer_ratio"] = 0.0
    adapted["loan_payment_ratio"] = 0.0
    adapted["income_total_30d"] = 0.0
    adapted["expense_total_30d"] = adapted["monetary_30d"]
    adapted["net_cashflow_30d"] = -adapted["expense_total_30d"]
    adapted["negative_cashflow_days"] = np.minimum(30, np.ceil(adapted["frequency_30d"] / 3))
    adapted["end_month_negative_cashflow_flag"] = (adapted["negative_cashflow_days"] > 0).astype(int)
    adapted["balance_volatility"] = (_num(df, "std_amount", 0.0) / _num(df, "mean_amount", 1.0).replace(0, 1)).clip(0, 5)
    adapted["salary_detected_flag"] = 0
    adapted["weekend_spending_ratio"] = 0.0
    adapted["night_transaction_ratio"] = 0.0
    adapted["travel_frequency_90d"] = np.ceil(adapted["travel_ratio"] * tx_proxy)
    adapted["shopping_frequency_30d"] = np.ceil(adapted["shopping_ratio"] * adapted["frequency_30d"])
    adapted["risk_score"] = (
        0.35 * _num(df, "high_value_txn_ratio", 0.0)
        + 0.25 * _num(df, "distance_from_home_ratio", 0.0)
        + 0.20 * _num(df, "foreign_txn_ratio", 0.0)
        + 0.20 * (1 - _num(df, "top_country_ratio", 1.0))
    ).clip(0, 1)
    adapted["updated_at"] = datetime.now(timezone.utc).isoformat()
    return adapted


def build_dashboard_payload(
    features: pd.DataFrame,
    products: list[dict[str, Any]],
    data_path: Path | None = None,
    *,
    limit: int = 80,
) -> DashboardPayload:
    normalized = normalize_features(features)
    if normalized.empty:
        return DashboardPayload([], [], {"source": str(data_path or ""), "rowCount": 0})

    normalized["customer_value_score"] = _percentile(normalized["monetary_90d"])
    normalized["segment"] = normalized.apply(assign_segment, axis=1)

    leads = [
        build_lead(row, products)
        for _, row in normalized.sort_values("customer_value_score", ascending=False).head(limit).iterrows()
    ]
    leads.sort(key=lambda lead: lead["leadScore"], reverse=True)
    alerts = build_fraud_alerts(normalized, limit=25)
    meta = {
        "source": str(data_path or ""),
        "rowCount": int(len(normalized)),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }
    return DashboardPayload(leads, alerts, meta)


def normalize_features(features: pd.DataFrame) -> pd.DataFrame:
    df = features.copy()
    if "user_id" not in df.columns and "customer_id" in df.columns:
        df["user_id"] = df["customer_id"]

    numeric_defaults = {
        "recency_days": 0.0,
        "frequency_7d": 0.0,
        "frequency_30d": 0.0,
        "frequency_90d": 0.0,
        "monetary_7d": 0.0,
        "monetary_30d": 0.0,
        "monetary_90d": 0.0,
        "avg_transaction_amount": 0.0,
        "max_transaction_amount": 0.0,
        "std_transaction_amount": 0.0,
        "shopping_ratio": 0.0,
        "travel_ratio": 0.0,
        "food_ratio": 0.0,
        "education_ratio": 0.0,
        "healthcare_ratio": 0.0,
        "entertainment_ratio": 0.0,
        "cashout_ratio": 0.0,
        "transfer_ratio": 0.0,
        "loan_payment_ratio": 0.0,
        "income_total_30d": 0.0,
        "expense_total_30d": 0.0,
        "net_cashflow_30d": 0.0,
        "negative_cashflow_days": 0.0,
        "end_month_negative_cashflow_flag": 0.0,
        "balance_volatility": 0.0,
        "salary_detected_flag": 0.0,
        "weekend_spending_ratio": 0.0,
        "night_transaction_ratio": 0.0,
        "travel_frequency_90d": 0.0,
        "shopping_frequency_30d": 0.0,
        "risk_score": 0.0,
    }
    for column, default in numeric_defaults.items():
        df[column] = _num(df, column, default)

    df["user_id"] = df["user_id"].astype(str)
    return df[df["user_id"].str.len() > 0].reset_index(drop=True)


def build_lead(row: pd.Series, products: list[dict[str, Any]]) -> dict[str, Any]:
    fraud_score = infer_fraud_score(row)
    candidates = build_recommendations(row, products, fraud_score)
    top_score = candidates[0]["score"] if candidates else 0.0
    recency_score = 1 - min(float(row["recency_days"]) / 90, 1)
    customer_value_score = float(row["customer_value_score"])
    fatigue_score = 0.20 if fraud_score >= 0.3 else 0.08
    propensity = float(np.mean([top_score, recency_score, 1 - float(row["risk_score"])]))
    lead_score = np.clip(
        0.30 * top_score
        + 0.25 * propensity
        + 0.20 * recency_score
        + 0.15 * customer_value_score
        - 0.10 * fatigue_score,
        0,
        1,
    )

    eligibility = "eligible"
    if fraud_score >= 0.7:
        eligibility = "blocked_fraud"
    elif fraud_score >= 0.3:
        eligibility = "review_low_risk_only"

    return {
        "id": row["user_id"],
        "segment": row["segment"],
        "tier": tier_for_score(lead_score),
        "leadScore": round(float(lead_score), 4),
        "fraudScore": round(float(fraud_score), 4),
        "riskScore": round(float(row["risk_score"]), 4),
        "topProduct": candidates[0]["name"] if candidates else "Blocked",
        "eligibility": eligibility,
        "breakdown": {
            "product_match": round(float(top_score), 4),
            "propensity": round(float(propensity), 4),
            "recency": round(float(recency_score), 4),
            "customer_value": round(float(customer_value_score), 4),
            "fatigue": round(float(fatigue_score), 4),
        },
        "products": candidates[:3],
        "activity": activity_for(row, fraud_score, candidates),
    }


def build_recommendations(
    row: pd.Series, products: list[dict[str, Any]], fraud_score: float
) -> list[dict[str, Any]]:
    if fraud_score >= 0.7:
        return []

    candidates = []
    for product in products:
        if not product.get("is_active", True):
            continue
        if fraud_score >= 0.3 and product.get("risk_allowed") != "low":
            continue
        eligibility = product.get("eligibility_json", {})
        max_risk = float(eligibility.get("max_risk_score", 1))
        min_frequency = float(eligibility.get("min_frequency_30d", 0))
        if float(row["risk_score"]) > max_risk or float(row["frequency_30d"]) < min_frequency:
            continue

        behavior = weighted_signal_score(row, product.get("target_signals_json", {}))
        segment_affinity = segment_affinity_score(str(row["segment"]), str(product.get("target_behavior", "")))
        affordability = affordability_score(row)
        timing = timing_need_score(row, str(product.get("target_behavior", "")))
        priority = float(product.get("campaign_priority", 0.5))
        score = np.clip(
            0.40 * behavior
            + 0.25 * segment_affinity
            + 0.20 * affordability
            + 0.10 * timing
            + 0.05 * priority,
            0,
            1,
        )

        candidates.append(
            {
                "id": product["product_id"],
                "name": product["product_name"],
                "type": product["product_type"],
                "score": round(float(score), 4),
                "reasons": recommendation_reasons(row, product, behavior, segment_affinity, affordability),
            }
        )

    return sorted(candidates, key=lambda item: (-item["score"], item["id"]))


def weighted_signal_score(row: pd.Series, weights: dict[str, float]) -> float:
    if not weights:
        return 0.0
    total_weight = sum(float(weight) for weight in weights.values()) or 1.0
    score = 0.0
    for signal, weight in weights.items():
        score += signal_value(row, signal) * float(weight)
    return float(np.clip(score / total_weight, 0, 1))


def signal_value(row: pd.Series, signal: str) -> float:
    if signal.endswith("_inverse"):
        base = signal.removesuffix("_inverse")
        if base == "risk_score":
            return 1 - float(row["risk_score"])
        if base == "recency":
            return 1 - min(float(row["recency_days"]) / 90, 1)
        if base == "balance_volatility":
            return 1 - min(float(row["balance_volatility"]), 1)
        if base == "net_cashflow_30d":
            expense = max(float(row["expense_total_30d"]), 1)
            return min(abs(min(float(row["net_cashflow_30d"]), 0)) / expense, 1)

    if signal == "avg_transaction_amount":
        return min(np.log1p(float(row["avg_transaction_amount"])) / np.log1p(1_000_000), 1)
    if signal in {"frequency_30d", "frequency_90d", "shopping_frequency_30d", "travel_frequency_90d"}:
        return min(float(row.get(signal, 0)) / 20, 1)
    if signal == "negative_cashflow_days":
        return min(float(row["negative_cashflow_days"]) / 10, 1)
    if signal == "foreign_txn_proxy":
        return min(float(row["travel_ratio"]) + 0.25 * float(row["travel_frequency_90d"] > 0), 1)

    return float(np.clip(float(row.get(signal, 0)), 0, 1))


def assign_segment(row: pd.Series) -> str:
    if float(row["customer_value_score"]) >= 0.80:
        return "Premium High Value"
    if float(row["travel_ratio"]) >= 0.15 or float(row["travel_frequency_90d"]) >= 3:
        return "Gold Travel"
    if float(row["shopping_ratio"]) >= 0.30 or float(row["shopping_frequency_30d"]) >= 5:
        return "Basic Retail"
    return "Domestic Everyday"


def segment_affinity_score(segment: str, target_behavior: str) -> float:
    segment = segment.lower()
    target_behavior = target_behavior.lower()
    if "travel" in segment and "travel" in target_behavior:
        return 0.88
    if "retail" in segment and "shopping" in target_behavior:
        return 0.82
    if "premium" in segment and target_behavior in {"positive_cashflow", "healthcare_high"}:
        return 0.78
    if "domestic" in segment and target_behavior in {"healthcare_high", "positive_cashflow"}:
        return 0.62
    return 0.35


def affordability_score(row: pd.Series) -> float:
    value = min(np.log1p(float(row["monetary_90d"])) / np.log1p(200_000_000), 1)
    return float(np.clip((1 - float(row["risk_score"])) * 0.65 + value * 0.35, 0, 1))


def timing_need_score(row: pd.Series, target_behavior: str) -> float:
    if target_behavior == "travel_high":
        return min(float(row["travel_frequency_90d"]) / 5, 1)
    if target_behavior == "shopping_high":
        return min(float(row["shopping_frequency_30d"]) / 8, 1)
    if target_behavior in {"negative_cashflow", "end_month_cash_shortage"}:
        return max(
            min(float(row["negative_cashflow_days"]) / 10, 1),
            float(row["end_month_negative_cashflow_flag"]),
        )
    if target_behavior == "healthcare_high":
        return min(float(row["healthcare_ratio"]) * 2, 1)
    return 0.40


def recommendation_reasons(
    row: pd.Series,
    product: dict[str, Any],
    behavior: float,
    segment_affinity: float,
    affordability: float,
) -> list[str]:
    reasons = []
    target = str(product.get("target_behavior", ""))
    if behavior >= 0.5:
        reasons.append(f"Strong behavior match for {target.replace('_', ' ')}")
    if segment_affinity >= 0.6:
        reasons.append(f"Segment affinity supports {product['product_name']}")
    if affordability >= 0.65:
        reasons.append("Risk and value signals are within policy")
    if not reasons:
        reasons.append(product.get("reason_template", "Eligible under current product policy"))
    return reasons[:3]


def build_fraud_alerts(features: pd.DataFrame, *, limit: int) -> list[dict[str, Any]]:
    ranked = features.assign(fraud_score=features.apply(infer_fraud_score, axis=1))
    ranked = ranked[ranked["fraud_score"] >= 0.25].sort_values("fraud_score", ascending=False)
    alerts = []
    for index, (_, row) in enumerate(ranked.head(limit).iterrows(), start=1):
        score = float(row["fraud_score"])
        status = "block" if score >= 0.7 else "review" if score >= 0.3 else "pass"
        severity = "high" if score >= 0.7 else "medium" if score >= 0.3 else "low"
        alerts.append(
            {
                "id": f"ALERT-{index:04d}",
                "userId": row["user_id"],
                "transactionId": f"USER-{row['user_id']}",
                "severity": severity,
                "score": round(score, 4),
                "status": status,
                "summary": fraud_summary(row),
                "shap": {
                    "risk_score": round(float(row["risk_score"]), 4),
                    "night_transaction": round(float(row["night_transaction_ratio"]), 4),
                    "balance_volatility": round(min(float(row["balance_volatility"]), 1), 4),
                    "negative_cashflow": round(min(float(row["negative_cashflow_days"]) / 10, 1), 4),
                },
                "timeline": fraud_timeline(row, score),
            }
        )
    return alerts


def infer_fraud_score(row: pd.Series) -> float:
    return float(
        np.clip(
            0.82 * float(row["risk_score"])
            + 0.07 * min(float(row["night_transaction_ratio"]), 1)
            + 0.06 * min(float(row["balance_volatility"]) / 2, 1)
            + 0.05 * min(float(row["negative_cashflow_days"]) / 10, 1),
            0,
            1,
        )
    )


def fraud_summary(row: pd.Series) -> str:
    if float(row["risk_score"]) >= 0.7:
        return "High model risk score and volatile spending profile"
    if float(row["night_transaction_ratio"]) >= 0.4:
        return "Night transaction ratio is elevated"
    if float(row["balance_volatility"]) >= 1:
        return "Transaction amount volatility is elevated"
    return "Risk score requires manual review"


def fraud_timeline(row: pd.Series, score: float) -> list[str]:
    timeline = [f"Fraud score recalculated at {score:.2f}"]
    if float(row["night_transaction_ratio"]) > 0:
        timeline.append("Night transaction signal contributed")
    if float(row["balance_volatility"]) > 0.5:
        timeline.append("Amount volatility signal contributed")
    if float(row["negative_cashflow_days"]) > 0:
        timeline.append("Cashflow proxy signal contributed")
    return timeline[:4]


def activity_for(row: pd.Series, fraud_score: float, products: list[dict[str, Any]]) -> list[str]:
    if fraud_score >= 0.7:
        return ["Blocked by fraud gate", "No pitch allowed", "No recommendation returned"]
    activity = [
        f"Feature store updated at {row.get('updated_at', 'unknown')}",
        f"{len(products)} eligible product candidates",
    ]
    if fraud_score >= 0.3:
        activity.append("Review mode: low-risk products only")
    return activity


def tier_for_score(score: float) -> str:
    if score > 0.85:
        return "hot"
    if score >= 0.60:
        return "warm"
    return "cold"


def _num(df: pd.DataFrame, column: str, default: float) -> pd.Series:
    if column not in df.columns:
        return pd.Series(default, index=df.index, dtype=float)
    return pd.to_numeric(df[column], errors="coerce").fillna(default)


def _percentile(series: pd.Series) -> pd.Series:
    if series.nunique(dropna=True) <= 1:
        return pd.Series(0.5, index=series.index)
    return series.rank(pct=True).fillna(0.5)
