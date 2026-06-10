import json
import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from src.backend.dashboard_data import load_dashboard_payload
from src.db.init_db import initialize_database


class InitDbTest(unittest.TestCase):
    def test_initializes_sqlite_database_from_local_artifacts(self):
        with TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            data_dir = project_root / "data"
            configs_dir = project_root / "configs"
            data_dir.mkdir()
            configs_dir.mkdir()

            pd.DataFrame(
                [
                    {
                        "user_id": "C1",
                        "recency_days": 1,
                        "frequency_7d": 2,
                        "frequency_30d": 8,
                        "frequency_90d": 12,
                        "monetary_7d": 200,
                        "monetary_30d": 800,
                        "monetary_90d": 1200,
                        "avg_transaction_amount": 100,
                        "max_transaction_amount": 250,
                        "std_transaction_amount": 40,
                        "shopping_ratio": 0.7,
                        "travel_ratio": 0.1,
                        "food_ratio": 0.1,
                        "education_ratio": 0.0,
                        "healthcare_ratio": 0.0,
                        "entertainment_ratio": 0.1,
                        "cashout_ratio": 0.0,
                        "transfer_ratio": 0.0,
                        "loan_payment_ratio": 0.0,
                        "income_total_30d": 0,
                        "expense_total_30d": 800,
                        "net_cashflow_30d": -800,
                        "negative_cashflow_days": 2,
                        "end_month_negative_cashflow_flag": 1,
                        "balance_volatility": 0.4,
                        "salary_detected_flag": 0,
                        "weekend_spending_ratio": 0.2,
                        "night_transaction_ratio": 0.0,
                        "travel_frequency_90d": 1,
                        "shopping_frequency_30d": 5,
                        "risk_score": 0.2,
                        "updated_at": "2026-06-09T00:00:00+00:00",
                    }
                ]
            ).to_csv(data_dir / "user_features_sample.csv", index=False)

            pd.DataFrame(
                [
                    {
                        "transaction_id": "TX1",
                        "customer_id": "C1",
                        "timestamp": "2026-06-01T00:00:00Z",
                        "merchant": "Store",
                        "merchant_category": "Retail",
                        "amount": 100,
                        "country": "VN",
                        "city": "HCMC",
                        "card_type": "Basic Credit",
                        "card_present": True,
                        "channel": "pos",
                        "device": "POS",
                        "device_fingerprint": "fp",
                        "ip_address": "127.0.0.1",
                        "is_fraud": False,
                    }
                ]
            ).to_csv(data_dir / "synthetic_fraud_data.csv", index=False)

            products = [
                {
                    "product_id": "P001",
                    "product_name": "Cashback Credit Card",
                    "product_type": "credit_card",
                    "risk_allowed": "medium",
                    "target_behavior": "shopping_high",
                    "target_signals_json": {"shopping_ratio": 1.0},
                    "eligibility_json": {"max_risk_score": 0.65},
                    "campaign_priority": 0.8,
                    "reason_template": "Shopping fit",
                    "is_active": True,
                }
            ]
            (configs_dir / "product_catalog.json").write_text(json.dumps(products), encoding="utf-8")

            db_path = data_dir / "smart_finance.db"
            summary = initialize_database(db_path, project_root=project_root, transaction_limit=1)

            self.assertEqual(summary["transactions"], 1)
            conn = sqlite3.connect(db_path)
            try:
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM user_features").fetchone()[0], 1)
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM product_catalog").fetchone()[0], 1)
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM user_segments").fetchone()[0], 1)
            finally:
                conn.close()

            payload = load_dashboard_payload(project_root)
            self.assertEqual(payload.meta["rowCount"], 1)
            self.assertEqual(payload.leads[0]["id"], "C1")


if __name__ == "__main__":
    unittest.main()
