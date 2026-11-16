"""
Tạo/cập nhật tài khoản quản trị cá nhân theo biến môi trường OWNER_EMAIL, OWNER_FULL_NAME
(tiêu chí A4.3.2: email admin là email của sinh viên thực hiện).

Chạy trong thư mục frappe-bench/sites:
    ../env/bin/python /workspace/scripts/set_owner.py dmx.localhost
"""
import os
import sys

import frappe
from frappe.utils.password import update_password

ADMIN_ROLES = ["System Manager", "Sales Manager", "Sales Master Manager", "Sales User",
               "Accounts Manager", "Accounts User", "HR Manager"]


def main():
    site = sys.argv[1] if len(sys.argv) > 1 else "dmx.localhost"
    email = (os.environ.get("OWNER_EMAIL") or "").strip().lower()
    full_name = (os.environ.get("OWNER_FULL_NAME") or "").strip()
    password = os.environ.get("ADMIN_PASSWORD", "admin123")
    gmail_pw = (os.environ.get("GMAIL_APP_PASSWORD") or "").strip()
    if not email:
        print("[owner] OWNER_EMAIL trống – bỏ qua")
        return

    frappe.init(site=site, sites_path=".")
    frappe.connect()
    frappe.set_user("Administrator")

    if frappe.db.exists("User", email):
        user = frappe.get_doc("User", email)
    else:
        user = frappe.new_doc("User")
        user.email = email
        user.send_welcome_email = 0
    user.first_name = full_name or email.split("@")[0]
    user.middle_name = ""
    user.last_name = ""
    user.language = "vi"
    user.time_zone = "Asia/Ho_Chi_Minh"
    user.user_type = "System User"
    user.enabled = 1
    user.save(ignore_permissions=True)
    user.add_roles(*ADMIN_ROLES)
    update_password(email, password)

    if gmail_pw:
        acc = frappe.get_doc("Email Account", "Điện Máy Xanh CSKH")
        acc.email_id = email
        acc.password = gmail_pw
        acc.save(ignore_permissions=True)
        frappe.db.set_value("System Settings", None, "disable_system_update_notification", 1)

    frappe.db.commit()
    print(f"[owner] Tài khoản quản trị: {email} ({user.full_name}) – mật khẩu: {password}")
    frappe.destroy()


if __name__ == "__main__":
    main()
