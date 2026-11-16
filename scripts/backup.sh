#!/bin/bash
# Sao lưu toàn bộ dữ liệu site (DB + file) vào thư mục backup/ của repo (macOS/Linux/Git Bash).
docker compose exec frappe bash -c 'cd ~/frappe-bench && bench --site $SITE_NAME backup --with-files && cd sites/$SITE_NAME/private/backups && for f in $(ls -t | head -4); do cp "$f" /workspace/backup/; done && ls -la /workspace/backup'
echo "Đã sao lưu vào backup/. Xoá các bản cũ nếu không cần, rồi commit + push để cả nhóm dùng chung."
