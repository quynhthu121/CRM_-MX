# Xoá toàn bộ container + dữ liệu Docker và khôi phục lại từ bản backup mới nhất trong backup/.
# CẢNH BÁO: dữ liệu chưa sao lưu sẽ mất.
docker compose down -v
docker compose up -d
docker compose logs -f frappe
