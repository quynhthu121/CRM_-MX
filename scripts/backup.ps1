# Sao lưu toàn bộ dữ liệu site (DB + file) vào thư mục backup/ của repo.
# Chạy trong PowerShell tại thư mục gốc repo:   .\scripts\backup.ps1
docker compose exec frappe bash -c 'cd ~/frappe-bench && bench --site $SITE_NAME backup --with-files && cd sites/$SITE_NAME/private/backups && for f in $(ls -t | head -4); do cp "$f" /workspace/backup/; done && ls -la /workspace/backup'
Write-Host "Da sao luu vao thu muc backup\. Xoa cac file backup cu neu khong can, roi commit + push de ca nhom dung chung." -ForegroundColor Green
