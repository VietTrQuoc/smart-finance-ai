import unittest

import pandas as pd

from src.backend.dashboard_data import build_dashboard_payload


PRODUCTS = [
    {
        "product_id": "P001",
        "product_name": "Cashback Credit Card",
        "product_type": "credit_card",
        "risk_allowed": "medium",
        "target_behavior": "shopping_high",
        "target_signals_json": {"shopping_ratio": 1.0},
        "eligibility_json": {"max_risk_score": 0.65},
        "campaign_priority": 0.8,
        "is_active": True,
    },
    {
        "product_id": "P002",
        "product_name": "Travel Insurance",
        "product_type": "insurance",
        "risk_allowed": "low",
        "target_behavior": "travel_high",
        "target_signals_json": {"travel_ratio": 1.0},
        "eligibility_json": {"max_risk_score": 0.9},
        "campaign_priority": 0.8,
        "is_active": True,
    },
]


class DashboardDataTest(unittest.TestCase):
    def test_blocks_products_when_fraud_score_is_high(self):
        features = pd.DataFrame(
            [
                {
                    "user_id": "C1",
                    "risk_score": 0.95,
                    "monetary_90d": 1000,
                    "travel_ratio": 0.9,
                    "shopping_ratio": 0.1,
                    "frequency_30d": 10,
                }
            ]
        )

        payload = build_dashboard_payload(features, PRODUCTS)
        lead = payload.leads[0]

        self.assertEqual(lead["eligibility"], "blocked_fraud")
        self.assertEqual(lead["products"], [])
        self.assertEqual(lead["topProduct"], "Blocked")

    def test_review_mode_keeps_low_risk_products_only(self):
        features = pd.DataFrame(
            [
                {
                    "user_id": "C2",
                    "risk_score": 0.45,
                    "monetary_90d": 1000,
                    "travel_ratio": 0.8,
                    "shopping_ratio": 0.8,
                    "frequency_30d": 10,
                }
            ]
        )

        payload = build_dashboard_payload(features, PRODUCTS)
        lead = payload.leads[0]

        self.assertEqual(lead["eligibility"], "review_low_risk_only")
        self.assertEqual([product["id"] for product in lead["products"]], ["P002"])


if __name__ == "__main__":
    unittest.main()
