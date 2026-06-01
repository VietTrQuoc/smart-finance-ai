# Product Requirements Document (PRD) & System Specification

**Tên dự án:** AI Transaction Analyzer (Phân tích Giao dịch, Khuyến nghị & Phát hiện Gian lận)
**Trạng thái:** Bản Nháp (Draft) cho MVP
**Thời gian phát triển (dự kiến):** 6 tuần

---

## 1. TỔNG QUAN DỰ ÁN (Project Overview)

### 1.1 Mục tiêu kinh doanh
Hệ thống AI Transaction Analyzer được xây dựng nhằm giải quyết hai bài toán lớn của tổ chức tài chính thông qua việc phân tích dữ liệu giao dịch:
1. **Bảo vệ tài sản:** Phát hiện và ngăn chặn theo thời gian thực (real-time) các hành vi gian lận (Account Takeover, Money Mule, Fraud Rings...), giảm thiểu thiệt hại tài chính.
2. **Tăng trưởng doanh thu (Cross-sell/Up-sell):** Phân tích hành vi tiêu dùng và luồng tiền (cashflow) để gợi ý các sản phẩm tài chính (thẻ tín dụng, khoản vay, bảo hiểm) phù hợp nhất với từng cá nhân, đồng thời tự động sinh kịch bản tư vấn bằng LLM để tối ưu hoá tỷ lệ chốt sale.

### 1.2 Khách hàng mục tiêu (Target Users)
* **Fraud Analyst (Chuyên viên chống gian lận):** Giám sát các giao dịch có độ rủi ro cao, xem xét các cảnh báo (alerts), kiểm tra các đặc điểm dẫn đến quyết định của AI (Explainable AI - SHAP) và đưa ra quyết định cuối cùng.
* **Telesales / Relationship Manager (Nhân viên tư vấn):** Tra cứu khách hàng, xem danh sách sản phẩm được gợi ý để chào bán, và sử dụng kịch bản do LLM sinh ra để gọi điện tư vấn.

---

## 2. PHẠM VI SẢN PHẨM (Product Scope)

### 2.1 In Scope (Trong MVP 6 tuần)
* Pipeline xử lý dữ liệu giao dịch thành các đặc trưng người dùng (User Features) và đặc trưng gian lận (Fraud Features).
* Hệ thống Fraud Detection (Rule-based + Isolation Forest + XGBoost) phát hiện 9 loại gian lận cơ bản.
* Hệ thống Recommendation (Rule-based kết hợp phân loại rủi ro) gợi ý Top 3 sản phẩm tài chính.
* Cơ chế chặn (Gatekeeper): Không cho phép gợi ý sản phẩm hoặc tạo kịch bản cho người dùng bị tình nghi gian lận.
* Tích hợp Agentic LLM (LangGraph + Deepseek/Gemini) để sinh kịch bản tư vấn telesales có kiểm duyệt (Guardrails).
* Dashboard 2 chức năng riêng biệt cho Fraud Analyst và Telesales.
* Hệ thống API xử lý thời gian thực với Latency cho Fraud Detection < 200ms.

### 2.2 Out of Scope (Không làm trong MVP)
* Mô hình Two-Tower PyTorch cho Recommendation (đợi thu thập đủ dữ liệu tương tác thực tế).
* Mô hình Graph Neural Network (GNN) để phát hiện gian lận theo cụm/mạng lưới phức tạp.
* Streaming Data thực sự qua Kafka/Flink (chỉ mô phỏng API real-time).
* Gửi kịch bản tư vấn qua SMS/Email tự động (hiện tại nhân viên phải thao tác thủ công).

---

## 3. CÁC TÍNH NĂNG CHÍNH VÀ USER STORIES (Epics)

### EPIC 1: Fraud Detection Engine (Hệ thống phát hiện gian lận)
| ID | User Story | Acceptance Criteria (Tiêu chí nghiệm thu) |
|---|---|---|
| FD-01 | Là hệ thống, tôi muốn tự động chấm điểm gian lận cho mọi giao dịch mới trong vòng 200ms. | - Trả về `fraud_score` từ 0 đến 1.<br>- Phân loại 3 mức: PASS (<0.3), REVIEW (0.3-0.7), FLAG (>0.7).<br>- Phản hồi API <= 200ms. |
| FD-02 | Là hệ thống, tôi muốn phân loại rõ loại gian lận (Account Takeover, Money Mule, v.v.). | - Output API phải chứa trường `fraud_type` dựa vào Rule hoặc Model. |
| FD-03 | Là Fraud Analyst, tôi muốn biết TẠI SAO một giao dịch bị đánh dấu gian lận. | - API phải trả về `shap_explanation` chứa top 3-5 features đóng góp nhiều nhất vào `fraud_score`. |
| FD-04 | Là Fraud Analyst, tôi muốn xem danh sách các tài khoản đang bị cảnh báo và xác nhận (Confirm) hoặc loại bỏ (False Positive). | - API `/fraud/feedback` lưu trữ phản hồi của Analyst xuống Database. |

### EPIC 2: Product Recommendation (Hệ thống gợi ý sản phẩm)
| ID | User Story | Acceptance Criteria (Tiêu chí nghiệm thu) |
|---|---|---|
| RE-01 | Là Telesales, tôi muốn nhận được Top 3 sản phẩm phù hợp nhất với một `user_id`. | - API trả về mảng 3 sản phẩm từ `product_catalog`.<br>- Mỗi sản phẩm kèm theo một `reason` mô tả lý do (vd: "Hay mua vé máy bay"). |
| RE-02 | Là hệ thống, tôi muốn KHÔNG gợi ý sản phẩm cho các tài khoản đang có `fraud_score > 0.7`. | - Trả về thông báo lỗi "Tài khoản bị cảnh báo gian lận". |
| RE-03 | Là hệ thống, tôi muốn chỉ gợi ý sản phẩm rủi ro thấp (tiết kiệm, bảo hiểm) cho các tài khoản có `fraud_score` từ 0.3 - 0.7. | - Không có thẻ tín dụng hoặc khoản vay trong danh sách gợi ý của các tài khoản này. |

### EPIC 3: Agentic LLM Pitching Bot (Trợ lý tư vấn bằng LLM)
| ID | User Story | Acceptance Criteria (Tiêu chí nghiệm thu) |
|---|---|---|
| LB-01 | Là Telesales, tôi muốn hệ thống tự động sinh kịch bản tư vấn độ dài 80-120 từ. | - Kịch bản phải tự nhiên, chuyên nghiệp.<br>- Phải nhắc đến insights của khách hàng và lý do gợi ý sản phẩm. |
| LB-02 | Là tổ chức, tôi muốn đảm bảo LLM không bao giờ nói những từ khóa nhạy cảm (như "thiếu tiền", "AI phát hiện", "gian lận"). | - Áp dụng Guardrails, kịch bản sinh ra không được chứa các ngôn từ cấm. |
| LB-03 | Là Telesales, tôi không muốn hệ thống sinh kịch bản nếu người dùng bị nghi ngờ gian lận (`fraud_score` > 0.3). | - Trả về thông báo từ chối tạo kịch bản do rủi ro tài khoản. |

### EPIC 4: Frontend Dashboard (Giao diện người dùng)
| ID | User Story | Acceptance Criteria (Tiêu chí nghiệm thu) |
|---|---|---|
| UI-01 | Là người dùng, tôi muốn có 2 Tab riêng biệt (Fraud và Recommendation) để không bị rối mắt. | - Layout Streamlit/React có hệ thống Tab Navigation. |
| UI-02 | Là Fraud Analyst, tôi muốn xem biểu đồ thể hiện lý do gian lận. | - Tích hợp Plotly Waterfall/Bar chart để biểu diễn SHAP values. |
| UI-03 | Là Telesales, tôi muốn có một nút bấm "Tạo kịch bản tư vấn" nằm cạnh sản phẩm được gợi ý. | - Bấm nút sẽ gọi API `/generate-pitch` và hiển thị kết quả trong textbox. |

---

## 4. YÊU CẦU PHI CHỨC NĂNG (Non-Functional Requirements)

### 4.1. Hiệu suất & Thời gian phản hồi (Performance & Latency)
- **Fraud Detection Pipeline:** Phải hoàn thành luồng trích xuất đặc trưng (Feature extraction) -> Rule-based -> XGBoost -> SHAP trong tổng thời gian **< 200 mili-giây** để đáp ứng yêu cầu Real-time block.
- **Recommendation API:** Phản hồi dưới **2 giây**.
- **LLM Pitching:** Phản hồi dưới **10 giây**.

### 4.2. Bảo mật & Tuân thủ (Security & Compliance)
- **Mã hoá PII:** API không được trả về số tài khoản đầy đủ, số điện thoại (phải dùng kỹ thuật masking như `098***123`). Không truyền dữ liệu định danh thật qua API của Deepseek/Gemini.
- **RBAC (Role-based Access Control):** Frontend phải hỗ trợ hai vai trò người dùng: Telesales (không thấy tab Fraud) và Analyst (thấy toàn bộ).

### 4.3. Sự kiện Tương tác (Telemetry & Tracking)
- Mọi tương tác của Telesales với sản phẩm gợi ý (View, Click, Khách hàng đồng ý, Khách hàng từ chối) phải được gọi API `POST /recommendations/interaction` để thu thập dữ liệu phục vụ huấn luyện mô hình ML sau này.

### 4.4. Độ tin cậy (Reliability)
- **LLM Fallback:** Nếu API LLM gặp sự cố, hệ thống trả về kịch bản cứng (rule-based template) thay vì báo lỗi toàn bộ ứng dụng.

---

## 5. MÔ HÌNH DỮ LIỆU & KIẾN TRÚC API (System Specs)

### 5.1 Hệ thống Database cốt lõi (6 bảng)
1. `transactions`: Lưu trữ lịch sử giao dịch thô.
2. `user_features`: Ma trận đặc trưng tổng hợp của người dùng (RFM, Cashflow).
3. `product_catalog`: Danh mục sản phẩm cấu hình sẵn rủi ro.
4. `fraud_alerts`: Bảng quản lý các cảnh báo gian lận và feedback của Analyst.
5. `fraud_model_scores`: Lưu lại log chấm điểm và SHAP của mô hình Fraud cho từng giao dịch.
6. `recommendation_logs` & `pitch_logs`: Lưu log khuyến nghị và nội dung kịch bản LLM.

### 5.2 API Interfaces
- Nhóm Fraud: `POST /fraud/score`, `GET /users/{id}/fraud-alerts`, `POST /fraud/feedback`.
- Nhóm Khách hàng: `GET /users/{id}/profile`, `GET /users/{id}/insights`.
- Nhóm Khuyến nghị: `GET /users/{id}/recommendations`, `POST /users/{id}/generate-pitch`, `POST /recommendations/interaction`.

---

## 6. CHỈ SỐ ĐO LƯỜNG THÀNH CÔNG (Success Metrics)

| Hạng mục | KPI / Metric | Mục tiêu MVP |
|---|---|---|
| **Fraud Detection** | Tỷ lệ báo nhầm (False Positive Rate) | < 5% |
| | Điểm F1 / AUPRC trên tập test | Đạt > 0.85 |
| **Recommendation** | Rule Coverage (Tỷ lệ KH có gợi ý hợp lệ) | > 95% |
| | Conversion Rate ước tính (A/B Test) | Tăng 15% so với ngẫu nhiên |
| **LLM Bot** | Số từ nhạy cảm lọt qua Guardrails | 0 |
| | Thời gian trung bình tạo pitch | < 10 giây |
| **System** | API Uptime | 99.9% |
