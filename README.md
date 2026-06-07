# Tool Buff View Article 🎯

Một công cụ tự động hóa Selenium để mở và xem các bài viết trong trình duyệt, hỗ trợ cả chế độ CLI và GUI.

## 📋 Mô tả

Tool này sử dụng Selenium để tự động:
- Mở các liên kết bài viết trong trình duyệt (Chrome/Edge)
- Cuộn trang và tương tác với content
- Chạy theo vòng lặp với cấu hình linh hoạt
- Hỗ trợ xử lý nhiều liên kết đồng thời (lên đến 4 cửa sổ)

## 🛠️ Công nghệ sử dụng

- **Python** - Logic chính
- **Selenium WebDriver** - Tự động hóa trình duyệt
- **Tkinter** - Giao diện người dùng GUI
- **PyInstaller** - Đóng gói thành executable

## 📊 Thành phần dự án

| Tên file | Mô tả |
|----------|-------|
| `selenium_ui_app.py` | Ứng dụng GUI (Tkinter) với giao diện đầy đủ |
| `main-noproxy-nochromdef.py` | Script CLI không proxy |
| `requirements.txt` | Các thư viện cần thiết |
| `build_app.ps1` | Script xây dựng executable (PowerShell) |
| `SeleniumWindowRunner.spec` | Cấu hình PyInstaller |

## 🚀 Cài đặt

### Yêu cầu
- Python 3.8+
- Windows (do sử dụng ctypes.windll)
- Chrome hoặc Edge browser

### Bước 1: Clone repo
```bash
git clone https://github.com/DODANGHOANCNTT2K15/tool-buff-view-article.git
cd tool-buff-view-article
```

### Bước 2: Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### Bước 3: Tạo file link.txt
Tạo file `link.txt` trong thư mục gốc và thêm các liên kết (tối đa 4 dòng):
```
https://example.com/article1
https://example.com/article2
https://example.com/article3
```

## 📖 Cách sử dụng

### Chế độ GUI (Khuyến nghị)
```bash
python selenium_ui_app.py
```

**Các tùy chọn cấu hình:**
- **Browser**: Chọn Edge hoặc Chrome
- **Số vong**: Số lần lặp (1-1000)
- **Cho sau mo**: Chờ (giây) sau khi mở trang
- **Cho sau cuon**: Chờ (giây) sau khi cuộn
- **Cho truoc dong**: Chờ (giây) trước đóng tất cả cửa sổ
- **Nghi giua vong**: Chờ (giây) giữa các vòng
- **Pixel cuon**: Số pixel cuộn (mặc định 2500)
- **Timeout load**: Timeout tải trang (giây)
- **Retry**: Số lần thử lại nếu lỗi

### Chế độ CLI
```bash
python main-noproxy-nochromdef.py
```

Chỉnh sửa các hằng số ở đầu file:
```python
BROWSER = "edge"  # hoặc "chrome"
LOOP_COUNT = 1000
SCROLL_PIXELS = 2500
PAGE_LOAD_TIMEOUT_SECONDS = 10
WAIT_AFTER_OPEN_SECONDS = 0
WAIT_AFTER_SCROLL_SECONDS = 0
WAIT_BEFORE_CLOSE_ALL_SECONDS = 3
WAIT_BETWEEN_ROUNDS_SECONDS = 0
RETRY_PER_ROUND = 2
```

## 🔧 Xây dựng Executable

### Trên Windows (PowerShell):
```powershell
./build_app.ps1
```

Hoặc thủ công:
```bash
pyinstaller SeleniumWindowRunner.spec
```

Tệp .exe sẽ được tạo trong thư mục `dist/`.

## 📝 Tính năng chính

✅ **Hỗ trợ 2 browser**: Chrome + Edge  
✅ **Chế độ đơn/đa liên kết**: Mở 1-4 liên kết đồng thời  
✅ **Giao diện GUI**: Kiểm soát dễ dàng  
✅ **Xử lý lỗi**: Tự động retry khi Selenium gặp lỗi  
✅ **Log chi tiết**: Theo dõi tiến trình trong thời gian thực  
✅ **Cuộn + Tương tác chuột**: Mô phỏng hành vi người dùng  
✅ **Đóng gói executable**: Chạy mà không cần Python  

## 🎮 Ví dụ sử dụng

1. **Mở 3 liên kết 10 lần** với Edge:
   - Paste 3 liên kết vào khung "Links"
   - Đặt "So vong" = 10
   - Browser = "edge"
   - Nhấn "Start"

2. **Chạy 1 liên kết 1000 lần** với cuộn:
   - Paste 1 liên kết
   - "So vong" = 1000
   - "Pixel cuon" = 2500
   - Nhấn "Start"

## ⚙️ Cấu hình mặc định

```python
LOOP_COUNT = 1000           # Số lần lặp
WAIT_AFTER_OPEN_SECONDS = 0 # Không chờ sau mở
SCROLL_PIXELS = 2500         # Cuộn 2500 pixel
PAGE_LOAD_TIMEOUT_SECONDS = 10
RETRY_PER_ROUND = 2         # Retry 2 lần nếu lỗi
```

## 📞 Troubleshooting

**Vấn đề: "link.txt dang trong" (File trống)**
- Tạo file `link.txt` và thêm ít nhất 1 liên kết

**Vấn đề: Chrome/Edge không mở**
- Kiểm tra các browser đã cài đặt
- Cập nhật ChromeDriver/EdgeDriver

**Vấn đề: Timeout lỗi**
- Tăng "Timeout load"
- Kiểm tra kết nối internet

**Vấn đề: Retry lỗi liên tục**
- Tăng "Retry" số lượng
- Thử đơn vị chỉ 1 liên kết

## 📦 Dependencies

```
selenium==4.38.0
pyinstaller
```

## 👤 Tác giả

**DODANGHOANCNTT2K15**
- GitHub: [@DODANGHOANCNTT2K15](https://github.com/DODANGHOANCNTT2K15)

## 📄 Giấy phép

Chưa được chỉ định. Vui lòng liên hệ tác giả.

## 🔗 Liên quan

- [Selenium Documentation](https://www.selenium.dev/)
- [PyInstaller Guide](https://pyinstaller.org/)

---

⭐ **Nếu thấy hữu ích, hãy cho repo này một star!**

💡 **Tip**: Để chạy lần đầu, dùng GUI (`selenium_ui_app.py`) - dễ dùng hơn!
