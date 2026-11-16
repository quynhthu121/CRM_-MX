#!/bin/bash
# Khởi tạo bench Frappe v15 + ERPNext + CRM trong container và khôi phục dữ liệu Điện Máy Xanh.
# Được gọi tự động bởi docker-compose (service "frappe"). Không cần chạy tay.
set -e

SITE="${SITE_NAME:-dmx.localhost}"
DB_ROOT_PASSWORD="${DB_ROOT_PASSWORD:-dmx@2026}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin123}"
BENCH=/home/frappe/frappe-bench
BACKUP_DIR=/workspace/backup
export REPO_DIR=/workspace

log() { echo -e "\n========== [DMX] $* ==========\n"; }

# MariaDB client trong image frappe/bench mặc định đòi SSL, còn server mariadb:10.11
# trong compose không bật TLS -> "ERROR 2026: SSL is required, but the server does not
# support it" khi `bench restore`. Tắt SSL cho client (chỉ dùng trong mạng nội bộ Docker).
cat > /home/frappe/.my.cnf <<'EOF'
[client]
skip-ssl

[mysqldump]
skip-ssl
EOF

# ---------------------------------------------------------------- Lần chạy sau: chỉ start
if [ -f "$BENCH/sites/$SITE/site_config.json" ] && [ -f "$BENCH/.dmx_ready" ]; then
  log "Bench đã sẵn sàng – khởi động server (http://$SITE:8000)"
  cd "$BENCH"
  exec bench start
fi

# ---------------------------------------------------------------- 1. bench init + apps
cd /home/frappe
if [ ! -d "$BENCH/apps/frappe" ]; then
  log "1/5 bench init (Frappe version-15) – mất vài phút"
  rm -rf "$BENCH"
  bench init --skip-redis-config-generation --frappe-branch version-15 frappe-bench
fi
cd "$BENCH"
bench set-mariadb-host mariadb
bench set-redis-cache-host redis://redis:6379
bench set-redis-queue-host redis://redis:6379
bench set-redis-socketio-host redis://redis:6379
sed -i '/redis/d' ./Procfile
sed -i '/watch/d' ./Procfile

if [ ! -d apps/erpnext ]; then
  log "2/5 Tải ERPNext version-15"
  bench get-app erpnext --branch version-15
fi
if [ ! -d apps/crm ]; then
  log "3/5 Tải Frappe CRM version-15"
  bench get-app crm --branch version-15
fi

# ---------------------------------------------------------------- 2. tạo site
log "4/5 Tạo site $SITE"
bench new-site "$SITE" --force \
  --mariadb-root-password "$DB_ROOT_PASSWORD" \
  --admin-password "$ADMIN_PASSWORD" \
  --mariadb-user-host-login-scope='%'

# ---------------------------------------------------------------- 3. khôi phục backup (hoặc cấu hình mới)
DB_BACKUP=$(ls "$BACKUP_DIR"/*-database.sql.gz 2>/dev/null | sort | tail -1 || true)
if [ -n "$DB_BACKUP" ]; then
  P="${DB_BACKUP%-database.sql.gz}"
  log "5/5 Khôi phục dữ liệu từ $(basename "$DB_BACKUP")"
  bench --site "$SITE" restore "$DB_BACKUP" \
    --with-public-files "$P-files.tar" \
    --with-private-files "$P-private-files.tar" \
    --db-root-password "$DB_ROOT_PASSWORD" \
    --admin-password "$ADMIN_PASSWORD" --force
  if [ -f "$P-site_config_backup.json" ]; then
    KEY=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('encryption_key',''))" "$P-site_config_backup.json")
    [ -n "$KEY" ] && bench --site "$SITE" set-config encryption_key "$KEY"
  fi
  bench --site "$SITE" migrate
else
  log "5/5 Không có backup – cài app và chạy script cấu hình A4.2.1"
  bench --site "$SITE" install-app erpnext
  bench --site "$SITE" install-app crm
  (cd sites && ../env/bin/python /workspace/scripts/configure_a421.py "$SITE")
fi

bench --site "$SITE" set-config mute_emails 1
bench --site "$SITE" set-config server_script_enabled 1
bench use "$SITE"

# Tài khoản quản trị cá nhân (OWNER_EMAIL trong .env)
(cd sites && ../env/bin/python /workspace/scripts/set_owner.py "$SITE") || true

touch "$BENCH/.dmx_ready"
log "HOÀN TẤT – mở http://$SITE:8000 (hoặc http://localhost:8000)"
exec bench start
