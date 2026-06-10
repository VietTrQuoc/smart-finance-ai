# Báo cáo Phân tích Phân cụm Khách hàng (K-Means)

> **Ngày:** 04/06/2026  
> **Dữ liệu:** `customer_features.csv` — 4,869 khách hàng  
> **Loại tài liệu:** Experiment snapshot, không phải production config cố định  
> **Model version snapshot:** `seg_experiment_20260604_pc11_k4`  
> **Pipeline snapshot:** Feature Engineering → StandardScaler → TruncatedSVD (11 PCs, 81.31% variance) → K-Means (k=4)  
> **Notebook:** `SVD_and_clustering.ipynb` — `N_COMPONENTS=11`, `k_final=4`

---

## 0. Đồng bộ với notebook hiện tại

| Source | n_components | k | Vai trò |
|---|---:|---:|---|
| Report snapshot `seg_experiment_20260604_pc11_k4` | 11 | 4 | Run hiện tại, đồng bộ với notebook |
| Report cũ `seg_experiment_20260603_pc16_k5` | 16 | 5 | Run lịch sử để tham khảo |

Tài liệu này ghi nhận số liệu của run `pc11_k4`. Trong production, `n_components`, `k`, feature schema và tên cụm phải đi theo `model_version`, không lấy report này làm cấu hình cố định.

## 1. Pipeline Tổng quan

```
52 cột raw → Lọc còn 20 cột → StandardScaler → TruncatedSVD (11 PCs, 81.31% variance) → K-Means (k=4)
Snapshot: seg_experiment_20260604_pc11_k4
```

### 1.1 Loại bỏ feature (32 cột bị loại)

| Tiêu chí | Số cột | Chi tiết |
|---|---|---|
| ID | 1 | `customer_id` |
| Variance = 0 | 2 | `unique_countries`, `unique_currencies` |
| Trùng r=1.0 | 12 | `merchant_*` gốc, `mobile_ratio`, `online_ratio`, `distance_from_home_ratio`, ... |
| Trùng r ≥ 0.999 | 3 | `channel_ratio_web`, `category_entropy`, `recent_distance_from_home_ratio` |
| Raw amounts/counts | 7 | `total_amount`, `mean_amount`, `median_amount`, `max_amount`, `std_amount`, `unique_card_type_count`, `distance_from_home_count` |
| Redundant (tổng=1) | 2 | `merchant_category_ratio_Travel`, `card_type_ratio_premium` |

### 1.2 20 feature giữ lại

| Nhóm | Feature |
|---|---|
| **Merchant (7)** | `merchant_category_ratio_Education`, `_Entertainment`, `_Gas`, `_Grocery`, `_Healthcare`, `_Restaurant`, `_Retail` |
| **Channel (2)** | `channel_ratio_mobile`, `channel_ratio_pos` |
| **Card type (2)** | `card_type_ratio_basic`, `card_type_ratio_gold` |
| **Log amounts (3)** | `total_amount_log`, `mean_amount_log`, `max_amount_log` |
| **Behavior (4)** | `high_value_txn_ratio`, `foreign_txn_ratio`, `top_country_ratio`, `city_diversity_ratio` |
| **Diversity (1)** | `category_diversity` |
| **Other (1)** | `unique_cities` |

### 1.3 TruncatedSVD

| Components | Variance giữ lại |
|---|---|
| **11** | **81.31%** (đã chọn) |
| 14 | ~90.0% (ngưỡng 90%) |
| 16 | ~97.9% (ngưỡng gần 98%) |
| 20 | 100% (rank thực tế = 19, PC20 = 0) |

**Ý nghĩa các PC chính (11 components):**

| PC | Diễn giải |
|---|---|
| PC1 | **Quy mô**: `total_amount_log` (+0.54), `mean_amount_log` (+0.53), `high_value_txn_ratio` (+0.47) |
| PC2 | **Địa lý**: `top_country_ratio` (+0.57) vs `foreign_txn_ratio` (−0.54), `unique_cities` (−0.50) |
| PC3 | **Thẻ**: `card_type_ratio_basic` (+0.57) vs `card_type_ratio_gold` (−0.51), `max_amount_log` (−0.45) |
| PC4 | **Đa dạng**: `category_diversity` (+0.59) vs `city_diversity_ratio` (−0.55) |
| PC5 | **Ngành hàng**: `Healthcare`/`Education` vs `Grocery`/`Restaurant` |
| PC6 | **Retail & Education** vs `Entertainment`/`Gas`/`Grocery` |
| PC7 | **Gas & Entertainment** vs `Grocery`/`Healthcare` |
| PC8 | **Entertainment** vs `Gas` |
| PC9 | **Restaurant** vs `Retail`/`Grocery` |
| PC10 | **Education & Grocery** vs `Healthcare` |
| PC11 | **Mobile** (+0.85) vs `POS` (−0.47) — kênh giao dịch |

---

## 2. Chọn số cụm tối ưu

### 2.1 Elbow Method & Silhouette Analysis

| k | Inertia | Δ Inertia | Gain % | Silhouette |
|---|---|---|---|---|
| 2 | 68,306 | — | — | **0.190** |
| 3 | 62,252 | 6,054 | 8.9% | 0.115 |
| **4** | **58,366** | **3,886** | **6.2%** | **0.103** ✅ |
| 5 | 56,230 | 2,136 | 3.7% | 0.092 |
| 6 | 54,380 | 1,850 | 3.3% | 0.085 |
| 7 | 52,974 | 1,406 | 2.6% | 0.078 |
| 8 | 51,651 | 1,323 | 2.5% | 0.077 |

### 2.2 Phân bố kích thước cụm

| k | Cân bằng (min/max) | Nhận xét |
|---|---|---|
| 3 | 0.635 | Khá cân bằng |
| **4** | **0.591** | ✅ Tốt — không cụm nào <17% |
| 5 | 0.553 | Tốt |
| 6 | 0.430 | Có cụm quá nhỏ (9.6%) |

### 2.3 Kết luận chọn k

- **Knee point**: k=4 (Δ inertia = 3,886, gain 6.2%), k=5 giảm còn 3.7%
- k=2 cho silhouette cao nhất (0.190) nhưng không đủ chi tiết
- k=4 có silhouette (0.103) **cao hơn** k=5 (0.092) và k=6 (0.085)
- k=4 có cụm nhỏ nhất 846 khách (17.4%) **cân bằng hơn** k=5 (696 khách, 14.3%)
- **→ Chọn k=4:** knee point rõ ràng, silhouette cao nhất trong các k≥3, kích thước cụm cân bằng và đủ lớn để diễn giải kinh doanh. Silhouette 0.103 vẫn ở mức thấp–trung bình, nên dùng các cụm như phân khúc sơ bộ/heuristic.

---

## 3. Kết quả 4 cụm

### 3.1 Phân bố

| Cụm | Số lượng | Tỉ lệ | Tên gọi |
|---|---|---|---|
| 0 | 1,328 | 27.3% | 📱 Basic - Phổ thông |
| 1 | 1,432 | 29.4% | 🥇 Gold - Du lịch |
| 2 | 846 | 17.4% | 💎 Siêu VIP |
| 3 | 1,263 | 25.9% | 🏠 Đại chúng nội địa |

### 3.2 Đặc trưng từng cụm (Z-score)

| Feature | Cụm 0 📱 | Cụm 1 🥇 | Cụm 2 💎 | Cụm 3 🏠 |
|---|---|---|---|---|
| `card_type_ratio_basic` | 🔴 **+1.01** | 🟡 **−0.77** | −0.33 | +0.03 |
| `card_type_ratio_gold` | −0.49 | 🟡 **+0.48** | +0.06 | −0.08 |
| `total_amount_log` | 🟡 **−0.55** | −0.02 | 🔴 **+1.69** | 🟡 **−0.53** |
| `mean_amount_log` | 🟡 **−0.58** | −0.13 | 🔴 **+1.80** | −0.45 |
| `max_amount_log` | 🟡 **−0.81** | 🟡 **+0.64** | +0.29 | −0.07 |
| `high_value_txn_ratio` | −0.39 | −0.36 | 🔴 **+1.93** | −0.47 |
| `foreign_txn_ratio` | 🟡 **+0.56** | 🟡 **+0.59** | −0.39 | 🔴 **−1.00** |
| `top_country_ratio` | −0.43 | 🟡 **−0.58** | +0.31 | 🟡 **+0.90** |
| `unique_cities` | +0.40 | 🟡 **+0.50** | −0.12 | 🟡 **−0.91** |

### 3.3 Diễn giải

- **📱 Cụm 0 — Basic Phổ thông (1,328 khách, 27.3%):** 89% basic card, chi tiêu thấp (~41M), max GD thấp nhất (~2.0M), có giao dịch nước ngoài (36%), phân tán quốc gia
- **🥇 Cụm 1 — Gold Du lịch (1,432 khách, 29.4%):** 38% gold card, max GD cao nhất (~4.1M), hay đi nước ngoài (36%), nhiều thành phố, phân tán quốc gia
- **💎 Cụm 2 — Siêu VIP (846 khách, 17.4%):** Tổng chi tiêu ~199M (gấp 3-5 lần), GD TB ~127K, 73% high-value, 23% basic + 21% gold
- **🏠 Cụm 3 — Đại chúng nội địa (1,263 khách, 25.9%):** Nước ngoài thấp nhất (26%), tập trung 1 quốc gia (74%), ít thành phố nhất, chi tiêu thấp (~41M)

---

## 4. Đánh giá chất lượng cụm (k=4)

### 4.1 Silhouette từng cụm

| Cụm | Silhouette | Negative % | Đánh giá |
|---|---|---|---|
| 2 💎 Siêu VIP | **0.135** | 9.9% | Tốt nhất — nhóm VIP tách biệt khá rõ |
| 1 🥇 Gold DL | **0.114** | 0.0% | Tốt — không có điểm nào bị gán sai |
| 0 📱 Basic PT | **0.106** | 0.5% | Khả dụng |
| 3 🏠 Nội địa | **0.066** | 16.6% | Yếu — dễ chồng lấn với các cụm khác |

> Cụm 3 (Nội địa) có **16.6% điểm silhouette âm**, tín hiệu chồng lấn đáng kể. Nên cân nhắc gom với cụm khác hoặc dùng thêm feature bổ trợ. Các cụm còn lại có chất lượng khả dụng.

### 4.2 Khoảng cách giữa các tâm cụm

| | Cụm 0 📱 | Cụm 1 🥇 | Cụm 2 💎 | Cụm 3 🏠 |
|---|---|---|---|---|
| **Cụm 0 📱** | — | **2.60** | 4.59 | 2.75 |
| **Cụm 1 🥇** | **2.60** | — | 3.80 | 2.98 |
| **Cụm 2 💎** | 4.59 | 3.80 | — | 4.17 |
| **Cụm 3 🏠** | 2.75 | 2.98 | 4.17 | — |

- **Cặp gần nhất**: Cụm 0 ↔ Cụm 1 (2.60) — Basic PT gần Gold Du lịch (cùng có foreign_txn cao)
- **Cặp xa nhất**: Cụm 0 ↔ Cụm 2 (4.59) — Basic PT cách biệt hoàn toàn với Siêu VIP
- **Tỉ lệ min/max = 0.57** → các cụm phân bố khá đều

### 4.3 Top feature phân biệt cụm mạnh nhất

1. `high_value_txn_ratio` — tỉ lệ giao dịch giá trị cao (phân biệt VIP)
2. `card_type_ratio_basic` — loại thẻ basic (phân biệt Basic PT)
3. `total_amount_log` / `mean_amount_log` — quy mô chi tiêu (phân biệt VIP)
4. `foreign_txn_ratio` — tỉ lệ giao dịch nước ngoài (phân biệt Nội địa)
5. `top_country_ratio` — mức độ tập trung địa lý (phân biệt Nội địa)
6. `max_amount_log` — giao dịch lớn nhất (phân biệt Gold DL vs Basic PT)
7. `unique_cities` — số thành phố giao dịch (phân biệt Nội địa)
8. *(các merchant ratio ít phân biệt hơn — phân phối khá đều giữa các cụm)*

---

## 5. Số liệu kinh doanh (k=4)

| Cụm | SL | Tổng chi tiêu TB | GD TB | GD max TB | % High-value | % Nước ngoài | % Basic | % Gold |
|---|---|---|---|---|---|---|---|---|
| 📱 **Basic PT** | 1,328 | 41,295,807 | 27,302 | 2,025,581 | 15% | 36% | **89%** | 0% |
| 🥇 **Gold DL** | 1,432 | 58,198,057 | 35,435 | **4,130,637** | 16% | 36% | 2% | **38%** |
| 💎 **Siêu VIP** | 846 | **198,788,007** | **127,259** | 3,585,943 | **73%** | 30% | 23% | 21% |
| 🏠 **Nội địa** | 1,263 | 41,410,944 | 29,316 | 3,036,911 | 13% | **26%** | 41% | 16% |

---

## 6. Kết luận & Khuyến nghị

### Điểm mạnh
- ✅ **k=4 là lựa chọn hợp lý:** knee point rõ ràng, silhouette cao nhất trong các k≥3 (0.103), kích thước cụm cân bằng
- ✅ Cụm Siêu VIP (cụm 2) nổi bật với Z-score >1.5 trên total_amount_log, mean_amount_log, high_value_txn_ratio — dễ ưu tiên trong chiến dịch
- ✅ Phân khúc theo loại thẻ (basic/gold) và geography (nội địa/quốc tế) là hai trục diễn giải rõ nhất
- ✅ Cụm 1 (Gold DL) có 0% negative silhouette — phân khúc ổn định nhất

### Điểm yếu
- ⚠️ Cụm 3 (Nội địa) có 16.6% negative silhouette — chồng lấn đáng kể, cần feature bổ trợ
- ⚠️ Silhouette tổng thể 0.103 vẫn thấp — phân cụm phù hợp làm segment sơ bộ, không nên coi là ranh giới cứng
- ⚠️ Merchant ratios không phân biệt tốt giữa các cụm (Z-score đều gần 0)

### Khuyến nghị hành động
1. **💎 Cụm 2 (Siêu VIP):** Chăm sóc đặc biệt, loyalty program, personal banking — ưu tiên cao nhất
2. **🥇 Cụm 1 (Gold DL):** Cross-sell bảo hiểm du lịch, FX card, ưu đãi ngoại tệ — phân khúc du lịch rõ ràng
3. **📱 Cụm 0 (Basic PT):** Digital banking, upsell từ Basic lên Gold — phân khúc lớn, foreign cao
4. **🏠 Cụm 3 (Nội địa):** Duy trì, digital banking cơ bản + cashback nhỏ — tín hiệu yếu, không ưu tiên cao

---

## 7. Ánh xạ Cụm → Sản phẩm Tài chính

> **Phương pháp:** Mỗi sản phẩm được gán điểm heuristic dựa trên Z-score của các feature liên quan trong cluster profile. Score dùng để xếp hạng tương đối trong cùng cụm, không phải xác suất mua.

### 7.1 Quy tắc ánh xạ

| Hành vi trong dữ liệu | Sản phẩm gợi ý | Feature tín hiệu |
|---|---|---|
| Nhiều quốc gia, `foreign_txn` cao | FX Card, Thẻ du lịch, Bảo hiểm du lịch | `foreign_txn_ratio`, `unique_cities`, `−top_country_ratio` |
| Giao dịch giá trị cao, `max_amount` cao | Trả góp/BNPL, Thẻ tín dụng cao cấp | `max_amount_log`, `high_value_txn_ratio`, `mean_amount_log` |
| Tổng chi tiêu cao, đã dùng Gold | Thẻ tín dụng cao cấp, Vay nhanh | `total_amount_log`, `card_type_ratio_gold`, `high_value_txn_ratio` |
| Online/mobile nhiều, basic card | Ngân hàng số, Voucher TMĐT | `channel_ratio_mobile`, `−channel_ratio_pos`, `card_type_ratio_basic` |
| Chi tiêu nhiều Retail, Grocery | Thẻ hoàn tiền, Voucher/Cashback | `merchant_category_ratio_Retail`, `merchant_category_ratio_Grocery` |
| Entertainment, giải trí nhiều | Voucher giải trí, Cashback lifestyle | `merchant_category_ratio_Entertainment` |

### 7.2 Kết quả theo cụm

#### 💎 Cụm 2 — Siêu VIP (846 khách, 17.4%) — ĐIỂM CAO VƯỢT TRỘI

| # | Sản phẩm | Score | Mức độ |
|---|---|---|---|
| 1 | **Vay nhanh / Hạn mức ngắn hạn** | ⭐ **+5.42** | Rất mạnh |
| 2 | **Trả góp / BNPL** | ⭐ **+4.02** | Rất mạnh |
| 3 | **Thẻ tín dụng cao cấp** | ⭐ **+3.68** | Rất mạnh |
| 4 | **Bảo hiểm thiết bị** | ⭐ **+2.22** | Mạnh |

> 💡 VIP là phân khúc **sinh lời nhất** — phù hợp với mọi sản phẩm cao cấp. Score gấp 3-5 lần các cụm khác. Ưu tiên tiếp cận nhóm này trước.

---

#### 🥇 Cụm 1 — Gold Du lịch (1,432 khách, 29.4%)

| # | Sản phẩm | Score | Mức độ |
|---|---|---|---|
| 1 | **FX Card (ngoại tệ)** | ★ **+1.67** | Mạnh |
| 2 | **Thẻ du lịch (Travel Card)** | ★ **+1.67** | Mạnh |
| 3 | **Bảo hiểm du lịch** | ★ **+1.67** | Mạnh |
| 4 | Bảo hiểm thiết bị | · +0.53 | Trung bình |

> 💡 Phân khúc du lịch/công tác quốc tế rõ ràng — `foreign_txn_ratio` cao, `top_country_ratio` thấp, nhiều thành phố. Ưu tiên cross-sell bộ 3 sản phẩm du lịch.

---

#### 📱 Cụm 0 — Basic Phổ thông (1,328 khách, 27.3%)

| # | Sản phẩm | Score | Mức độ |
|---|---|---|---|
| 1 | **FX Card (ngoại tệ)** | ★ **+1.39** | Mạnh |
| 2 | **Thẻ du lịch (Travel Card)** | ★ **+1.39** | Mạnh |
| 3 | **Bảo hiểm du lịch** | ★ **+1.39** | Mạnh |
| 4 | **Ngân hàng số (Digital Banking)** | ★ **+1.01** | Mạnh |

> 💡 89% basic card, foreign cao (36%), phân tán quốc gia. Digital banking là entry point, sau đó cross-sell thẻ du lịch cơ bản. Tiềm năng upsell từ Basic lên Gold.

---

#### 🏠 Cụm 3 — Đại chúng nội địa (1,263 khách, 25.9%)

| # | Sản phẩm | Score | Mức độ |
|---|---|---|---|
| 1 | Ngân hàng số (Digital Banking) | · +0.03 | Rất yếu |
| 2 | Thẻ hoàn tiền (Cashback) | · +0.02 | Rất yếu |
| 3 | Voucher/Cashback TMĐT | · +0.01 | Rất yếu |
| 4 | Voucher giải trí / Lifestyle | · −0.02 | Không phù hợp |

> ⚠️ **Tín hiệu yếu nhất** — khách nội địa, ít chi tiêu, ít thành phố, `foreign_txn` thấp nhất. Khó cross-sell. Nên tập trung vào digital banking cơ bản + cashback nhỏ, không đầu tư nhiều nguồn lực. Cân nhắc gom với cụm khác nếu cần đơn giản hóa chiến lược.

---

### 7.3 Tổng hợp chiến lược theo mức độ ưu tiên

| Ưu tiên | Cụm | SL | Chiến lược | Sản phẩm chính |
|---|---|---|---|---|
| 🔴 **Cực cao** | 💎 Siêu VIP | 846 | All-in, cá nhân hóa | Vay nhanh, BNPL, thẻ cao cấp, bảo hiểm |
| 🟠 **Cao** | 🥇 Gold DL | 1,432 | Cross-sell du lịch | FX Card, bảo hiểm DL, thẻ DL |
| 🟡 **Vừa** | 📱 Basic PT | 1,328 | Entry-level + upsell | Digital banking, thẻ DL cơ bản → upsell Gold |
| ⚪ **Thấp** | 🏠 Nội địa | 1,263 | Duy trì, không ưu tiên | Digital banking, cashback nhỏ |

### 7.4 Hạn chế

- ⚠️ **Merchant-based products** (thẻ hoàn tiền, voucher siêu thị, cashback grocery) **không phân biệt tốt** vì tỉ lệ chi tiêu theo ngành hàng (`merchant_category_ratio_*`) gần như đều nhau giữa các cụm. Đây là hạn chế của dữ liệu hiện tại.
- ⚠️ Không có dữ liệu về `velocity` (tần suất giao dịch/giờ) và `device`/`electronics` riêng biệt ở mức customer-level, nên chưa đánh giá được hết tiềm năng vay nhanh và bảo hiểm thiết bị.
- ⚠️ Score sản phẩm hiện vẫn là rule-based heuristic. Trước khi gọi LLM pitching theo kế hoạch, cần kết hợp thêm `fraud_score`, `risk_score`, `product_catalog` và lead score để lọc sản phẩm được phép chào.
- ⚠️ Cụm 3 (Nội địa) có 16.6% điểm silhouette âm — ranh giới cụm không rõ ràng, có thể cần thêm feature hoặc merge với cụm lân cận.

---

## 8. Production policy: versioning & no hard-code

- Report này là một snapshot phân tích, không phải cấu hình vận hành cố định.
- Trong production, `n_components`, `k`, feature schema, artifact paths và metrics được lưu trong `segmentation_model_versions`.
- `cluster_id` chỉ có ý nghĩa ổn định trong cùng một `model_version`. Sau full retrain, cụm mới phải được so khớp với cụm cũ bằng centroid/profile similarity trước khi hiển thị như cùng một phân khúc.
- Không hard-code `cluster_names` theo số cụm toàn hệ thống. Tên, mô tả, size, ratio, top features và product hints phải đọc từ `cluster_profiles` theo `model_version`.
- PC/K chọn bằng metrics: explained variance, elbow/inertia, silhouette, balance, stability và min cluster size. LLM chỉ giải thích trade-off hoặc chọn trong shortlist đã hợp lệ, không tự quyết từ raw data.
- LLM Segment Profiler chỉ nhận aggregate profile/top z-score/metrics của cụm; không gửi raw transaction, PII, card number, IP, device fingerprint hoặc dữ liệu định danh trực tiếp.
- Run hiện tại là `seg_experiment_20260604_pc11_k4`. Run cũ `seg_experiment_20260603_pc16_k5` được lưu làm lịch sử tham khảo.
