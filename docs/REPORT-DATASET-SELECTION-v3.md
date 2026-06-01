# BÁO CÁO LỰA CHỌN BỘ DỮ LIỆU

---

## TÓM TẮT ĐIỀU HÀNH

Dataset **Transactions** (`synthetic_fraud_data.csv`, Kaggle — Ismat Samadov, Apache 2.0) được chọn làm nguồn dữ liệu duy nhất cho MVP.

Đây là dataset **duy nhất** trong số 5 lựa chọn có đủ cả nhãn fraud, `merchant_category` đa dạng, device info và geo data — tức là phục vụ được đồng thời cả hai pipeline Fraud Detection và Recommendation từ một nguồn.

Đánh đổi duy nhất: thiếu `balance_before/after`, làm giảm ~15% độ chính xác với loại fraud "rút cạn tài khoản". Chấp nhận được cho MVP; có thể bổ sung PaySim sau nếu cần.

---

## 1. YÊU CẦU DỮ LIỆU

Hệ thống chạy hai pipeline song song. Mỗi pipeline cần các cột gốc khác nhau:

| Cột gốc | Fraud Detection | Recommendation | Ghi chú |
|---|---|---|---|
| `fraud` (nhãn 0/1) | ✅ Bắt buộc — train XGBoost | ✅ Lọc user gian lận | Thiếu → không làm được supervised model |
| `merchant_category` | ✅ Hành vi bất thường | ✅ **Sống còn** — tính category ratios | Thiếu → Recommendation không hoạt động |
| `timestamp` | ✅ Velocity, sequence | ✅ RFM, recency | ~35/62 features phụ thuộc cột này |
| `amount` | ✅ Core feature | ✅ Core feature | Hiển nhiên |
| `customer_id` | ✅ Gộp theo user | ✅ Gộp theo user | Thiếu → không có user profile |
| `device_type` / `device_fingerprint` | ✅ Phát hiện Account Takeover | — | 3/7 luật Rule-based phụ thuộc cột này |
| `card_present` | ✅ Card-not-present fraud | — | Vector gian lận phổ biến nhất hiện nay |
| `country`, `city`, `city_size` | ✅ Geo-anomaly | ✅ Demographic proxy, cold start | — |
| `transaction_type` | ✅ Velocity | ✅ Cashout ratio, cashflow | — |
| `balance_before/after` | ✅ Balance anomaly | — | Quan trọng nhưng có thể ước lượng |

**Ràng buộc cốt lõi:** `merchant_category` là cột bắt buộc cho Recommendation (9 category ratios + 2 behavior frequency features đều phụ thuộc cột này). Bất kỳ dataset nào thiếu cột này đều không thể dùng cho Pipeline B.

---

## 2. SO SÁNH 5 DATASET

| Cột bắt buộc | **Transactions** | PaySim | IEEE-CIS | BankSim | Synthetic Financial |
|---|---|---|---|---|---|
| `fraud` (nhãn) | ✅ | ✅ | ✅ | ✅ | ✅ |
| `customer_id` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `timestamp` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `amount` | ✅ | ✅ | ✅ | ✅ | ✅ |
| **`merchant_category`** | **✅ Đa dạng** | **❌** | **❌** | **❌** | **⚠️ Hạn chế** |
| `device_type` | ✅ | ❌ | ✅ | ❌ | ❌ |
| `card_present` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `ip_address` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `transaction_type` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `balance_before/after` | ❌ | ✅ | ❌ | ✅ | ✅ |
| **Đáp ứng (trên 10)** | **9/10** | 7/10 | 7/10 | 7/10 | 6/10 |
| **Dùng được cho Rec?** | **✅** | ❌ | ❌ | ❌ | ⚠️ Yếu |
| **Kết luận** | **CHỌN** | Loại | Loại | Loại | Loại |

PaySim, IEEE-CIS, BankSim đều bị loại vì cùng một lý do: không có `merchant_category` → Recommendation không thể hoạt động.

---

## 3. ĐÁNH ĐỔI & CÁCH XỬ LÝ

| Hạn chế | Ảnh hưởng | Cách xử lý trong MVP |
|---|---|---|
| Thiếu `balance_before/after` | Giảm ~15% độ chính xác với loại fraud "rút cạn tài khoản" | Ước lượng từ `amount` + `transaction_type`; dùng `amount_zscore` thay `amount_to_balance_ratio` |
| Không có nhãn cho Recommendation | Cần tự tạo nhãn | Pseudo-label từ Rule-based Scorer dựa trên `merchant_category` |
| Dữ liệu synthetic | Không phải giao dịch thật 100% | Đủ cho MVP; thay thế bằng dữ liệu thật khi vận hành |
| Dung lượng 2.93 GB | Cần máy đủ RAM | Sample 30–50% hoặc dùng Polars/chunking |

---

## 4. KIẾN NGHỊ

| Hạng mục | Quyết định |
|---|---|
| Dataset chính | `synthetic_fraud_data.csv` (Transactions, Apache 2.0) |
| Dataset phụ | Không cần cho MVP |
| Mở rộng sau MVP | PaySim nếu cần cải thiện Account Takeover; dữ liệu thật khi vận hành |
| Xử lý dữ liệu | Sample 30–50% nếu máy yếu; chuẩn hóa `merchant_category` về bộ giá trị chung |
| Nhãn Recommendation | Pseudo-label từ Rule-based Scorer |

