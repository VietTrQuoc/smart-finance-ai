# Smart Finance AI

Repo demo hệ thống phân tích giao dịch tài chính: tạo feature theo khách hàng, seed SQLite, chấm fraud/risk heuristic, gợi ý sản phẩm từ `product_catalog`, xếp lead và hiển thị dashboard local.

## Thành phần chính

```text
smart-finance-ai/
├── configs/                    # Product catalog và schema cấu hình
├── dashboard/                  # Static UI cho Recommendation/Fraud review
├── data/                       # Dữ liệu local, bị gitignore
├── docs/                       # PRD, database, model/data, plan
├── output/                     # Output phân cụm/recommendation
├── scripts/                    # Script chạy dashboard và tạo slide
├── src/
│   ├── api/                    # HTTP server local
│   ├── backend/                # Build payload cho dashboard
│   ├── data/                   # Feature engineering từ transaction CSV
│   ├── db/                     # SQLite schema + seed
│   └── recommendation/         # Cluster -> product mapping
└── tests/                      # Unit tests
```

## Yêu cầu

- Python 3.10+.
- Windows PowerShell hoặc terminal tương đương.
- File dữ liệu raw `synthetic_fraud_data.csv` nếu muốn build lại feature/database từ đầu.

Dataset raw có thể tải từ Kaggle: [Synthetic Fraud Data](https://www.kaggle.com/datasets/ismetsemedov/transactions?select=synthetic_fraud_data.csv).

Sau khi tải, đặt file tại:

```text
data/synthetic_fraud_data.csv
```

Lưu ý: thư mục `data/` bị ignore trong git vì file CSV/DB rất lớn.

## Cài đặt môi trường

Chạy từ thư mục gốc repo:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Các lệnh bên dưới dùng trực tiếp `.\.venv\Scripts\python.exe`, nên không cần activate venv.

## Chạy nhanh dashboard

Nếu trong `data/` đã có `smart_finance.db` hoặc `user_features_sample.csv`, chạy:

```powershell
.\.venv\Scripts\python.exe scripts\run_dashboard.py --host 127.0.0.1 --port 8000
```

Mở trình duyệt tại:

```text
http://127.0.0.1:8000
```

API kiểm tra nhanh:

```text
http://127.0.0.1:8000/api/health
http://127.0.0.1:8000/api/dashboard
```

Dashboard ưu tiên đọc `data/smart_finance.db`. Nếu chưa có DB, backend sẽ đọc feature CSV trong `data/` theo thứ tự: `user_features.csv`, `user_features_sample.csv`, rồi `customer_features.csv`.

## Build dữ liệu từ CSV raw

Nếu mới tải `data/synthetic_fraud_data.csv`, tạo feature store trước.

Tạo bản sample để chạy demo nhanh:

```powershell
.\.venv\Scripts\python.exe -m src.data.feature_engineering --input data\synthetic_fraud_data.csv --output data\user_features_sample.csv --sample-rows 100000
```

Tạo full feature store:

```powershell
.\.venv\Scripts\python.exe -m src.data.feature_engineering --input data\synthetic_fraud_data.csv --output data\user_features.csv
```

Sau đó seed SQLite:

```powershell
.\.venv\Scripts\python.exe -m src.db.init_db --db data\smart_finance.db --recreate
```

Mặc định seed DB chỉ import tối đa `10,000` transactions raw để dashboard nhẹ. Nếu muốn import toàn bộ transaction CSV:

```powershell
.\.venv\Scripts\python.exe -m src.db.init_db --db data\smart_finance.db --recreate --full-transactions
```

## Luồng recommendation và fraud hiện tại

Trong MVP hiện tại, `fraud_score` trên dashboard là heuristic, chưa phải model XGBoost thật:

```text
fraud_score =
  0.82 * risk_score
+ 0.07 * night_transaction_ratio
+ 0.06 * min(balance_volatility / 2, 1)
+ 0.05 * min(negative_cashflow_days / 10, 1)
```

Ngưỡng guardrail:

```text
fraud_score < 0.3        -> eligible
0.3 <= fraud_score < 0.7 -> chỉ gợi ý sản phẩm risk_allowed = low
fraud_score >= 0.7       -> blocked_fraud, không gợi ý sản phẩm
```

Thiết kế production trong docs định hướng dùng XGBoost probability + SHAP, nhưng phần đó chưa được implement đầy đủ trong source hiện tại.

## Product catalog

Danh mục sản phẩm nằm ở:

```text
configs/product_catalog.json
```

Khi thêm/sửa sản phẩm, cập nhật các trường chính:

- `product_id`, `product_name`, `product_type`
- `risk_allowed`
- `target_behavior`
- `target_signals_json`
- `eligibility_json`
- `campaign_priority`
- `reason_template`

Sau khi sửa catalog, seed lại DB để dashboard nhận dữ liệu mới:

```powershell
.\.venv\Scripts\python.exe -m src.db.init_db --db data\smart_finance.db --recreate
```

## Tạo PowerPoint từ catalog

Tạo deck visual:

```powershell
.\.venv\Scripts\python.exe scripts\product_catalog_visual_pptx.py --catalog configs\product_catalog.json --output PRODUCT_CATALOG_VISUAL.pptx
```

Tạo deck từ Markdown Marp-style:

```powershell
.\.venv\Scripts\python.exe scripts\markdown_to_pptx.py configs\PRODUCT_CATALOG_SLIDES.md PRODUCT_CATALOG_SLIDES.pptx
```

## Chạy tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Kết quả kỳ vọng:

```text
Ran 5 tests
OK
```

## Lệnh hữu ích

Chạy API server trực tiếp:

```powershell
.\.venv\Scripts\python.exe -m src.api.server --host 127.0.0.1 --port 8000
```

Xem help của feature engineering:

```powershell
.\.venv\Scripts\python.exe -m src.data.feature_engineering --help
```

Xem help của DB seed:

```powershell
.\.venv\Scripts\python.exe -m src.db.init_db --help
```

Chạy cluster-product mapping cũ:

```powershell
.\.venv\Scripts\python.exe src\recommendation\cluster_product_mapping.py
```

Nếu lệnh cluster báo thiếu `sklearn`, cài thêm:

```powershell
.\.venv\Scripts\python.exe -m pip install scikit-learn
```

## Troubleshooting

Nếu gặp lỗi `ModuleNotFoundError: No module named 'src'`, hãy chạy lệnh từ thư mục gốc repo `smart-finance-ai`.

Nếu dashboard không có dữ liệu, kiểm tra một trong các file sau có tồn tại không:

```text
data/smart_finance.db
data/user_features.csv
data/user_features_sample.csv
data/customer_features.csv
```

Nếu PowerShell không cho activate venv, không cần activate. Dùng trực tiếp:

```powershell
.\.venv\Scripts\python.exe <command>
```

Nếu build full `synthetic_fraud_data.csv` quá lâu, dùng `--sample-rows` để tạo bản demo nhanh trước.

## Tài liệu thêm

- [docs/PRD.md](docs/PRD.md)
- [docs/MODEL&DATA.md](docs/MODEL&DATA.md)
- [docs/DATABASE.md](docs/DATABASE.md)
- [docs/PLAN.md](docs/PLAN.md)
- [configs/PRODUCT_CATALOG.md](configs/PRODUCT_CATALOG.md)
