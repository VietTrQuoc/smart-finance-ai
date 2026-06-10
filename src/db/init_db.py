"""Create and seed the local Smart Finance SQLite database."""

from __future__ import annotations

import argparse
import json
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.backend.dashboard_data import (
    assign_segment,
    build_dashboard_payload,
    load_product_catalog,
    load_user_features,
    normalize_features,
)
from src.data.feature_engineering import USER_FEATURE_COLUMNS


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = Path(__file__).with_name("schema.sql")
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "smart_finance.db"
DEFAULT_TRANSACTION_PATH = PROJECT_ROOT / "data" / "synthetic_fraud_data.csv"
MODEL_VERSION = "seg_local_features_v1"


def initialize_database(
    db_path: Path,
    *,
    project_root: Path = PROJECT_ROOT,
    transaction_limit: int | None = 10_000,
    recreate: bool = False,
) -> dict[str, int | str]:
    if db_path.exists():
        if not recreate:
            raise FileExistsError(f"Database already exists: {db_path}")
        db_path.unlink()

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

        data_path, raw_features = load_user_features(project_root / "data")
        products = load_product_catalog(project_root / "configs" / "product_catalog.json")
        features = normalize_features(raw_features)
        payload = build_dashboard_payload(features, products, data_path)

        seed_user_features(conn, features)
        seed_product_catalog(conn, products)
        seed_transactions(
                conn,
                project_root / "data" / "synthetic_fraud_data.csv",
                transaction_limit,
            )
        seed_lead_scores(conn, payload.leads)
        seed_recommendation_logs(conn, payload.leads)
        seed_fraud_alerts(conn, payload.fraud_alerts)
        seed_fraud_model_scores(conn, payload.fraud_alerts)
        seed_fraud_rules(conn)
        seed_segmentation(conn, features)
        seed_marketing_campaigns(conn)
        conn.commit()
        counts = table_counts(conn)
    finally:
        conn.close()

    return {
        "database": str(db_path),
        "feature_source": str(data_path),
        **counts,
    }


def table_counts(conn: sqlite3.Connection) -> dict[str, int]:
    tables = [
        "transactions",
        "user_features",
        "product_catalog",
        "fraud_alerts",
        "fraud_model_scores",
        "fraud_rules",
        "recommendation_logs",
        "pitch_logs",
        "consultation_log",
        "lead_scores",
        "segmentation_model_versions",
        "user_segments",
        "cluster_profiles",
        "segmentation_runs",
        "marketing_campaigns",
    ]
    return {
        table: int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        for table in tables
    }


def seed_user_features(conn: sqlite3.Connection, features: pd.DataFrame) -> int:
    rows = []
    for _, row in features.iterrows():
        rows.append(tuple(to_db_value(row.get(column)) for column in USER_FEATURE_COLUMNS))

    placeholders = ", ".join("?" for _ in USER_FEATURE_COLUMNS)
    columns = ", ".join(USER_FEATURE_COLUMNS)
    conn.executemany(
        f"INSERT OR REPLACE INTO user_features ({columns}) VALUES ({placeholders})",
        rows,
    )
    return len(rows)


def seed_product_catalog(conn: sqlite3.Connection, products: list[dict[str, Any]]) -> int:
    rows = []
    for product in products:
        eligibility = product.get("eligibility_json", {})
        rows.append(
            (
                product["product_id"],
                product["product_name"],
                product["product_type"],
                product.get("description"),
                product.get("target_behavior"),
                json.dumps(product.get("target_signals_json", {}), ensure_ascii=False),
                json.dumps(eligibility, ensure_ascii=False),
                product.get("risk_allowed", "low"),
                float(eligibility.get("min_risk_score", 0.0)),
                float(eligibility.get("max_risk_score", 1.0)),
                float(product.get("campaign_priority", 0.5)),
                product.get("reason_template"),
                int(bool(product.get("is_active", True))),
            )
        )

    conn.executemany(
        """
        INSERT OR REPLACE INTO product_catalog (
            product_id, product_name, product_type, description, target_behavior,
            target_signals_json, eligibility_json, risk_allowed, min_risk_score,
            max_risk_score, campaign_priority, reason_template, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    return len(rows)


def seed_transactions(
    conn: sqlite3.Connection, transaction_path: Path, limit: int | None
) -> int:
    if not transaction_path.exists():
        return 0

    imported = 0
    rows = []
    reader = pd.read_csv(transaction_path, chunksize=10_000)
    try:
        for chunk in reader:
            if limit is not None:
                chunk = chunk.head(max(limit - imported, 0))
            for _, row in chunk.iterrows():
                rows.append(
                    (
                        row["transaction_id"],
                        row["customer_id"],
                        row["timestamp"],
                        float(row["amount"]),
                        "card_purchase",
                        row.get("merchant"),
                        row.get("merchant_category"),
                        row.get("country"),
                        row.get("city"),
                        row.get("card_type"),
                        int(bool_value(row.get("card_present"))),
                        None,
                        None,
                        row.get("channel"),
                        row.get("device"),
                        row.get("device_fingerprint"),
                        row.get("ip_address"),
                        "completed",
                        int(bool_value(row.get("is_fraud"))),
                    )
                )
            imported += len(chunk)
            if len(rows) >= 20_000:
                insert_transactions(conn, rows)
                rows.clear()
            if limit is not None and imported >= limit:
                break
    finally:
        reader.close()

    if rows:
        insert_transactions(conn, rows)
    return imported


def insert_transactions(conn: sqlite3.Connection, rows: list[tuple]) -> None:
    conn.executemany(
        """
        INSERT OR REPLACE INTO transactions (
            transaction_id, user_id, transaction_time, amount, transaction_type,
            merchant_name, merchant_category, country, city, card_type,
            card_present, balance_before, balance_after, channel, device_id,
            device_fingerprint, ip_address, status, is_fraud
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def seed_lead_scores(conn: sqlite3.Connection, leads: list[dict[str, Any]]) -> int:
    rows = []
    now = utc_now()
    for lead in leads:
        top_product = lead["products"][0] if lead["products"] else {}
        breakdown = lead["breakdown"]
        rows.append(
            (
                lead["id"],
                lead["leadScore"],
                lead["tier"],
                top_product.get("id"),
                top_product.get("score", 0.0),
                breakdown["product_match"],
                breakdown["propensity"],
                breakdown["recency"],
                breakdown["customer_value"],
                breakdown["fatigue"],
                None,
                0,
                None,
                lead["eligibility"],
                now,
            )
        )

    conn.executemany(
        """
        INSERT OR REPLACE INTO lead_scores (
            user_id, lead_score, lead_tier, top_product_id, top_product_score,
            product_match_score, propensity_score, recency_score,
            customer_value_score, fatigue_score, days_since_last_contact,
            contact_count_30d, last_contact_status, eligibility_status,
            calculated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    return len(rows)


def seed_recommendation_logs(conn: sqlite3.Connection, leads: list[dict[str, Any]]) -> int:
    rows = []
    now = utc_now()
    for lead in leads:
        for product in lead["products"]:
            rows.append(
                (
                    f"rec_{uuid.uuid4().hex}",
                    lead["id"],
                    product["id"],
                    product["score"],
                    json.dumps(lead["breakdown"], ensure_ascii=False),
                    json.dumps(product["reasons"], ensure_ascii=False),
                    lead["fraudScore"],
                    lead["riskScore"],
                    MODEL_VERSION,
                    now,
                )
            )

    conn.executemany(
        """
        INSERT INTO recommendation_logs (
            log_id, user_id, product_id, score, score_breakdown_json,
            reason_json, fraud_score, risk_score, model_version, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    return len(rows)


def seed_fraud_alerts(conn: sqlite3.Connection, alerts: list[dict[str, Any]]) -> int:
    rows = []
    now = utc_now()
    for alert in alerts:
        rows.append(
            (
                alert["id"],
                alert["userId"],
                alert["transactionId"],
                alert.get("status"),
                alert["score"],
                alert["severity"],
                alert["summary"],
                json.dumps(alert.get("shap", {}), ensure_ascii=False),
                "open",
                None,
                None,
                now,
            )
        )

    conn.executemany(
        """
        INSERT OR REPLACE INTO fraud_alerts (
            alert_id, user_id, transaction_id, fraud_type, fraud_score,
            severity, description, evidence, alert_status, reviewed_by,
            reviewed_at, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    return len(rows)


def seed_fraud_model_scores(conn: sqlite3.Connection, alerts: list[dict[str, Any]]) -> int:
    rows = []
    now = utc_now()
    for alert in alerts:
        rows.append(
            (
                f"score_{uuid.uuid4().hex}",
                alert["userId"],
                alert["transactionId"],
                alert["score"],
                alert["score"],
                0.5,
                int(alert["score"] >= 0.5),
                json.dumps(alert.get("shap", {}), ensure_ascii=False),
                json.dumps({"source": "dashboard_seed"}, ensure_ascii=False),
                "fraud_seed_v1",
                now,
            )
        )

    conn.executemany(
        """
        INSERT INTO fraud_model_scores (
            score_id, user_id, transaction_id, xgboost_score, final_fraud_score,
            decision_threshold, predicted_fraud, shap_values, features_used,
            model_version, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    return len(rows)


def seed_fraud_rules(conn: sqlite3.Connection) -> int:
    now = utc_now()
    rules = [
        ("R01", "Amount Spike", "amount", "amount_zscore >= threshold", 5.0, "high"),
        ("R02", "High Velocity", "velocity", "tx_count_1h >= threshold", 10.0, "high"),
        ("R03", "Device Change Risk", "device", "new_device_flag = 1", 1.0, "medium"),
        ("R04", "Night Large Transaction", "time", "night and amount > 3x avg", 3.0, "medium"),
        ("R05", "Fast Cash-out", "velocity", "cashout_velocity >= threshold", 3.0, "high"),
        ("R06", "Many Accounts Same Device", "network", "multiple_accounts_same_device >= threshold", 3.0, "medium"),
        ("R07", "Circular Transaction", "network", "circular_transaction_score >= threshold", 0.7, "high"),
    ]
    conn.executemany(
        """
        INSERT OR REPLACE INTO fraud_rules (
            rule_id, rule_name, rule_type, condition, threshold, severity,
            is_active, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
        """,
        [(*rule, now, now) for rule in rules],
    )
    return len(rules)


def seed_segmentation(conn: sqlite3.Connection, features: pd.DataFrame) -> int:
    started = time.time()
    now = utc_now()
    segmented = features.copy()
    segmented["customer_value_score"] = segmented["monetary_90d"].rank(pct=True).fillna(0.5)
    segmented["segment"] = segmented.apply(assign_segment, axis=1)

    segment_names = sorted(segmented["segment"].unique())
    cluster_map = {name: idx for idx, name in enumerate(segment_names)}

    conn.execute(
        """
        INSERT OR REPLACE INTO segmentation_model_versions (
            model_version, n_components, k, scaler_path, svd_path, kmeans_path,
            feature_schema, metrics_json, selection_policy, status,
            trained_at, activated_at, created_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            MODEL_VERSION,
            0,
            len(cluster_map),
            "not_applicable/local_sqlite_seed",
            "not_applicable/local_sqlite_seed",
            "not_applicable/local_sqlite_seed",
            json.dumps(USER_FEATURE_COLUMNS, ensure_ascii=False),
            json.dumps({"source": "heuristic_seed", "users": int(len(segmented))}, ensure_ascii=False),
            "heuristic segment labels derived from canonical user_features",
            "active",
            now,
            now,
            "init_db.py",
        ),
    )

    user_rows = []
    cluster_rows = []
    total = max(len(segmented), 1)
    for segment, group in segmented.groupby("segment"):
        cluster_id = cluster_map[segment]
        centroid = float(group["customer_value_score"].mean())
        for _, row in group.iterrows():
            user_rows.append(
                (
                    row["user_id"],
                    MODEL_VERSION,
                    cluster_id,
                    abs(float(row["customer_value_score"]) - centroid),
                    "heuristic_seed",
                    now,
                )
            )

        cluster_rows.append(
            (
                MODEL_VERSION,
                cluster_id,
                segment,
                describe_segment(segment),
                int(len(group)),
                float(len(group) / total),
                json.dumps(top_features(group), ensure_ascii=False),
                json.dumps(product_hints(segment), ensure_ascii=False),
                json.dumps({"customer_value_score": centroid}, ensure_ascii=False),
                None,
                None,
                "rule_map",
                0.75,
                0,
                now,
            )
        )

    conn.executemany(
        """
        INSERT OR REPLACE INTO user_segments (
            user_id, model_version, cluster_id, distance_to_centroid,
            assignment_mode, assigned_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        user_rows,
    )
    conn.executemany(
        """
        INSERT OR REPLACE INTO cluster_profiles (
            model_version, cluster_id, cluster_name, description, size, ratio,
            top_features_json, product_hints_json, centroid_json,
            previous_cluster_id, previous_similarity, llm_model,
            llm_confidence, needs_review, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        cluster_rows,
    )

    conn.execute(
        """
        INSERT OR REPLACE INTO segmentation_runs (
            run_id, model_version, mode, status, triggered_by, users_processed,
            changed_users_count, duration_seconds, metrics_json, error_message,
            started_at, finished_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"run_{MODEL_VERSION}",
            MODEL_VERSION,
            "full_retrain",
            "succeeded",
            "init_db.py",
            int(len(segmented)),
            int(len(segmented)),
            round(time.time() - started, 4),
            json.dumps({"cluster_count": len(cluster_map)}, ensure_ascii=False),
            None,
            now,
            utc_now(),
        ),
    )
    return len(user_rows)


def seed_marketing_campaigns(conn: sqlite3.Connection) -> int:
    campaigns = [
        ("CAMP001", "Travel 2026", "Travel insurance campaign", "insurance", "travel_high", 0.70, 1, "2026-06-01", "2026-08-31"),
        ("CAMP002", "Cashflow Support", "Loan campaign for cashflow needs", "loan", "negative_cashflow", 0.60, 1, "2026-09-01", "2026-12-31"),
        ("CAMP003", "Flexible Saving", "Savings campaign for low-risk customers", "saving", "positive_cashflow", 0.65, 1, "2026-06-01", "2026-12-31"),
    ]
    conn.executemany(
        """
        INSERT OR REPLACE INTO marketing_campaigns (
            campaign_id, campaign_name, description, target_product_type,
            target_behavior, min_lead_score, is_active, start_date, end_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        campaigns,
    )
    return len(campaigns)


def top_features(group: pd.DataFrame) -> list[dict[str, Any]]:
    candidates = [
        "shopping_ratio",
        "travel_ratio",
        "healthcare_ratio",
        "monetary_90d",
        "risk_score",
        "customer_value_score",
    ]
    values = []
    for column in candidates:
        if column in group.columns:
            values.append({"feature": column, "mean": round(float(group[column].mean()), 4)})
    return sorted(values, key=lambda item: item["mean"], reverse=True)[:5]


def product_hints(segment: str) -> list[dict[str, Any]]:
    mapping = {
        "Gold Travel": [("P002", 0.86, "Travel behavior is prominent")],
        "Basic Retail": [("P001", 0.82, "Shopping behavior is prominent")],
        "Premium High Value": [("P005", 0.80, "Customer value is high"), ("P006", 0.68, "Low-risk insurance fit")],
        "Domestic Everyday": [("P005", 0.62, "Stable everyday banking fit"), ("P006", 0.58, "Low-risk insurance fit")],
    }
    return [
        {
            "product_id": product_id,
            "affinity": affinity,
            "confidence": 0.75,
            "positive_signals": [segment.lower().replace(" ", "_")],
            "reason": reason,
        }
        for product_id, affinity, reason in mapping.get(segment, [])
    ]


def describe_segment(segment: str) -> str:
    descriptions = {
        "Gold Travel": "Customers with visible travel activity and cross-sell potential for low-risk insurance.",
        "Basic Retail": "Customers with strong retail or grocery spending behavior.",
        "Premium High Value": "High-value customers with stronger monetary activity.",
        "Domestic Everyday": "Everyday customers with broad, lower-intensity product fit.",
    }
    return descriptions.get(segment, "Heuristic customer segment from local feature store.")


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "t"}


def to_db_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create and seed local SQLite DB")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--transaction-limit", type=int, default=10_000)
    parser.add_argument("--full-transactions", action="store_true")
    parser.add_argument("--recreate", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    limit = None if args.full_transactions else args.transaction_limit
    summary = initialize_database(args.db, transaction_limit=limit, recreate=args.recreate)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
