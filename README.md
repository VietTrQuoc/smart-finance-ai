# Hướng dẫn thiết lập dữ liệu (Data Setup)

Dự án này sử dụng tập dữ liệu giao dịch giả lập để phát hiện gian lận. Vui lòng làm theo các bước dưới đây để tải, giải nén và cấu hình đúng thư mục dữ liệu trước khi chạy mã nguồn.

---

## Các bước thực hiện

### Bước 1: Tải dữ liệu từ Kaggle
1. Truy cập vào đường dẫn tập dữ liệu trên Kaggle: [Synthetic Fraud Data](https://www.kaggle.com/datasets/ismetsemedov/transactions?select=synthetic_fraud_data.csv).
2. Đăng nhập tài khoản Kaggle của bạn (nếu chưa đăng nhập).
3. Nhấn vào nút **Download** (biểu tượng tải xuống) để tải file nén `archive.zip` về máy tính.

### Bước 2: Tạo thư mục chứa dữ liệu
Trong thư mục gốc của dự án (`smart-finance-ai`), tiến hành tạo một thư mục mới có tên là `data`.

* **Giao diện (UI):** Click chuột phải ở thư mục gốc -> Chọn *New Folder* -> Đặt tên là `data`.
* **Lệnh Terminal:** Nếu bạn dùng dòng lệnh, hãy chạy:
  ```bash
  mkdir data

  ```

### Bước 3: Giải nén và đổi tên file

1. Giải nén file `archive.zip` vừa tải về từ Kaggle. Bên trong bạn sẽ thấy tệp tin có tên là `synthetic_fraud_data.csv`.
2. Di chuyển (hoặc copy) file `synthetic_fraud_data.csv` vào bên trong thư mục `data` vừa tạo ở Bước 2.

---

## Cấu trúc thư mục chuẩn sau khi thiết lập

Sau khi hoàn thành, cấu trúc thư mục dự án của bạn phải trông giống như thế này:

  ```text
  smart-finance-ai/
  ├── data/
  │   └── synthetic_fraud_data.csv
  ├── .gitignore
  └── README.md

  ```
