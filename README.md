# Frappe CRM – Điện Máy Xanh (Đồ án CRM · UIT)

Hệ thống **Frappe CRM + ERPNext v15** đã được cấu hình sẵn cho doanh nghiệp **Điện Máy Xanh** theo tiêu chí **A4.2.1** (tiền tệ VND, múi giờ, ngôn ngữ, người dùng & phân quyền, avatar, email, sales team, pipeline/lead, nguyên nhân thất bại, mẫu báo giá/hóa đơn).
Toàn bộ dữ liệu nằm trong thư mục `backup/`. Khi bạn chạy Docker lần đầu, script sẽ **tự cài đặt và khôi phục**, không phải cấu hình lại từ đầu.

| Thành viên | Email | Phòng ban | Vai trò |
|---|---|---|---|
| Đinh Thị Quỳnh Thư | quynhthu3677@gmail.com | Ban Quản trị CRM | System Manager, Sales Manager (Admin) |
| Nguyễn Ngô Gia Hân | nnghan23@gmail.com | Phòng Kinh doanh | Sales Manager, Sales User |
| Nguyễn Châu Hoàng Phương | nchphuong06@gmail.com | Phòng Chăm sóc Khách hàng | Sales User, Support Team |
| Thạch Thanh Thủy | thachthanhthuy287@gmail.com | Phòng Marketing | Sales User, Marketing User |

Mật khẩu mặc định của tất cả tài khoản (kể cả `Administrator`) là **`admin123`**.

---

## 1. Chuẩn bị (làm 1 lần)

1. Cài **Docker Desktop**: <https://www.docker.com/products/docker-desktop/>
   - Windows: bật **WSL 2** khi được hỏi, khởi động lại máy.
   - Mở Docker Desktop → *Settings → Resources*: cấp **RAM ≥ 4 GB** (khuyến nghị 6 GB).
2. Cài **Git**: <https://git-scm.com/downloads>
3. Kiểm tra trong PowerShell:
   ```powershell
   docker --version
   docker compose version
   git --version
   ```

## 2. Tải mã nguồn và chạy (2 lệnh)

```powershell
git clone https://github.com/quynhthu121/CRM_-MX.git
cd CRM_-MX
```

> **Bắt buộc với phần cá nhân (A4.3.2):** mở file `.env` và sửa 2 dòng sau thành **email và họ tên của chính bạn**:
> ```
> OWNER_EMAIL=email_cua_ban@gmail.com
> OWNER_FULL_NAME=Họ Tên Của Bạn
> ```
> Script sẽ tạo tài khoản quản trị (System Manager) mang email của bạn, mật khẩu `admin123`.

```powershell
docker compose up -d
docker compose logs -f frappe
```

Lần đầu mất khoảng **15–30 phút** để tải Frappe/ERPNext/CRM và khôi phục dữ liệu. Khi log hiện dòng sau là xong (nhấn `Ctrl + C` để thoát xem log, hệ thống vẫn chạy):

```
========== [DMX] HOÀN TẤT – mở http://dmx.localhost:8000 (hoặc http://localhost:8000) ==========
```

Mở trình duyệt:
- **Giao diện CRM:** <http://dmx.localhost:8000/crm>
- **Giao diện quản trị (Desk):** <http://dmx.localhost:8000/app>

Đăng nhập bằng email của bạn (hoặc `quynhthu3677@gmail.com`) với mật khẩu `admin123`.

## 3. Dùng hằng ngày

| Việc cần làm | Lệnh |
|---|---|
| Tạm dừng (giữ nguyên dữ liệu) | `docker compose stop` |
| Chạy lại | `docker compose start` (chỉ vài giây) |
| Xem log | `docker compose logs -f frappe` |
| Mở terminal bench | `docker compose exec frappe bash` rồi `cd frappe-bench` |
| Sao lưu dữ liệu vào `backup/` | `.\scripts\backup.ps1` (Windows) hoặc `bash scripts/backup.sh` |
| Xoá hết & khôi phục lại từ backup | `.\scripts\reset.ps1` |

> ⚠️ Lệnh `docker compose down` xoá container. Lần `up` sau sẽ **khôi phục lại từ bản backup mới nhất** trong `backup/`. Hãy chạy `backup.ps1` trước nếu muốn giữ dữ liệu mới.

### Chia sẻ dữ liệu mới cho cả nhóm
1. `.\scripts\backup.ps1` → file backup mới xuất hiện trong `backup/` (xoá bản cũ nếu không cần).
2. `git add backup && git commit -m "Cập nhật dữ liệu" && git push`
3. Thành viên khác: `git pull` rồi `.\scripts\reset.ps1`.

## 4. Những gì đã cấu hình (A4.2.1)

| # | Tiêu chí | Vị trí trên hệ thống | Ảnh minh chứng |
|---|---|---|---|
| 1 | Tiền tệ VND, múi giờ Asia/Ho_Chi_Minh, Tiếng Việt + English | `/app/system-settings`, `/app/global-defaults`, `/app/language` | `docs/screenshots/01_cau_hinh_chung.png` |
| 2 | Người dùng, phòng ban, phân quyền | `/app/user`, `/app/employee`, `/app/department` | `02_nguoi_dung_phan_quyen.png` |
| 3 | Avatar tài khoản chính | `/app/user/quynhthu3677@gmail.com` | `03_avatar_admin.png` |
| 4 | Cấu hình mail (Email Domain + Email Account) | `/app/email-account` | `04_cau_hinh_mail.png` |
| 5 | Sales team + chỉ tiêu | `/app/sales-person/view/tree` | `05_sales_teams.png` |
| 6 | Pipeline (Deal stages), Lead status, Lead source | `/crm/deals/view/kanban`, `/app/crm-deal-status` | `06_pipeline_lead.png` |
| 7 | Nguyên nhân thất bại | `/app/crm-lost-reason` | `07_nguyen_nhan_that_bai.png` |
| 8 | Layout báo giá / hóa đơn | Print Format *Báo giá Điện Máy Xanh*, *Hóa đơn Điện Máy Xanh* | `08_layout_tai_lieu.png` |


### Gửi mail thật bằng Gmail
1. Bật xác minh 2 bước cho Gmail → tạo **App Password** tại <https://myaccount.google.com/apppasswords>.
2. Vào `/app/email-account/Điện Máy Xanh CSKH`, sửa *Địa chỉ email* thành Gmail của bạn và dán App Password vào ô *Mật khẩu* → **Lưu**.
3. Bỏ chế độ tắt mail: `docker compose exec frappe bash -c "cd frappe-bench && bench --site dmx.localhost set-config mute_emails 0"`.

## 5. Tự động hoá (thư mục `scripts/`)

| File | Chức năng |
|---|---|
| `configure_a421.py` | Cấu hình toàn bộ 8 mục A4.2.1 bằng Frappe API (dùng khi không có backup). Chạy lại nhiều lần vẫn an toàn. |
| `set_owner.py` | Tạo tài khoản quản trị theo `OWNER_EMAIL` trong `.env`. |
| `take_screenshots.py` | Dùng Playwright đăng nhập và chụp 8 ảnh minh chứng vào `docs/screenshots/`. |
| `build_report.py` | Sinh báo cáo Word từ file Markdown và chèn ảnh minh chứng (báo cáo chỉ lưu trên máy, không đưa lên GitHub). |
| `print_format_*.html` | Mẫu in Báo giá / Hóa đơn nhận diện Điện Máy Xanh (Jinja). |
| `backup.ps1`, `backup.sh`, `reset.ps1` | Sao lưu / khôi phục. |

Chụp lại ảnh minh chứng trên máy bạn (sau khi hệ thống đã chạy):

```powershell
pip install playwright pillow python-docx
python -m playwright install chromium
python scripts\take_screenshots.py --base http://dmx.localhost:8000 --user email_cua_ban@gmail.com --password admin123
python scripts\build_report.py
```

## 6. Xử lý sự cố

| Hiện tượng | Cách xử lý |
|---|---|
| `port is already allocated` | Đổi `HTTP_PORT=8080` trong `.env`, chạy lại `docker compose up -d`, truy cập `http://localhost:8080`. |
| Không mở được `dmx.localhost` | Dùng `http://localhost:8000`. |
| Log báo `$'\r': command not found` | Git đã đổi kết thúc dòng. Chạy `git config --global core.autocrlf input`, xoá thư mục và `git clone` lại. |
| Cài đặt bị gián đoạn (mất mạng, tắt máy) | `docker compose down` rồi `docker compose up -d` để chạy lại từ đầu. |
| Quên mật khẩu | `docker compose exec frappe bash -c "cd frappe-bench && bench --site dmx.localhost set-password email@gmail.com admin123"` |
| Máy chậm / build lỗi do thiếu RAM | Tăng RAM cho Docker Desktop (≥ 4 GB) rồi `docker compose restart frappe`. |

---
*Phiên bản đã kiểm thử: Frappe 15.126.1 · ERPNext 15.125.0 · Frappe CRM 15.0.1 (nhánh `version-15`) · MariaDB 10.11.*
