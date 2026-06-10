---
marp: true
theme: default
paginate: true
---

# Product Catalog

## Danh mục sản phẩm cho hệ thống gợi ý tài chính

Mục tiêu: giúp hệ thống chọn đúng sản phẩm cho từng khách hàng dựa trên hành vi, rủi ro và chiến dịch.

---

# 1. Product Catalog là gì?

Product Catalog là nơi lưu toàn bộ sản phẩm có thể được hệ thống gợi ý cho khách hàng.

Nói đơn giản:

- Có những sản phẩm nào?
- Sản phẩm đó dành cho ai?
- Rủi ro của sản phẩm là thấp, trung bình hay cao?
- Khi nào được phép gợi ý sản phẩm đó?

---

# 2. Catalog hiện có gì?

Hiện catalog có **15 sản phẩm** thuộc **7 nhóm**.

| Nhóm | Số sản phẩm | Ví dụ |
|---|---:|---|
| Credit Card | 2 | Cashback Card, Premium Travel Card |
| Insurance | 4 | Travel, Health, Life, Accident |
| Loan | 4 | Consumer, Overdraft, Home, Auto |
| Saving | 2 | Flexible Savings, Fixed Deposit |
| Investment | 1 | Investment Fund |
| Pension | 1 | Retirement Plan |
| Service | 1 | Bill Payment |

---

# 3. Vì sao cần catalog?

Nếu không có catalog, hệ thống chỉ biết khách hàng có hành vi gì, nhưng không biết nên gợi ý sản phẩm nào.

Catalog đóng vai trò như "luật kinh doanh":

- Khách hay mua sắm -> thẻ cashback.
- Khách hay du lịch -> bảo hiểm du lịch hoặc thẻ travel.
- Khách có áp lực dòng tiền -> khoản vay phù hợp.
- Khách rủi ro cao -> không gợi ý sản phẩm rủi ro.

---

# 4. Mỗi sản phẩm gồm những thông tin chính

| Trường | Ý nghĩa |
|---|---|
| `product_id` | Mã sản phẩm |
| `product_name` | Tên sản phẩm |
| `product_type` | Nhóm sản phẩm |
| `risk_allowed` | Mức rủi ro cho phép |
| `target_behavior` | Hành vi khách hàng mục tiêu |
| `target_signals_json` | Feature dùng để chấm điểm phù hợp |
| `eligibility_json` | Điều kiện được gợi ý |
| `campaign_priority` | Ưu tiên chiến dịch |

---

# 5. Ví dụ dễ hiểu

## P002 - Travel Insurance

Phù hợp với khách hàng:

- Có tỷ lệ chi tiêu du lịch cao.
- Có giao dịch liên quan du lịch trong 90 ngày.
- Có rủi ro thấp hoặc đang ở mức cho phép.

Vì đây là sản phẩm `risk_allowed = low`, nên vẫn có thể gợi ý cho khách hàng đang ở trạng thái review nhẹ.

---

# 6. Cách hệ thống chọn sản phẩm

Luồng đơn giản:

```text
User features
  -> kiểm tra fraud/risk
  -> lọc sản phẩm không đủ điều kiện
  -> tính điểm từng sản phẩm
  -> sắp xếp theo điểm
  -> lấy Top 3
```

Kết quả cuối cùng không phải "một cụm khách hàng = một sản phẩm", mà là chấm điểm từng khách hàng với từng sản phẩm.

---

# 7. Công thức điểm gợi ý

Điểm sản phẩm được tính từ 5 phần:

| Thành phần | Vai trò |
|---|---|
| Behavior match | Hành vi khách có khớp sản phẩm không |
| Segment affinity | Cụm khách hàng có hợp sản phẩm không |
| Affordability fit | Khả năng chi trả và mức rủi ro |
| Timing need | Nhu cầu gần đây có xuất hiện không |
| Campaign priority | Ưu tiên kinh doanh |

---

# 8. Guardrail rủi ro

Hệ thống không gợi ý bừa. Fraud score là cổng chặn trước khi recommend.

| Fraud score | Hành động |
|---|---|
| `< 0.3` | Gợi ý đầy đủ sản phẩm đủ điều kiện |
| `0.3 - 0.7` | Chỉ giữ sản phẩm rủi ro thấp |
| `>= 0.7` | Không gợi ý sản phẩm nào |

Điều này giúp Recommendation không làm tăng rủi ro vận hành.

---

# 9. Các nhóm sản phẩm theo rủi ro

| Mức rủi ro | Số sản phẩm | Ý nghĩa |
|---|---:|---|
| Low | 8 | Dễ gợi ý, an toàn, phù hợp nhiều khách |
| Medium | 6 | Cần kiểm tra điều kiện và risk score |
| High | 1 | Chỉ dành cho khách phù hợp, rủi ro thấp |

Ví dụ:

- Low: bảo hiểm, tiết kiệm, bill payment.
- Medium: thẻ tín dụng, khoản vay.
- High: investment fund.

---

# 10. Cách cập nhật catalog

Khi thêm hoặc sửa sản phẩm:

1. Cập nhật `configs/product_catalog.json`.
2. Kiểm tra `target_behavior` và `target_signals_json`.
3. Kiểm tra điều kiện trong `eligibility_json`.
4. Chạy lại DB seed nếu cần:

```powershell
.\.venv\Scripts\python.exe -m src.db.init_db --db data\smart_finance.db --recreate
```

5. Kiểm tra dashboard Recommendation.

---

# Kết luận

Product Catalog là cầu nối giữa dữ liệu hành vi khách hàng và quyết định gợi ý sản phẩm.

Nó giúp hệ thống:

- Gợi ý đúng sản phẩm.
- Có lý do giải thích rõ ràng.
- Tuân thủ fraud/risk policy.
- Dễ mở rộng khi ngân hàng thêm sản phẩm mới.
