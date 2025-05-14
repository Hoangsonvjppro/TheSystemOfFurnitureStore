# PV5 – Dự án Cửa hàng Nội thất

Kho lưu trữ này chứa ứng dụng web bán đồ nội thất gồm hai phần:

* **Backend**: Django + Django REST Framework
* **Frontend**: HTML + TailwindCSS + JavaScript thuần

---

## 📋 Cấu trúc dự án

```
PV5/
├── backend/                # Phần backend Django
│   ├── .venv/              # Môi trường ảo Python (bị ignore)
│   ├── manage.py           # Entry-point Django
│   ├── requirements.txt    # Danh sách dependencies Python
│   ├── PV5/                # Module Django chính
│   └── apps/               # Các Django apps (users, products, ...)
└── frontend/               # Phần frontend TailwindCSS + JS
    ├── node_modules/       # Dependencies npm (bị ignore)
    ├── package.json        # Cấu hình npm + scripts
    └── src/                # HTML template, CSS, JS
```

---

## 🚀 Hướng dẫn nhanh

Thực hiện các bước sau sau khi clone repo:

```bash
# Clone repo
git clone https://github.com/<your-username>/PV5.git
cd PV5
```

### 1. Thiết lập Backend (Django)

1. **Cài đặt Python 3.13.3+**
2. **Tạo và kích hoạt môi trường ảo**

   ```bash
   cd backend
   python -m venv .venv          # Tạo venv trong backend/
   # Trên macOS/Linux:
   source .venv/bin/activate
   # Trên Windows (PowerShell):
   .\.venv\Scripts\Activate.ps1
   ```
3. **Cài dependencies**

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. **Cấu hình biến môi trường**

   * Copy file `.env.example` thành `.env` và cấu hình thông tin DB (MySQL) nếu cần.
5. **Chạy migrations & khởi động server**

   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

Mở trình duyệt đến `http://localhost:8000/admin/` để truy cập Django Admin.

### 2. Thiết lập Frontend (TailwindCSS + JS)

1. **Cài Node.js (v16+) và npm/yarn**
2. **Cài npm packages**

   ```bash
   cd ../frontend
   npm install
   ```
3. **Build CSS**

   * **Build một lần:**

     ```bash
     npm run build
     ```
   * **Chế độ watch (tự rebuild khi thay đổi):**

     ```bash
     npm run watch
     ```
4. **Xem demo HTML**

   * Mở trực tiếp file trong `src/pages/*.html`, hoặc tích hợp vào Django template bằng cách copy file build vào thư mục `static/` của Django.

### 3. Không phụ thuộc IDE

* Bạn có thể dùng bất kỳ editor/IDE nào: VS Code, Sublime Text, Vim, Emacs, IntelliJ, v.v.
* Chỉ cần trỏ interpreter Python của IDE vào `backend/.venv` và cấu hình Node path trỏ vào `frontend/node_modules`.

### 4. Lưu ý hệ điều hành

* **macOS / Linux**:

  * Dùng `source .venv/bin/activate` để kích hoạt venv.
  * Cấp quyền thực thi `chmod +x manage.py` nếu cần.
* **Windows**:

  * Dùng PowerShell với `Activate.ps1` hoặc CMD với `activate.bat`.
  * Thay dấu `/` bằng `\\` trong đường dẫn khi chỉnh script.

### 5. Các lệnh thường dùng

```bash
# Chạy backend
git pull && cd backend && source .venv/bin/activate && python manage.py runserver
# Chạy frontend
git pull && cd frontend && npm run watch
```

### 6. Đóng góp & Triển khai

* **Chi nhánh**: Tạo branch từ `main` cho mỗi tính năng.
* **Test**: Mỗi app có `tests.py`; chạy `python manage.py test`.
* **CI/CD**: Sử dụng GitHub Actions hoặc GitLab CI để tự động tests và build.

---

*Chi tiết module, xem README.md trong từng thư mục `apps/` nếu có.*

