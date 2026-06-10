# Product Catalog Documentation

> **File:** `configs/product_catalog.json`  
> **Version:** v2.0 — 15 sản phẩm  
> **Ngày:** 09/06/2026  
> **Mục đích:** Source of truth cho toàn bộ sản phẩm tài chính được phép tiếp thị trong hệ thống Recommendation Engine.

---

## 1. Tổng quan

Product catalog gồm **15 sản phẩm** thuộc **7 nhóm**:

| Nhóm | Số lượng | Sản phẩm |
|---|---|---|
| Credit Card | 2 | P001, P007 |
| Insurance | 5 | P002, P006, P008, P015 |
| Loan | 4 | P003, P004, P009, P010 |
| Saving | 2 | P005, P011 |
| Investment | 1 | P012 |
| Pension | 1 | P013 |
| Service | 1 | P014 |

---

## 2. Chi tiết từng sản phẩm

### 2.1 Nhóm Credit Card (Thẻ tín dụng)

#### P001 — Cashback Credit Card

| Thuộc tính | Giá trị |
|---|---|
| Loại | credit_card |
| Rủi ro | medium |
| Hành vi mục tiêu | shopping_high |
| Ưu tiên chiến dịch | 0.80 |

**Lý do có sản phẩm này:**
- Phục vụ khách hàng có hành vi mua sắm thường xuyên (`shopping_ratio` cao).
- Đặc biệt phù hợp với **Siêu VIP** (tổng chi tiêu ~199M, cashback giá trị lớn) và **Basic PT** (89% basic card → upgrade lên thẻ có rewards).
- Là sản phẩm tín dụng entry-level, rủi ro trung bình, dễ tiếp thị.

---

#### P007 — Premium Travel Card

| Thuộc tính | Giá trị |
|---|---|
| Loại | credit_card |
| Rủi ro | medium |
| Hành vi mục tiêu | travel_premium |
| Ưu tiên chiến dịch | 0.82 |

**Lý do có sản phẩm này:**
- Khác biệt với P001: nhắm đến phân khúc **du lịch cao cấp** (`foreign_txn_ratio` cao, `avg_transaction_amount` cao).
- Phù hợp với **Gold DL** (38% gold card, max GD ~4.1M, foreign 36%) và **Siêu VIP** (chi tiêu cao, đi lại nhiều).
- Perks: lounge access, miễn phí giao dịch nước ngoài — giá trị khác biệt rõ với cashback card thông thường.

---

### 2.2 Nhóm Insurance (Bảo hiểm)

#### P002 — Travel Insurance

| Thuộc tính | Giá trị |
|---|---|
| Loại | insurance |
| Rủi ro | low |
| Hành vi mục tiêu | travel_high |
| Ưu tiên chiến dịch | 0.85 |

**Lý do có sản phẩm này:**
- Sản phẩm bảo hiểm có **độ ưu tiên cao nhất** (0.85) do tỉ lệ chấp nhận cao ở nhóm khách du lịch.
- Phù hợp nhất với **Gold DL** (foreign_txn_ratio Z=+0.59) — đây là cross-sell tự nhiên nhất.
- Rủi ro thấp, dễ phê duyệt, doanh thu ổn định từ phí bảo hiểm định kỳ.

---

#### P006 — Health Insurance

| Thuộc tính | Giá trị |
|---|---|
| Loại | insurance |
| Rủi ro | low |
| Hành vi mục tiêu | healthcare_high |
| Ưu tiên chiến dịch | 0.75 |

**Lý do có sản phẩm này:**
- Phục vụ khách hàng có chi tiêu y tế (`healthcare_ratio` cao).
- Phù hợp rộng: **Nội địa** (bảo vệ sức khỏe trong nước), **Gold DL** (bảo hiểm du lịch kèm sức khỏe), **Siêu VIP** (gói premium).
- Sản phẩm thiết yếu, nhu cầu phổ quát, rủi ro thấp.

---

#### P008 — Life Insurance

| Thuộc tính | Giá trị |
|---|---|
| Loại | insurance |
| Rủi ro | low |
| Hành vi mục tiêu | family_stable |
| Ưu tiên chiến dịch | 0.65 |

**Lý do có sản phẩm này:**
- Nhắm đến khách hàng **ổn định, gắn bó lâu dài** (`top_country_ratio` cao — tập trung trong nước, ít di chuyển).
- Phù hợp với **Nội địa** (74% tập trung 1 quốc gia → có gia đình, định cư) và **VIP** (bảo vệ tài sản lớn).
- Sản phẩm tài chính dài hạn, tạo quan hệ khách hàng bền vững.

---

#### P015 — Personal Accident Insurance

| Thuộc tính | Giá trị |
|---|---|
| Loại | insurance |
| Rủi ro | low |
| Hành vi mục tiêu | general_protection |
| Ưu tiên chiến dịch | 0.55 |

**Lý do có sản phẩm này:**
- Sản phẩm **phổ quát**, phù hợp mọi phân khúc — không yêu cầu hành vi đặc thù.
- Đặc biệt phù hợp **Basic PT** (cần bảo vệ cơ bản, chi phí thấp) và **Nội địa**.
- Rủi ro thấp nhất, là "sản phẩm mồi" để bắt đầu quan hệ cross-sell.
- Đóng vai trò fallback khi các sản phẩm khác không khớp.

---

### 2.3 Nhóm Loan (Khoản vay)

#### P003 — Consumer Loan

| Thuộc tính | Giá trị |
|---|---|
| Loại | loan |
| Rủi ro | medium |
| Hành vi mục tiêu | negative_cashflow |
| Ưu tiên chiến dịch | 0.65 |

**Lý do có sản phẩm này:**
- Phục vụ khách hàng có **áp lực chi tiêu ngắn hạn** (`negative_cashflow_days` cao, `net_cashflow_30d` thấp).
- Phù hợp **Nội địa** và **Basic PT** — nhóm chi tiêu thấp, thỉnh thoảng thiếu hụt.
- Khoản vay nhỏ, thời gian ngắn, rủi ro được kiểm soát qua `max_risk_score=0.55`.

---

#### P004 — Overdraft Loan

| Thuộc tính | Giá trị |
|---|---|
| Loại | loan |
| Rủi ro | medium |
| Hành vi mục tiêu | end_month_cash_shortage |
| Ưu tiên chiến dịch | 0.60 |

**Lý do có sản phẩm này:**
- Thiết kế riêng cho khách hàng có **áp lực cuối tháng** (`end_month_negative_cashflow_flag`).
- Phù hợp nhất **Basic PT** (89% basic card, quản lý chi tiêu chưa tối ưu → dễ thiếu hụt cuối tháng).
- Lãi suất thấu chi thường cao hơn consumer loan → biên lợi nhuận tốt cho ngân hàng.

---

#### P009 — Home Loan

| Thuộc tính | Giá trị |
|---|---|
| Loại | loan |
| Rủi ro | medium |
| Hành vi mục tiêu | domestic_settled |
| Ưu tiên chiến dịch | 0.55 |

**Lý do có sản phẩm này:**
- Sản phẩm **cho vay thế chấp** — nhắm đến khách hàng **định cư trong nước** (`top_country_ratio` cao, `unique_cities` thấp).
- Phù hợp nhất **Nội địa** (74% tập trung 1 quốc gia, ít di chuyển → sẵn sàng mua nhà).
- Giá trị khoản vay lớn, thời gian dài → doanh thu bền vững cho ngân hàng.
- Cần `min_frequency_90d=15` để đảm bảo khách hàng có lịch sử giao dịch đủ dài.

---

#### P010 — Auto Loan

| Thuộc tính | Giá trị |
|---|---|
| Loại | loan |
| Rủi ro | medium |
| Hành vi mục tiêu | domestic_transport |
| Ưu tiên chiến dịch | 0.58 |

**Lý do có sản phẩm này:**
- Nhắm đến khách hàng có **chi tiêu vận tải trong nước** (`merchant_category_ratio_Gas` cao).
- Phù hợp **Nội địa** (di chuyển nội địa, chi tiêu xăng dầu) và **Basic PT** (cần phương tiện cá nhân).
- Khoản vay trung bình, tài sản đảm bảo là xe → rủi ro thấp hơn consumer loan không thế chấp.

---

### 2.4 Nhóm Saving (Tiết kiệm)

#### P005 — Flexible Savings

| Thuộc tính | Giá trị |
|---|---|
| Loại | saving |
| Rủi ro | low |
| Hành vi mục tiêu | positive_cashflow |
| Ưu tiên chiến dịch | 0.70 |

**Lý do có sản phẩm này:**
- Sản phẩm tiết kiệm **linh hoạt**, không kỳ hạn — phù hợp mọi phân khúc.
- Đặc biệt phù hợp **Nội địa** (ổn định, tập trung), **VIP** (quản lý tài sản thanh khoản), **Basic PT** (bắt đầu tiết kiệm).
- Rủi ro thấp nhất, là "cửa ngõ" để khách hàng làm quen với sản phẩm tài chính.

---

#### P011 — Fixed Deposit

| Thuộc tính | Giá trị |
|---|---|
| Loại | saving |
| Rủi ro | low |
| Hành vi mục tiêu | conservative_saving |
| Ưu tiên chiến dịch | 0.68 |

**Lý do có sản phẩm này:**
- Sản phẩm tiết kiệm **có kỳ hạn, lãi suất cố định** — dành cho khách hàng **bảo thủ**, thích an toàn.
- Phù hợp nhất **Nội địa** (tập trung 1 quốc gia, ổn định → sẵn sàng gửi tiết kiệm dài hạn).
- Khác biệt với P005: lãi suất cao hơn nhưng không rút được trước hạn → phù hợp khách có tiền nhàn rỗi.
- Giúp ngân hàng huy động vốn trung-dài hạn ổn định.

---

### 2.5 Nhóm Investment (Đầu tư)

#### P012 — Investment Fund

| Thuộc tính | Giá trị |
|---|---|
| Loại | investment |
| Rủi ro | high |
| Hành vi mục tiêu | wealth_growth |
| Ưu tiên chiến dịch | 0.72 |

**Lý do có sản phẩm này:**
- Sản phẩm **đầu tư có quản lý** — dành riêng cho khách hàng **giá trị ròng cao**.
- Phù hợp **độc quyền** cho **Siêu VIP** (`total_amount_log` Z=+1.69, `high_value_txn_ratio` Z=+1.93).
- Là sản phẩm duy nhất có `risk_allowed=high` — cần khách hàng chấp nhận rủi ro.
- Biên lợi nhuận cao nhất cho ngân hàng (phí quản lý quỹ).

---

### 2.6 Nhóm Pension (Hưu trí)

#### P013 — Retirement Pension Plan

| Thuộc tính | Giá trị |
|---|---|
| Loại | pension |
| Rủi ro | low |
| Hành vi mục tiêu | long_term_saving |
| Ưu tiên chiến dịch | 0.60 |

**Lý do có sản phẩm này:**
- Sản phẩm **hưu trí dài hạn** — nhắm đến khách hàng có lịch sử giao dịch lâu dài (`min_frequency_90d=20`).
- Phù hợp **Gold DL** (thu nhập khá, max GD cao → có khả năng đóng góp hưu trí) và **VIP** (tối ưu thuế, bảo vệ tương lai).
- Tạo quan hệ khách hàng 10-30 năm → giá trị vòng đời khách hàng (LTV) rất cao.

---

### 2.7 Nhóm Service (Dịch vụ)

#### P014 — Bill Payment Service

| Thuộc tính | Giá trị |
|---|---|
| Loại | service |
| Rủi ro | low |
| Hành vi mục tiêu | domestic_utility |
| Ưu tiên chiến dịch | 0.50 |

**Lý do có sản phẩm này:**
- Dịch vụ **thanh toán hóa đơn tự động** — tiện ích cơ bản cho khách hàng nội địa.
- Phù hợp **Nội địa** và **Basic PT** — nhóm có giao dịch recurring (tiện ích, grocery).
- Không tạo doanh thu trực tiếp cao, nhưng **tăng stickiness** (khách hàng khó rời bỏ ngân hàng).
- Là "sản phẩm neo" — một khi khách dùng bill payment, họ sẽ duy trì tài khoản.

---

## 3. Nguyên tắc thiết kế catalog

### 3.1 Đa dạng hóa rủi ro

| Mức rủi ro | Số SP | Sản phẩm |
|---|---|---|
| **low** | 9 | P002, P005, P006, P008, P011, P013, P014, P015 |
| **medium** | 5 | P001, P003, P004, P007, P009, P010 |
| **high** | 1 | P012 |

- Phần lớn sản phẩm (9/15) có rủi ro thấp → an toàn cho ngân hàng, dễ phê duyệt.
- Chỉ 1 sản phẩm rủi ro cao (P012 Investment Fund) — dành riêng cho phân khúc VIP đã được xác minh.

### 3.2 Phủ đủ 4 phân khúc khách hàng

Mỗi cụm đều có ít nhất 5 sản phẩm phù hợp (score > 0). Không cụm nào bị bỏ trống.

### 3.3 Phủ đủ vòng đời tài chính

```
Giai đoạn 1 (Trẻ, mới đi làm)
  → P014 Bill Payment, P015 Accident Insurance, P005 Flexible Savings

Giai đoạn 2 (Ổn định, có gia đình)
  → P009 Home Loan, P010 Auto Loan, P008 Life Insurance, P006 Health Insurance

Giai đoạn 3 (Tích lũy, thu nhập cao)
  → P001 Cashback Card, P007 Premium Travel Card, P011 Fixed Deposit, P012 Investment Fund

Giai đoạn 4 (Hưu trí)
  → P013 Retirement Pension Plan
```

### 3.4 Có sản phẩm "mồi" (entry product)

- **P014 Bill Payment Service** và **P015 Personal Accident Insurance** là các sản phẩm rủi ro thấp, chi phí thấp, dễ tiếp cận → dùng để bắt đầu quan hệ cross-sell.
- Sau khi khách hàng dùng sản phẩm mồi, hệ thống sẽ gợi ý các sản phẩm giá trị cao hơn.

### 3.5 Có sản phẩm "neo" (sticky product)

- **P014 Bill Payment**, **P005 Flexible Savings**, **P013 Retirement Pension** — một khi khách hàng đăng ký, chi phí chuyển đổi cao → giữ chân khách hàng lâu dài.

---

## 4. Cách scoring hoạt động

Script `src/recommendation/cluster_product_mapping.py` sử dụng **rule-based scoring**:

```
Với mỗi rule (product_id, cluster_id, feature, operator, threshold, weight):
  Nếu cluster_z thỏa mãn operator so với threshold:
    score += weight × |cluster_z - threshold|
```

Điểm số phản ánh **mức độ phù hợp** giữa đặc trưng của cụm và hành vi mục tiêu của sản phẩm.

---

## 5. Cập nhật catalog

Khi thêm/sửa/xóa sản phẩm:

1. Cập nhật `configs/product_catalog.json`.
2. Thêm scoring rules tương ứng vào `SCORING_RULES` trong `src/recommendation/cluster_product_mapping.py`.
3. Chạy lại script: `python -m src.recommendation.cluster_product_mapping`.
4. Kiểm tra `output/cluster_summary.csv` để xác nhận mapping hợp lý.
5. Cập nhật file `.md` này.
