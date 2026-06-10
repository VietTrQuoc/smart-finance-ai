import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from src.data.feature_engineering import (
    USER_FEATURE_COLUMNS,
    build_user_features,
    build_user_features_from_csv,
)


class BuildUserFeaturesTest(unittest.TestCase):
    def test_builds_canonical_user_feature_contract(self):
        transactions = pd.DataFrame(
            [
                {
                    "customer_id": "C1",
                    "timestamp": "2024-01-31T00:00:00Z",
                    "amount": 100.0,
                    "merchant_category": "Retail",
                    "transaction_hour": 23,
                    "weekend_transaction": False,
                    "distance_from_home": 0,
                    "high_risk_merchant": False,
                    "card_present": True,
                    "is_fraud": False,
                },
                {
                    "customer_id": "C1",
                    "timestamp": "2024-01-28T00:00:00Z",
                    "amount": 200.0,
                    "merchant_category": "Travel",
                    "transaction_hour": 12,
                    "weekend_transaction": True,
                    "distance_from_home": 1,
                    "high_risk_merchant": True,
                    "card_present": True,
                    "is_fraud": True,
                },
                {
                    "customer_id": "C1",
                    "timestamp": "2023-12-01T00:00:00Z",
                    "amount": 50.0,
                    "merchant_category": "Restaurant",
                    "transaction_hour": 13,
                    "weekend_transaction": False,
                    "distance_from_home": 0,
                    "high_risk_merchant": False,
                    "card_present": True,
                    "is_fraud": False,
                },
                {
                    "customer_id": "C2",
                    "timestamp": "2024-01-15T00:00:00Z",
                    "amount": 80.0,
                    "merchant_category": "Healthcare",
                    "transaction_hour": 9,
                    "weekend_transaction": False,
                    "distance_from_home": 0,
                    "high_risk_merchant": False,
                    "card_present": True,
                    "is_fraud": False,
                },
            ]
        )

        features = build_user_features(
            transactions,
            as_of="2024-02-01T00:00:00Z",
            updated_at="2024-02-01T00:00:00Z",
        )

        self.assertEqual(list(features.columns), USER_FEATURE_COLUMNS)
        self.assertEqual(len(features), 2)

        c1 = features.set_index("user_id").loc["C1"]
        self.assertEqual(c1["frequency_7d"], 2)
        self.assertEqual(c1["frequency_30d"], 2)
        self.assertEqual(c1["frequency_90d"], 3)
        self.assertEqual(c1["monetary_30d"], 300.0)
        self.assertAlmostEqual(c1["shopping_ratio"], 100.0 / 350.0)
        self.assertAlmostEqual(c1["travel_ratio"], 200.0 / 350.0)
        self.assertAlmostEqual(c1["food_ratio"], 50.0 / 350.0)
        self.assertEqual(c1["expense_total_30d"], 300.0)
        self.assertEqual(c1["net_cashflow_30d"], -300.0)
        self.assertEqual(c1["negative_cashflow_days"], 2)
        self.assertEqual(c1["end_month_negative_cashflow_flag"], 1)
        self.assertAlmostEqual(c1["weekend_spending_ratio"], 200.0 / 350.0)
        self.assertAlmostEqual(c1["night_transaction_ratio"], 1.0 / 3.0)
        self.assertEqual(c1["travel_frequency_90d"], 1)
        self.assertEqual(c1["shopping_frequency_30d"], 1)
        self.assertAlmostEqual(c1["risk_score"], 0.30)

    def test_chunked_csv_keeps_binary_flags_binary(self):
        transactions = pd.DataFrame(
            [
                {
                    "customer_id": "C1",
                    "timestamp": "2024-01-28T00:00:00Z",
                    "amount": 10.0,
                    "merchant_category": "Retail",
                    "transaction_hour": 8,
                    "weekend_transaction": True,
                    "distance_from_home": 0,
                    "high_risk_merchant": False,
                    "card_present": True,
                    "is_fraud": False,
                },
                {
                    "customer_id": "C1",
                    "timestamp": "2024-01-29T00:00:00Z",
                    "amount": 20.0,
                    "merchant_category": "Retail",
                    "transaction_hour": 9,
                    "weekend_transaction": False,
                    "distance_from_home": 0,
                    "high_risk_merchant": False,
                    "card_present": True,
                    "is_fraud": False,
                },
            ]
        )

        with TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "transactions.csv"
            output_path = Path(temp_dir) / "user_features.csv"
            transactions.to_csv(input_path, index=False)

            features = build_user_features_from_csv(
                input_path,
                output_path,
                chunksize=1,
                as_of="2024-02-01T00:00:00Z",
            )

        c1 = features.set_index("user_id").loc["C1"]
        self.assertEqual(c1["end_month_negative_cashflow_flag"], 1)
        self.assertEqual(c1["negative_cashflow_days"], 2)


if __name__ == "__main__":
    unittest.main()
