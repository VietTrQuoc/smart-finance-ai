"""
Recommendation Engine: Map clusters → suitable products + customer indices.

Pipeline:
  1. Load customer_features.csv → run SVD+KMeans clustering (k=4)
  2. Load product_catalog.json
  3. Score mỗi product cho từng cụm dựa trên cluster profile
  4. Xuất danh sách: cluster → top products + customer indices

Snapshot: seg_experiment_20260604_pc11_k4
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# ── Paths ──────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
CONFIG_DIR = ROOT / "configs"
OUTPUT_DIR = ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Clustering constants (sync with kmeans_clustering_report.md) ─
N_COMPONENTS = 11
K_FINAL = 4
RANDOM_SEED = 42

# ── Final 20 features (sync with notebook & report) ────────
FINAL_FEATURES = [
    "merchant_category_ratio_Education",
    "merchant_category_ratio_Entertainment",
    "merchant_category_ratio_Gas",
    "merchant_category_ratio_Grocery",
    "merchant_category_ratio_Healthcare",
    "merchant_category_ratio_Restaurant",
    "merchant_category_ratio_Retail",
    "channel_ratio_mobile",
    "channel_ratio_pos",
    "card_type_ratio_basic",
    "card_type_ratio_gold",
    "total_amount_log",
    "mean_amount_log",
    "max_amount_log",
    "high_value_txn_ratio",
    "foreign_txn_ratio",
    "top_country_ratio",
    "city_diversity_ratio",
    "category_diversity",
    "unique_cities",
]

CLUSTER_NAMES = {
    0: "📱 Basic - Phổ thông",
    1: "🥇 Gold - Du lịch",
    2: "💎 Siêu VIP",
    3: "🏠 Đại chúng nội địa",
}

CLUSTER_DESCRIPTIONS = {
    0: "89% basic card, chi tiêu thấp (~41M), max GD thấp nhất (~2M), có giao dịch nước ngoài (36%)",
    1: "38% gold card, max GD cao nhất (~4.1M), hay đi nước ngoài (36%), nhiều thành phố",
    2: "Tổng chi tiêu ~199M (gấp 3-5 lần), GD TB ~127K, 73% high-value, 23% basic + 21% gold",
    3: "Nước ngoài thấp nhất (26%), tập trung 1 quốc gia (74%), ít thành phố nhất, chi tiêu thấp (~41M)",
}

# ── Product-scoring rule: (product_id, cluster_id, feature, operator, threshold, weight) ──
# Mỗi rule kiểm tra: nếu feature của cụm OP threshold → cộng score_weight cho product.
# Operator: 'gt' = greater than (cluster value > threshold), 'lt' = less than.
ProductScoringRule = Tuple[str, int, str, str, float, float]

SCORING_RULES: List[ProductScoringRule] = [
    # ── P001: Cashback Credit Card ──
    ("P001", 2, "total_amount_log", "gt", 0.5, 0.40),
    ("P001", 2, "high_value_txn_ratio", "gt", 0.5, 0.30),
    ("P001", 0, "card_type_ratio_basic", "gt", 0.7, 0.25),
    ("P001", 1, "max_amount_log", "gt", 0.4, 0.20),
    ("P001", 1, "merchant_category_ratio_Retail", "gt", 0.0, 0.10),
    ("P001", 3, "card_type_ratio_basic", "gt", 0.2, 0.15),

    # ── P002: Travel Insurance ──
    ("P002", 1, "foreign_txn_ratio", "gt", 0.3, 0.40),
    ("P002", 1, "card_type_ratio_gold", "gt", 0.2, 0.25),
    ("P002", 0, "foreign_txn_ratio", "gt", 0.2, 0.20),
    ("P002", 2, "total_amount_log", "gt", 1.0, 0.15),
    ("P002", 3, "foreign_txn_ratio", "lt", -0.5, 0.0),

    # ── P003: Consumer Loan ──
    ("P003", 3, "total_amount_log", "lt", -0.3, 0.30),
    ("P003", 0, "total_amount_log", "lt", -0.3, 0.25),
    ("P003", 1, "max_amount_log", "gt", 0.4, 0.20),
    ("P003", 2, "total_amount_log", "gt", 1.0, 0.10),

    # ── P004: Overdraft Loan ──
    ("P004", 0, "card_type_ratio_basic", "gt", 0.7, 0.30),
    ("P004", 3, "total_amount_log", "lt", -0.3, 0.25),
    ("P004", 1, "card_type_ratio_gold", "gt", 0.2, 0.15),
    ("P004", 2, "high_value_txn_ratio", "gt", 1.0, 0.05),

    # ── P005: Flexible Savings ──
    ("P005", 3, "top_country_ratio", "gt", 0.5, 0.35),
    ("P005", 0, "card_type_ratio_basic", "gt", 0.7, 0.25),
    ("P005", 2, "total_amount_log", "gt", 1.0, 0.30),
    ("P005", 1, "card_type_ratio_gold", "gt", 0.2, 0.20),

    # ── P006: Health Insurance ──
    ("P006", 3, "top_country_ratio", "gt", 0.3, 0.30),
    ("P006", 0, "merchant_category_ratio_Healthcare", "gt", 0.0, 0.20),
    ("P006", 1, "foreign_txn_ratio", "gt", 0.3, 0.20),
    ("P006", 2, "total_amount_log", "gt", 1.0, 0.25),
    ("P006", 2, "merchant_category_ratio_Healthcare", "gt", 0.0, 0.15),

    # ── P007: Premium Travel Card ──
    ("P007", 1, "foreign_txn_ratio", "gt", 0.3, 0.35),
    ("P007", 1, "card_type_ratio_gold", "gt", 0.2, 0.30),
    ("P007", 2, "total_amount_log", "gt", 1.0, 0.25),
    ("P007", 2, "high_value_txn_ratio", "gt", 0.5, 0.20),
    ("P007", 0, "foreign_txn_ratio", "gt", 0.2, 0.15),
    ("P007", 3, "foreign_txn_ratio", "lt", -0.5, 0.0),

    # ── P008: Life Insurance ──
    ("P008", 3, "top_country_ratio", "gt", 0.5, 0.35),
    ("P008", 0, "card_type_ratio_basic", "gt", 0.5, 0.20),
    ("P008", 1, "card_type_ratio_gold", "gt", 0.2, 0.20),
    ("P008", 2, "total_amount_log", "gt", 1.0, 0.25),
    ("P008", 2, "high_value_txn_ratio", "gt", 0.5, 0.15),

    # ── P009: Home Loan ──
    ("P009", 3, "top_country_ratio", "gt", 0.5, 0.40),
    ("P009", 3, "unique_cities", "lt", -0.5, 0.25),
    ("P009", 1, "max_amount_log", "gt", 0.4, 0.20),
    ("P009", 2, "total_amount_log", "gt", 1.0, 0.20),
    ("P009", 0, "total_amount_log", "lt", -0.3, 0.10),

    # ── P010: Auto Loan ──
    ("P010", 3, "top_country_ratio", "gt", 0.3, 0.30),
    ("P010", 3, "merchant_category_ratio_Gas", "gt", 0.0, 0.20),
    ("P010", 0, "card_type_ratio_basic", "gt", 0.5, 0.25),
    ("P010", 1, "merchant_category_ratio_Gas", "gt", 0.0, 0.15),
    ("P010", 2, "total_amount_log", "gt", 1.0, 0.15),

    # ── P011: Fixed Deposit ──
    ("P011", 3, "top_country_ratio", "gt", 0.5, 0.40),
    ("P011", 0, "top_country_ratio", "gt", -0.1, 0.25),
    ("P011", 1, "card_type_ratio_gold", "gt", 0.2, 0.20),
    ("P011", 2, "total_amount_log", "gt", 1.0, 0.20),

    # ── P012: Investment Fund ──
    ("P012", 2, "total_amount_log", "gt", 1.0, 0.45),
    ("P012", 2, "high_value_txn_ratio", "gt", 1.0, 0.35),
    ("P012", 1, "max_amount_log", "gt", 0.5, 0.15),
    ("P012", 0, "total_amount_log", "lt", -0.3, 0.0),
    ("P012", 3, "total_amount_log", "lt", -0.3, 0.0),

    # ── P013: Retirement Pension Plan ──
    ("P013", 3, "top_country_ratio", "gt", 0.5, 0.30),
    ("P013", 1, "card_type_ratio_gold", "gt", 0.2, 0.25),
    ("P013", 2, "total_amount_log", "gt", 1.0, 0.30),
    ("P013", 0, "top_country_ratio", "gt", -0.1, 0.15),

    # ── P014: Bill Payment Service ──
    ("P014", 3, "top_country_ratio", "gt", 0.5, 0.35),
    ("P014", 0, "card_type_ratio_basic", "gt", 0.5, 0.25),
    ("P014", 0, "merchant_category_ratio_Grocery", "gt", 0.0, 0.15),
    ("P014", 3, "merchant_category_ratio_Grocery", "gt", 0.0, 0.15),
    ("P014", 1, "card_type_ratio_gold", "gt", 0.2, 0.10),

    # ── P015: Personal Accident Insurance ──
    ("P015", 0, "card_type_ratio_basic", "gt", 0.5, 0.25),
    ("P015", 3, "top_country_ratio", "gt", 0.3, 0.25),
    ("P015", 3, "total_amount_log", "lt", -0.3, 0.20),
    ("P015", 1, "card_type_ratio_gold", "gt", 0.2, 0.20),
    ("P015", 2, "total_amount_log", "gt", 1.0, 0.15),
    ("P015", 0, "foreign_txn_ratio", "gt", 0.2, 0.15),
]


def load_customer_features(path: str | Path) -> pd.DataFrame:
    """Load customer_features.csv."""
    return pd.read_csv(path)


def load_product_catalog(path: str | Path) -> List[dict]:
    """Load product_catalog.json."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ────────────────────────────────────────────────────────────
# Feature engineering (replicated from notebook)
# ────────────────────────────────────────────────────────────

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engineer the 20 final features from raw customer_features.csv."""
    df = df.copy()

    # 1. Merchant category ratios
    merchant_cols = [c for c in df.columns if c.startswith("merchant_")
                     and not c.startswith("merchant_category_ratio_")]
    for col in merchant_cols:
        cat_name = col.replace("merchant_", "")
        df[f"merchant_category_ratio_{cat_name}"] = (
            df[col] / df[merchant_cols].sum(axis=1)
        )

    # 2. Channel ratios
    df["channel_ratio_mobile"] = df["mobile_ratio"]
    df["channel_ratio_pos"] = df["pos_ratio"]

    # 3. Card type ratios
    df["card_type_ratio_basic"] = df["basic_card_ratio"]
    df["card_type_ratio_gold"] = df["gold_card_ratio"]

    # 4. Log transforms
    df["total_amount_log"] = np.log1p(df["total_amount"])
    df["mean_amount_log"] = np.log1p(df["mean_amount"])
    df["max_amount_log"] = np.log1p(df["max_amount"])

    # 5. City diversity ratio
    df["city_diversity_ratio"] = df["city_diversity"] / df["unique_cities"]

    # 6. Category diversity (Simpson)
    ratio_cols = [c for c in df.columns if c.startswith("merchant_category_ratio_")]
    df["category_diversity"] = 1 - (df[ratio_cols] ** 2).sum(axis=1)

    return df


def run_clustering(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run StandardScaler → TruncatedSVD (11 PCs) → KMeans (k=4).
    Returns df with 'cluster' column added.
    """
    feature_cols = [c for c in FINAL_FEATURES if c in df.columns]
    missing = set(FINAL_FEATURES) - set(feature_cols)
    if missing:
        raise ValueError(f"Missing features: {missing}")

    X = df[feature_cols].values

    # StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # TruncatedSVD
    svd = TruncatedSVD(n_components=N_COMPONENTS, random_state=RANDOM_SEED)
    X_svd = svd.fit_transform(X_scaled)
    print(f"  SVD: {len(feature_cols)} features → {N_COMPONENTS} PCs, "
          f"variance retained = {svd.explained_variance_ratio_.sum():.4f}")

    # KMeans
    kmeans = KMeans(n_clusters=K_FINAL, random_state=RANDOM_SEED, n_init=10)
    clusters = kmeans.fit_predict(X_svd)

    df["cluster"] = clusters
    return df


def compute_cluster_zscore_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Compute Z-score profile of each cluster on the 20 final features."""
    feature_cols = [c for c in FINAL_FEATURES if c in df.columns]
    cluster_profile = df.groupby("cluster")[feature_cols].mean()
    global_mean = df[feature_cols].mean()
    global_std = df[feature_cols].std()
    profile_z = (cluster_profile - global_mean) / global_std
    return profile_z


def score_products_for_clusters(
    profile_z: pd.DataFrame,
    products: List[dict],
    rules: List[ProductScoringRule],
) -> pd.DataFrame:
    """
    Score each product for each cluster using rule-based scoring.

    Returns DataFrame with columns: cluster, product_id, product_name, score, rank
    """
    # ── Score computation ──
    # Group rules by (cluster, product_id)
    product_rule_map: Dict[Tuple[int, str], List[ProductScoringRule]] = {}
    for rule in rules:
        product_id, cluster_id, feature, operator, threshold, weight = rule
        key = (cluster_id, product_id)
        if key not in product_rule_map:
            product_rule_map[key] = []
        product_rule_map[key].append(rule)

    scores: Dict[Tuple[int, str], float] = {}
    for (cluster_id, product_id), product_rules in product_rule_map.items():
        total = 0.0
        for rule in product_rules:
            _, _, feature, operator, threshold, weight = rule
            if feature not in profile_z.columns:
                continue
            cluster_z = profile_z.loc[cluster_id, feature]

            fire = False
            if operator == "gt" and cluster_z > threshold:
                fire = True
            elif operator == "lt" and cluster_z < threshold:
                fire = True

            if fire:
                deviation = abs(cluster_z - threshold)
                total += weight * deviation

        scores[(cluster_id, product_id)] = total

    # ── Build result DataFrame ──
    rows = []
    for (cluster_id, product_id), score in scores.items():
        product = next((p for p in products if p["product_id"] == product_id), None)
        product_name = product["product_name"] if product else product_id
        rows.append({
            "cluster": cluster_id,
            "cluster_name": CLUSTER_NAMES.get(cluster_id, f"Cluster {cluster_id}"),
            "product_id": product_id,
            "product_name": product_name,
            "score": round(score, 4),
        })

    result = pd.DataFrame(rows)

    # Rank within each cluster
    result["rank"] = result.groupby("cluster")["score"].rank(
        ascending=False, method="min"
    ).astype(int)

    result = result.sort_values(["cluster", "rank"]).reset_index(drop=True)
    return result


def build_customer_product_list(
    df: pd.DataFrame,
    cluster_scores: pd.DataFrame,
    products: List[dict],
    top_n: int = 3,
) -> pd.DataFrame:
    """
    Build the final list: each customer → their cluster → top-N recommended products.
    """
    # Top-N products per cluster — keep cluster as column
    top_products = (
        cluster_scores.sort_values(["cluster", "rank"])
        .groupby("cluster", as_index=False)
        .head(top_n)
    )

    # Merge with customer data
    customer_list = df[["customer_id", "cluster"]].copy()
    customer_list["cluster_name"] = customer_list["cluster"].map(CLUSTER_NAMES)

    # For each customer, assign top-N products
    rows = []
    for _, cust in customer_list.iterrows():
        cid = cust["customer_id"]
        c_cluster = cust["cluster"]
        cluster_prods = top_products[top_products["cluster"] == c_cluster]

        for _, prod in cluster_prods.iterrows():
            rows.append({
                "customer_id": cid,
                "cluster": c_cluster,
                "cluster_name": cust["cluster_name"],
                "product_id": prod["product_id"],
                "product_name": prod["product_name"],
                "product_rank": prod["rank"],
                "product_score": prod["score"],
            })

    result = pd.DataFrame(rows)
    return result


def build_cluster_summary(
    df: pd.DataFrame,
    cluster_scores: pd.DataFrame,
    top_n: int = 3,
) -> pd.DataFrame:
    """Build a summary table: cluster → description → top products → customer count → sample IDs."""
    top_products = (
        cluster_scores.sort_values(["cluster", "rank"])
        .groupby("cluster", as_index=False)
        .head(top_n)
    )

    rows = []
    for cluster_id in sorted(df["cluster"].unique()):
        cluster_custs = df[df["cluster"] == cluster_id]
        n_custs = len(cluster_custs)
        sample_ids = cluster_custs["customer_id"].head(5).tolist()

        cluster_prods = top_products[top_products["cluster"] == cluster_id]
        products_str = " → ".join(
            f"#{r['rank']} {r['product_id']} {r['product_name']}"
            for _, r in cluster_prods.iterrows()
        )

        rows.append({
            "cluster": cluster_id,
            "cluster_name": CLUSTER_NAMES.get(cluster_id, f"Cluster {cluster_id}"),
            "description": CLUSTER_DESCRIPTIONS.get(cluster_id, ""),
            "customer_count": n_custs,
            "customer_pct": f"{n_custs / len(df) * 100:.1f}%",
            "top_products": products_str,
            "sample_customer_ids": ", ".join(sample_ids[:3]),
        })

    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("RECOMMENDATION ENGINE: Cluster → Product Mapping")
    print(f"Model snapshot: seg_experiment_20260604_pc11_k4")
    print("=" * 70)

    # 1. Load data
    print("\n[1/6] Loading customer features ...")
    df_raw = load_customer_features(DATA_DIR / "customer_features.csv")
    print(f"  Loaded: {df_raw.shape[0]} customers × {df_raw.shape[1]} columns")

    print("\n[2/6] Engineering features ...")
    df = engineer_features(df_raw)
    print(f"  Engineered: {df.shape[1]} columns")

    print("\n[3/6] Running clustering (SVD + KMeans, k=4) ...")
    df = run_clustering(df)
    cluster_dist = df["cluster"].value_counts().sort_index()
    for c, cnt in cluster_dist.items():
        print(f"  Cluster {c}: {cnt:5d} customers ({cnt/len(df)*100:.1f}%)")

    # 2. Load product catalog
    print("\n[4/6] Loading product catalog ...")
    products = load_product_catalog(CONFIG_DIR / "product_catalog.json")
    print(f"  Loaded: {len(products)} products")
    for p in products:
        print(f"    {p['product_id']}: {p['product_name']} ({p['product_type']})")

    # 3. Compute cluster profiles
    print("\n[5/6] Computing cluster Z-score profiles & scoring products ...")
    profile_z = compute_cluster_zscore_profile(df)

    cluster_scores = score_products_for_clusters(profile_z, products, SCORING_RULES)

    # 4. Build customer-product list
    print("\n[6/6] Building customer-product recommendation list ...")
    customer_product_list = build_customer_product_list(df, cluster_scores, products, top_n=5)

    # ── Save outputs ──
    print("\n" + "=" * 70)
    print("OUTPUTS")
    print("=" * 70)

    # Output 1: Cluster → Product scoring table
    score_path = OUTPUT_DIR / "cluster_product_scores.csv"
    cluster_scores.to_csv(score_path, index=False)
    print(f"  ✓ {score_path}  — cluster-product scores")

    # Output 2: Cluster summary
    summary = build_cluster_summary(df, cluster_scores, top_n=5)
    summary_path = OUTPUT_DIR / "cluster_summary.csv"
    summary.to_csv(summary_path, index=False)
    print(f"  ✓ {summary_path}  — cluster summary")

    # Output 3: Full customer-product list
    full_path = OUTPUT_DIR / "customer_product_recommendations.csv"
    customer_product_list.to_csv(full_path, index=False)
    print(f"  ✓ {full_path}  — {len(customer_product_list)} rows "
          f"({len(df)} customers × 5 products)")

    # Output 4: Customer sample per cluster
    sample_path = OUTPUT_DIR / "customer_sample_per_cluster.csv"
    sample_rows = []
    for cluster_id in sorted(df["cluster"].unique()):
        cluster_custs = df[df["cluster"] == cluster_id]["customer_id"].head(10)
        for cid in cluster_custs:
            sample_rows.append({"cluster": cluster_id, "customer_id": cid})
    pd.DataFrame(sample_rows).to_csv(sample_path, index=False)
    print(f"  ✓ {sample_path}  — 10 sample customers per cluster")

    # ── Print summary table ──
    print("\n" + "=" * 70)
    print("CLUSTER → PRODUCT MAPPING SUMMARY")
    print("=" * 70)
    print()
    for _, row in summary.iterrows():
        print(f"  {row['cluster_name']}")
        print(f"    Mô tả: {row['description']}")
        print(f"    Khách hàng: {row['customer_count']} ({row['customer_pct']})")
        print(f"    Sản phẩm phù hợp: {row['top_products']}")
        print(f"    VD khách hàng: {row['sample_customer_ids']}")
        print()

    # ── Print scoring details ──
    print("=" * 70)
    print("DETAILED PRODUCT SCORES PER CLUSTER")
    print("=" * 70)
    for cluster_id in sorted(cluster_scores["cluster"].unique()):
        print(f"\n  {CLUSTER_NAMES.get(cluster_id, f'Cluster {cluster_id}')}")
        cluster_data = cluster_scores[cluster_scores["cluster"] == cluster_id]
        for _, row in cluster_data.iterrows():
            bar = "█" * int(row["score"] * 50)
            print(f"    {row['product_id']} {row['product_name']:<25s} "
                  f"score={row['score']:.4f}  rank=#{row['rank']}  {bar}")

    print("\n✅ Done! All outputs saved to:", str(OUTPUT_DIR))
    return df, cluster_scores, customer_product_list


if __name__ == "__main__":
    main()
