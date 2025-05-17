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

## 🚀 Hướng dẫn chạy hệ thống trên localhost

Hệ thống gồm 2 phần riêng biệt cần chạy song song: **Backend** (Django) và **Frontend** (HTML/JS/CSS). Dưới đây là hướng dẫn chi tiết:

### 1. Chuẩn bị môi trường

1. **Cài đặt các công cụ cần thiết**:
   - Python 3.13.3 trở lên
   - Node.js v16 trở lên và npm
   - Git (để clone repo)

2. **Clone repository**:
   ```bash
   git clone https://github.com/<your-username>/PV5.git
   cd PV5
   ```

### 2. Thiết lập và chạy Backend (Django)

1. **Tạo và kích hoạt môi trường ảo Python**:
   ```bash
   cd backend
   python -m venv .venv
   
   # Trên macOS/Linux:
   source .venv/bin/activate
   
   # Trên Windows (PowerShell):
   .\.venv\Scripts\Activate.ps1
   
   # Trên Windows (CMD):
   .\.venv\Scripts\activate.bat
   ```

2. **Cài đặt các dependencies Python**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Cấu hình môi trường**:
   - Tạo file `.env` từ file mẫu `.env.example` (nếu có)
   - Mặc định hệ thống sử dụng SQLite, không cần cấu hình DB phức tạp

4. **Chạy migrations để tạo cấu trúc database**:
   ```bash
   python manage.py migrate
   ```

5. **Tạo tài khoản admin (để truy cập Django Admin)**:
   ```bash
   python manage.py createsuperuser
   ```
   Điền thông tin theo hướng dẫn (email, username, password)

6. **Khởi động Django server trên port 8000**:
   ```bash
   python manage.py runserver
   ```
   Backend sẽ chạy tại địa chỉ: http://127.0.0.1:8000/

7. **Kiểm tra API hoạt động**:
   - Mở trình duyệt và truy cập: http://127.0.0.1:8000/api/v1/
   - Truy cập trang Admin: http://127.0.0.1:8000/admin/ (đăng nhập bằng tài khoản vừa tạo)

### 3. Thiết lập và chạy Frontend

1. **Cài đặt dependencies Node.js**:
   ```bash
   # Mở terminal mới (giữ terminal backend đang chạy)
   cd PV5/frontend
   npm install
   ```

2. **Build CSS với Tailwind**:
   ```bash
   npm run build
   ```

3. **Khởi động development server cho frontend**:
   ```bash
   npm run dev
   ```
   Frontend sẽ chạy tại địa chỉ: http://localhost:3000/

4. **Xem ở chế độ development (không cần server)**:
   - Ngoài việc chạy server, bạn cũng có thể mở trực tiếp file `frontend/src/index.html` trong trình duyệt
   - Tuy nhiên cách này có thể gặp vấn đề về CORS khi gọi API

### 4. Truy cập hệ thống đầy đủ

1. **Mở trình duyệt và truy cập**: http://localhost:3000/
2. **Hệ thống hoạt động khi**:
   - Backend Django chạy trên port 8000
   - Frontend server chạy trên port 3000
   - Frontend có thể gọi API từ backend qua địa chỉ http://127.0.0.1:8000/api/v1/

### 5. Các tính năng đã sẵn sàng

- **Xác thực người dùng**: Đăng ký, đăng nhập, quản lý token JWT
- **Sản phẩm**: Xem danh sách, chi tiết sản phẩm
- **Giỏ hàng**: Thêm sản phẩm, quản lý giỏ hàng
- **Phân quyền**: Admin, Quản lý, Nhân viên bán hàng, Nhân viên kho, Khách hàng

### 6. Các lệnh hữu ích

```bash
# Chạy backend ở chế độ debug
cd backend && source .venv/bin/activate && python manage.py runserver

# Chạy frontend với hot-reload CSS
cd frontend && npm run watch

# Chạy frontend dev server
cd frontend && npm run dev

# Tạo migrations mới (khi thay đổi model)
cd backend && python manage.py makemigrations

# Chạy tests
cd backend && python manage.py test

# Xóa dữ liệu và tạo lại database
cd backend && python manage.py flush
```

### 7. Xử lý lỗi thường gặp

1. **Lỗi CORS**: Nếu frontend không gọi được API, kiểm tra:
   - Backend đã chạy và truy cập được qua http://127.0.0.1:8000/api/v1/
   - Cài đặt CORS trong `backend/PV5/settings.py` đã cho phép frontend domain

2. **Lỗi 401 Unauthorized**: 
   - Kiểm tra đăng nhập và token JWT
   - Xem token đã được lưu đúng trong localStorage chưa

3. **Lỗi CSS không cập nhật**:
   - Chạy lại lệnh `npm run build` 
   - Kiểm tra file output.css đã được tạo trong thư mục frontend/src/static/css/

---

## 🛠️ Môi trường phát triển 

### Không phụ thuộc IDE

* Bạn có thể dùng bất kỳ editor/IDE nào: VS Code, Sublime Text, Vim, Emacs, IntelliJ, v.v.
* Chỉ cần trỏ interpreter Python của IDE vào `backend/.venv` và cấu hình Node path trỏ vào `frontend/node_modules`.

### Lưu ý hệ điều hành

* **macOS / Linux**:
  * Dùng `source .venv/bin/activate` để kích hoạt venv.
  * Cấp quyền thực thi `chmod +x manage.py` nếu cần.

* **Windows**:
  * Dùng PowerShell với `Activate.ps1` hoặc CMD với `activate.bat`.
  * Thay dấu `/` bằng `\\` trong đường dẫn khi chỉnh script.

### Đóng góp & Triển khai

* **Chi nhánh**: Tạo branch từ `main` cho mỗi tính năng.
* **Test**: Mỗi app có `tests.py`; chạy `python manage.py test`.
* **CI/CD**: Sử dụng GitHub Actions hoặc GitLab CI để tự động tests và build.

---

*Chi tiết module, xem README.md trong từng thư mục `apps/` nếu có.*

