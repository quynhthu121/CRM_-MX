"""
Cấu hình Frappe CRM + ERPNext cho Điện Máy Xanh theo tiêu chí A4.2.1.

Chạy bên trong bench (đứng ở thư mục frappe-bench/sites):
    ../env/bin/python /workspace/scripts/configure_a421.py dmx.localhost

Script idempotent: chạy lại nhiều lần không tạo trùng dữ liệu.
"""
import os
import sys

import frappe
from frappe.utils import add_days, getdate, nowdate

SITE = sys.argv[1] if len(sys.argv) > 1 else "dmx.localhost"
REPO = os.environ.get("REPO_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

COMPANY = "Công ty CP Thế Giới Di Động - Điện Máy Xanh"
ABBR = "DMX"
OWNER = {"email": "quynhthu3677@gmail.com", "full_name": "Đinh Thị Quỳnh Thư"}

MEMBERS = [
    # email, first_name (họ tên đầy đủ kiểu Việt Nam), last_name, department, designation, roles
    ("quynhthu3677@gmail.com", "Đinh Thị Quỳnh Thư", "", "Ban Quản trị CRM", "Quản trị hệ thống CRM",
     ["System Manager", "Sales Manager", "Sales Master Manager", "Sales User", "Accounts Manager", "Accounts User", "HR Manager"]),
    ("nnghan23@gmail.com", "Nguyễn Ngô Gia Hân", "", "Phòng Kinh doanh", "Trưởng nhóm Kinh doanh",
     ["Sales Manager", "Sales Master Manager", "Sales User", "Accounts User"]),
    ("nchphuong06@gmail.com", "Nguyễn Châu Hoàng Phương", "", "Phòng Chăm sóc Khách hàng", "Nhân viên Tư vấn & CSKH",
     ["Sales User", "Support Team"]),
    ("thachthanhthuy287@gmail.com", "Thạch Thanh Thủy", "", "Phòng Marketing", "Nhân viên Marketing",
     ["Sales User", "Marketing User"]),
]


def log(msg):
    print(f"[A4.2.1] {msg}", flush=True)


def upsert(doctype, name, values, name_field=None):
    """Tạo hoặc cập nhật 1 document theo tên."""
    if name and frappe.db.exists(doctype, name):
        doc = frappe.get_doc(doctype, name)
        doc.update(values)
        doc.save(ignore_permissions=True)
    else:
        doc = frappe.get_doc({"doctype": doctype, **values})
        doc.insert(ignore_permissions=True)
    return doc


# ---------------------------------------------------------------- 1. Cấu hình chung
def setup_general():
    from frappe.desk.page.setup_wizard.setup_wizard import setup_complete

    if not frappe.is_setup_complete():
        log("Chạy Setup Wizard (công ty, quốc gia, tiền tệ, múi giờ)…")
        setup_complete({
            "language": "English",
            "country": "Vietnam",
            "timezone": "Asia/Ho_Chi_Minh",
            "currency": "VND",
            "full_name": OWNER["full_name"],
            "email": OWNER["email"],
            "password": PASSWORD,
            "company_name": COMPANY,
            "company_abbr": ABBR,
            "chart_of_accounts": "Standard",
            "fy_start_date": "2026-01-01",
            "fy_end_date": "2026-12-31",
            "setup_demo": 0,
            "enable_telemetry": 0,
        })
        frappe.db.commit()

    log("System Settings: Vietnam / VND / Asia/Ho_Chi_Minh / Tiếng Việt")
    ss = frappe.get_doc("System Settings")
    ss.country = "Vietnam"
    ss.time_zone = "Asia/Ho_Chi_Minh"
    ss.language = "vi"
    ss.currency = "VND"
    ss.date_format = "dd-mm-yyyy"
    ss.time_format = "HH:mm"
    ss.number_format = "#.###,##"
    ss.currency_precision = "0"
    ss.float_precision = "2"
    ss.first_day_of_the_week = "Monday"
    ss.app_name = "Điện Máy Xanh CRM"
    ss.enable_onboarding = 0
    ss.save(ignore_permissions=True)

    gd = frappe.get_doc("Global Defaults")
    gd.default_currency = "VND"
    gd.country = "Vietnam"
    gd.default_company = COMPANY
    gd.save(ignore_permissions=True)

    cur = frappe.get_doc("Currency", "VND")
    cur.enabled = 1
    cur.symbol = "₫"
    cur.symbol_on_right = 1
    cur.number_format = "#.###"
    cur.fraction_units = 0
    cur.smallest_currency_fraction_value = 1
    cur.save(ignore_permissions=True)

    # Ngôn ngữ: chỉ bật Tiếng Việt + English
    for lang in frappe.get_all("Language", pluck="name"):
        frappe.db.set_value("Language", lang, "enabled", 1 if lang in ("vi", "en") else 0)
    frappe.db.set_value("Language", "vi", "language_name", "Tiếng Việt")

    # Logo ứng dụng / công ty
    logo = attach_file(os.path.join(REPO, "assets", "logo_dienmayxanh.png"), "Company", COMPANY, "company_logo")
    frappe.db.set_value("Company", COMPANY, {
        "company_logo": logo,
        "phone_no": "1800 1061",
        "email": "cskh@dienmayxanh.com",
        "website": "https://www.dienmayxanh.com",
        "company_description": "Hệ thống bán lẻ điện máy, điện tử, gia dụng Điện Máy Xanh",
    })
    nb = frappe.get_doc("Navbar Settings")
    nb.app_logo = logo
    nb.save(ignore_permissions=True)
    ws = frappe.get_doc("Website Settings")
    ws.app_logo = logo
    ws.app_name = "Điện Máy Xanh CRM"
    ws.save(ignore_permissions=True)

    # Frappe CRM: tiền tệ gốc VND, thương hiệu Điện Máy Xanh
    crm = frappe.get_doc("FCRM Settings")
    crm.currency = "VND"
    crm.brand_name = "Điện Máy Xanh CRM"
    crm.brand_logo = logo
    crm.favicon = logo
    crm.enable_forecasting = 1
    crm.enable_sales_hierarchy = 1
    crm.setup_completed = 1
    crm.save(ignore_permissions=True)

    # Địa chỉ công ty (hiển thị trên báo giá)
    if not frappe.db.exists("Address", {"address_title": "Điện Máy Xanh - Trụ sở"}):
        frappe.get_doc({
            "doctype": "Address",
            "address_title": "Điện Máy Xanh - Trụ sở",
            "address_type": "Office",
            "address_line1": "128 Trần Quang Khải, Phường Tân Định",
            "city": "TP. Hồ Chí Minh",
            "country": "Vietnam",
            "phone": "1800 1061",
            "email_id": "cskh@dienmayxanh.com",
            "is_your_company_address": 1,
            "links": [{"link_doctype": "Company", "link_name": COMPANY}],
        }).insert(ignore_permissions=True)


def attach_file(path, doctype, docname, field=None, is_private=0):
    fname = os.path.basename(path)
    existing = frappe.db.get_value("File", {"file_name": fname, "attached_to_doctype": doctype,
                                            "attached_to_name": docname}, "file_url")
    if existing:
        return existing
    with open(path, "rb") as f:
        content = f.read()
    fdoc = frappe.get_doc({
        "doctype": "File", "file_name": fname, "content": content, "is_private": is_private,
        "attached_to_doctype": doctype, "attached_to_name": docname, "attached_to_field": field,
    }).insert(ignore_permissions=True)
    return fdoc.file_url


# ---------------------------------------------------------------- 2. Người dùng & phân quyền
def setup_users():
    log("Tạo Role 'Marketing User' và quyền trên Lead/Campaign")
    if not frappe.db.exists("Role", "Marketing User"):
        frappe.get_doc({"doctype": "Role", "role_name": "Marketing User", "desk_access": 1}).insert()
    from frappe.permissions import add_permission, update_permission_property
    for dt, perms in {
        "Lead": ["read", "write", "create", "report", "export"],
        "Campaign": ["read", "write", "create", "delete", "report", "export"],
        "Lead Source": ["read", "write", "create"],
        "CRM Lead": ["read", "write", "create", "report", "export"],
        "CRM Lead Source": ["read", "write", "create"],
        "UTM Campaign": ["read", "write", "create"],
    }.items():
        if not frappe.db.exists("DocType", dt):
            continue
        add_permission(dt, "Marketing User", 0)
        for p in perms:
            update_permission_property(dt, "Marketing User", 0, p, 1)

    log("Tạo phòng ban, chức danh, tài khoản và nhân viên")
    for dept in ["Ban Quản trị CRM", "Phòng Kinh doanh", "Phòng Chăm sóc Khách hàng", "Phòng Marketing"]:
        full = f"{dept} - {ABBR}"
        if not frappe.db.exists("Department", full):
            frappe.get_doc({"doctype": "Department", "department_name": dept, "company": COMPANY,
                            "parent_department": "All Departments"}).insert(ignore_permissions=True)

    for email, first, last, dept, desig, roles in MEMBERS:
        if not frappe.db.exists("Designation", desig):
            frappe.get_doc({"doctype": "Designation", "designation_name": desig}).insert()
        if frappe.db.exists("User", email):
            user = frappe.get_doc("User", email)
        else:
            user = frappe.new_doc("User")
            user.email = email
        user.first_name = first
        user.middle_name = ""
        user.last_name = last
        user.language = "vi"
        user.time_zone = "Asia/Ho_Chi_Minh"
        user.send_welcome_email = 0
        user.user_type = "System User"
        user.enabled = 1
        user.save(ignore_permissions=True)
        user.add_roles(*roles)
        from frappe.utils.password import update_password
        update_password(email, PASSWORD)

        if not frappe.db.exists("Employee", {"user_id": email}):
            frappe.get_doc({
                "doctype": "Employee", "first_name": first, "last_name": last,
                "company": COMPANY, "department": f"{dept} - {ABBR}", "designation": desig,
                "user_id": email, "personal_email": email, "prefered_email": email,
                "gender": "Prefer not to say", "date_of_birth": "2004-01-01",
                "date_of_joining": "2026-09-01", "status": "Active", "create_user_permission": 0,
            }).insert(ignore_permissions=True)

    # Hiện cột Phòng ban trong danh sách Nhân viên
    from frappe.custom.doctype.property_setter.property_setter import make_property_setter
    make_property_setter("Employee", "department", "in_list_view", 1, "Check")

    # Chủ tài khoản quản trị: Administrator mang tên người cài đặt
    frappe.db.set_value("User", "Administrator", {"first_name": "Administrator (Quỳnh Thư)"})


def set_avatar():
    log("Cập nhật avatar cho Đinh Thị Quỳnh Thư")
    url = attach_file(os.path.join(REPO, "assets", "avatar_quynhthu.png"), "User", OWNER["email"], "user_image")
    frappe.db.set_value("User", OWNER["email"], "user_image", url)
    emp = frappe.db.get_value("Employee", {"user_id": OWNER["email"]})
    if emp:
        frappe.db.set_value("Employee", emp, "image", url)


# ---------------------------------------------------------------- 4. Email
def setup_email():
    log("Email Domain + Email Account (Gmail SMTP/IMAP)")
    frappe.local.flags.in_install = True  # bỏ qua bước thử kết nối khi tạo (máy chủ chưa có App Password)
    try:
        upsert("Email Domain", "gmail.com", {
            "domain_name": "gmail.com", "email_server": "imap.gmail.com", "use_imap": 1, "use_ssl": 1,
            "incoming_port": 993, "smtp_server": "smtp.gmail.com", "use_tls": 1, "smtp_port": 587,
            "append_emails_to_sent_folder": 1,
        })
        upsert("Email Domain", "dienmayxanh.com", {
            "domain_name": "dienmayxanh.com", "email_server": "imap.dienmayxanh.com", "use_imap": 1,
            "use_ssl": 1, "incoming_port": 993, "smtp_server": "smtp.dienmayxanh.com", "use_tls": 1,
            "smtp_port": 587,
        })
        upsert("Email Account", "Điện Máy Xanh CSKH", {
            "email_account_name": "Điện Máy Xanh CSKH",
            "email_id": OWNER["email"],
            "domain": "gmail.com",
            "service": "GMail",
            "login_id_is_different": 0,
            "password": os.environ.get("GMAIL_APP_PASSWORD", "xxxx xxxx xxxx xxxx"),
            "awaiting_password": 0,
            "email_server": "imap.gmail.com", "use_imap": 1, "use_ssl": 1, "incoming_port": 993,
            "smtp_server": "smtp.gmail.com", "use_tls": 1, "smtp_port": 587,
            "enable_incoming": 1, "default_incoming": 1,
            "enable_outgoing": 1, "default_outgoing": 1,
            "always_use_account_email_id_as_sender": 1,
            "always_use_account_name_as_sender_name": 1,
            "create_contact": 1, "track_email_status": 1,
            "email_sync_option": "UNSEEN", "initial_sync_count": "100",
            "imap_folder": [{"folder_name": "INBOX", "append_to": "CRM Lead"}],
            "append_to": "CRM Lead",
            "add_signature": 1,
            "signature": "<p>Trân trọng,<br><b>Điện Máy Xanh</b> – Tổng đài 1800.1061 (miễn phí)<br>"
                         "https://www.dienmayxanh.com</p>",
            "footer": "Cảm ơn Quý khách đã tin tưởng Điện Máy Xanh!",
        })
    finally:
        frappe.local.flags.in_install = False


# ---------------------------------------------------------------- 5. Sales Teams
def setup_sales_team():
    log("Territory, Sales Person tree, chỉ tiêu và phân bổ theo mùa")
    if not frappe.db.exists("Territory", "Việt Nam"):
        frappe.get_doc({"doctype": "Territory", "territory_name": "Việt Nam",
                        "parent_territory": "All Territories", "is_group": 1}).insert()
    for t in ["TP. Hồ Chí Minh", "Hà Nội", "Đà Nẵng"]:
        if not frappe.db.exists("Territory", t):
            frappe.get_doc({"doctype": "Territory", "territory_name": t, "parent_territory": "Việt Nam"}).insert()
        if not frappe.db.exists("CRM Territory", t):
            frappe.get_doc({"doctype": "CRM Territory", "territory_name": t}).insert()

    # Phân bổ chỉ tiêu theo tháng (mùa cao điểm Tết, mùa nóng bán máy lạnh)
    dist_name = "Phân bổ theo mùa ĐMX 2026"
    months = ["January", "February", "March", "April", "May", "June", "July", "August",
              "September", "October", "November", "December"]
    pct = [12, 6, 7, 9, 10, 9, 8, 7, 7, 7, 8, 10]
    if not frappe.db.exists("Monthly Distribution", dist_name):
        frappe.get_doc({"doctype": "Monthly Distribution", "distribution_id": dist_name, "fiscal_year": "2026",
                        "percentages": [{"month": m, "percentage_allocation": p} for m, p in zip(months, pct)]
                        }).insert()

    for g in ["Điện tử - Điện máy", "Gia dụng"]:
        if not frappe.db.exists("Item Group", g):
            frappe.get_doc({"doctype": "Item Group", "item_group_name": g, "parent_item_group": "All Item Groups"}).insert()

    team = "Đội Bán Hàng Khu Vực TP.HCM - Điện Máy Xanh"
    if not frappe.db.exists("Sales Person", team):
        frappe.get_doc({"doctype": "Sales Person", "sales_person_name": team, "parent_sales_person": "Sales Team",
                        "is_group": 1, "enabled": 1}).insert()

    # (email, tên, tỷ lệ đóng góp %, hoa hồng %)
    TOTAL_TARGET = 8_000_000_000  # 8 tỷ VNĐ / năm cho cả đội
    alloc = [
        ("nnghan23@gmail.com", "Nguyễn Ngô Gia Hân", 35, 1.5),
        ("nchphuong06@gmail.com", "Nguyễn Châu Hoàng Phương", 25, 1.2),
        ("thachthanhthuy287@gmail.com", "Thạch Thanh Thủy", 20, 1.0),
        ("quynhthu3677@gmail.com", "Đinh Thị Quỳnh Thư", 20, 1.0),
    ]
    for email, name, share, comm in alloc:
        emp = frappe.db.get_value("Employee", {"user_id": email})
        target = TOTAL_TARGET * share / 100
        vals = {
            "sales_person_name": name, "parent_sales_person": team, "is_group": 0, "enabled": 1,
            "employee": emp, "commission_rate": str(comm),
            "targets": [
                {"item_group": "Điện tử - Điện máy", "fiscal_year": "2026", "target_qty": 0,
                 "target_amount": target * 0.7, "distribution_id": dist_name},
                {"item_group": "Gia dụng", "fiscal_year": "2026", "target_qty": 0,
                 "target_amount": target * 0.3, "distribution_id": dist_name},
            ],
        }
        upsert("Sales Person", name, vals)

    # Cấu trúc đội trong Frappe CRM (CRM Sales Hierarchy)
    if frappe.db.exists("DocType", "CRM Sales Hierarchy"):
        # Quỳnh Thư (quản trị) -> Gia Hân (trưởng nhóm KD) -> Hoàng Phương, Thanh Thủy
        tree = [
            ("quynhthu3677@gmail.com", "Đinh Thị Quỳnh Thư", None, 1),
            ("nnghan23@gmail.com", "Nguyễn Ngô Gia Hân", "quynhthu3677@gmail.com", 1),
            ("nchphuong06@gmail.com", "Nguyễn Châu Hoàng Phương", "nnghan23@gmail.com", 0),
            ("thachthanhthuy287@gmail.com", "Thạch Thanh Thủy", "nnghan23@gmail.com", 0),
        ]
        for email, name, parent, is_group in tree:
            if frappe.db.exists("CRM Sales Hierarchy", {"user": email}):
                continue
            parent_node = frappe.db.get_value("CRM Sales Hierarchy", {"user": parent}) if parent else None
            frappe.get_doc({"doctype": "CRM Sales Hierarchy", "full_name": name, "user": email,
                            "reports_to": parent_node, "is_group": is_group}).insert()


# ---------------------------------------------------------------- 6. Pipeline & Lead
DEAL_STAGES = [
    ("Tiếp nhận nhu cầu", "Open", "blue", 10),
    ("Tư vấn sản phẩm", "Ongoing", "cyan", 30),
    ("Gửi báo giá", "Ongoing", "amber", 50),
    ("Chốt đơn & Giao lắp", "Ongoing", "orange", 80),
    ("Hoàn tất", "Won", "green", 100),
    ("Thất bại", "Lost", "red", 0),
]
LEAD_STATUSES = [
    ("Mới", "Open", "gray"),
    ("Đã liên hệ", "Ongoing", "orange"),
    ("Đang chăm sóc", "Ongoing", "blue"),
    ("Qualified", "Won", "green"),  # giữ tên chuẩn để CRM tự gán khi chuyển Lead -> Deal (hiển thị: Đủ điều kiện)
    ("Không tiềm năng", "Lost", "red"),
]
LEAD_SOURCES = ["Website Điện Máy Xanh", "Tổng đài 1800.1061", "Zalo OA", "Cửa hàng trực tiếp",
                "Facebook Fanpage", "Khách hàng giới thiệu"]


def setup_pipeline():
    log("Deal stages, Lead status, Lead source")
    keep_deal = {s[0] for s in DEAL_STAGES}
    for i, (name, typ, color, prob) in enumerate(DEAL_STAGES, start=1):
        upsert("CRM Deal Status", name, {"deal_status": name, "type": typ, "color": color,
                                          "probability": prob, "position": i})
    keep_lead = {s[0] for s in LEAD_STATUSES}
    for i, (name, typ, color) in enumerate(LEAD_STATUSES, start=1):
        upsert("CRM Lead Status", name, {"lead_status": name, "type": typ, "color": color, "position": i})

    # Xoá trạng thái mặc định (tiếng Anh) không còn dùng
    for name in frappe.get_all("CRM Deal Status", pluck="name"):
        if name not in keep_deal and not frappe.db.exists("CRM Deal", {"status": name}):
            frappe.delete_doc("CRM Deal Status", name, force=1, ignore_permissions=True)
    for name in frappe.get_all("CRM Lead Status", pluck="name"):
        if name not in keep_lead and not frappe.db.exists("CRM Lead", {"status": name}):
            frappe.delete_doc("CRM Lead Status", name, force=1, ignore_permissions=True)

    # Dịch "Qualified" sang tiếng Việt
    if not frappe.db.exists("Translation", {"source_text": "Qualified", "language": "vi"}):
        frappe.get_doc({"doctype": "Translation", "language": "vi", "source_text": "Qualified",
                        "translated_text": "Đủ điều kiện"}).insert()

    for dt in ("CRM Lead Source", "Lead Source"):
        for name in frappe.get_all(dt, pluck="name"):
            if name not in LEAD_SOURCES:
                try:
                    frappe.delete_doc(dt, name, ignore_permissions=True)
                except frappe.LinkExistsError:
                    pass
    for s in LEAD_SOURCES:
        if not frappe.db.exists("CRM Lead Source", s):
            frappe.get_doc({"doctype": "CRM Lead Source", "source_name": s}).insert()
        if not frappe.db.exists("Lead Source", s):
            frappe.get_doc({"doctype": "Lead Source", "source_name": s}).insert()

    if not frappe.db.exists("CRM Industry", "Bán lẻ điện máy"):
        frappe.get_doc({"doctype": "CRM Industry", "industry": "Bán lẻ điện máy"}).insert()


# ---------------------------------------------------------------- 7. Lost reasons
LOST_REASONS = [
    ("Giá cao hơn đối thủ (Nguyễn Kim/Chợ Lớn)", "Khách so sánh giá và chọn mua ở đối thủ có giá/khuyến mãi tốt hơn."),
    ("Hết hàng/Không có sẵn model", "Model khách cần tạm hết hàng tại kho/cửa hàng gần nhất."),
    ("Khách thay đổi nhu cầu", "Khách hoãn mua hoặc chuyển sang nhu cầu sản phẩm khác."),
    ("Thời gian giao lắp chậm", "Lịch giao hàng/lắp đặt không đáp ứng thời gian khách mong muốn."),
    ("Không liên lạc được khách", "Gọi/nhắn Zalo nhiều lần nhưng khách không phản hồi."),
    ("Chính sách trả góp không phù hợp", "Khách không đủ điều kiện hoặc lãi suất trả góp chưa hấp dẫn."),
]


def setup_lost_reasons():
    log("Lost reasons (CRM + ERPNext)")
    ours = {r for r, _ in LOST_REASONS}
    for dt in ("CRM Lost Reason", "Opportunity Lost Reason"):
        for name in frappe.get_all(dt, pluck="name"):
            if name not in ours:
                try:
                    frappe.delete_doc(dt, name, ignore_permissions=True)
                except frappe.LinkExistsError:
                    pass
    for r, desc in LOST_REASONS:
        if not frappe.db.exists("CRM Lost Reason", r):
            frappe.get_doc({"doctype": "CRM Lost Reason", "lost_reason": r, "description": desc}).insert()
        if not frappe.db.exists("Opportunity Lost Reason", r):
            frappe.get_doc({"doctype": "Opportunity Lost Reason", "lost_reason": r}).insert()
        if not frappe.db.exists("Quotation Lost Reason", r):
            frappe.get_doc({"doctype": "Quotation Lost Reason", "order_lost_reason": r}).insert()


# ---------------------------------------------------------------- Dữ liệu mẫu
ITEMS = [
    ("TV-SS-55QLED", "Smart Tivi QLED Samsung 4K 55 inch", "Điện tử - Điện máy", 15_990_000),
    ("ML-DK-1HP", "Máy lạnh Daikin Inverter 1 HP", "Điện tử - Điện máy", 10_490_000),
    ("TL-PN-322L", "Tủ lạnh Panasonic Inverter 322 lít", "Điện tử - Điện máy", 12_890_000),
    ("MG-LG-10KG", "Máy giặt LG Inverter 10 kg", "Điện tử - Điện máy", 8_990_000),
    ("NCD-SH-1L8", "Nồi cơm điện Sharp 1.8 lít", "Gia dụng", 1_290_000),
    ("LVS-SS-23L", "Lò vi sóng Samsung 23 lít", "Gia dụng", 2_390_000),
    ("DV-LAPDAT", "Dịch vụ lắp đặt máy lạnh (vật tư tiêu chuẩn)", "Gia dụng", 300_000),
]

CUSTOMERS = [
    ("Nguyễn Minh Khang", "0909 123 456", "khang.nguyen@example.com", "TP. Hồ Chí Minh"),
    ("Trần Thị Bảo Ngọc", "0938 456 789", "ngoc.tran@example.com", "TP. Hồ Chí Minh"),
    ("Lê Hoàng Nam", "0912 345 678", "nam.le@example.com", "TP. Hồ Chí Minh"),
    ("Phạm Thu Hà", "0987 654 321", "ha.pham@example.com", "TP. Hồ Chí Minh"),
    ("Võ Quốc Bảo", "0903 222 333", "bao.vo@example.com", "TP. Hồ Chí Minh"),
    ("Đỗ Ngọc Anh", "0977 111 222", "anh.do@example.com", "TP. Hồ Chí Minh"),
    ("Huỳnh Gia Huy", "0966 888 999", "huy.huynh@example.com", "TP. Hồ Chí Minh"),
    ("Bùi Thị Mai", "0944 555 666", "mai.bui@example.com", "TP. Hồ Chí Minh"),
]


def setup_master_data():
    log("Sản phẩm, bảng giá, khách hàng mẫu")
    if not frappe.db.exists("Customer Group", "Khách lẻ"):
        frappe.get_doc({"doctype": "Customer Group", "customer_group_name": "Khách lẻ",
                        "parent_customer_group": "All Customer Groups"}).insert()
    frappe.db.set_value("Price List", "Standard Selling", "currency", "VND")
    for code, name, group, price in ITEMS:
        if not frappe.db.exists("Item", code):
            frappe.get_doc({"doctype": "Item", "item_code": code, "item_name": name, "item_group": group,
                            "stock_uom": "Nos", "is_stock_item": 0 if code.startswith("DV") else 1,
                            "description": name, "standard_rate": price}).insert()
        if not frappe.db.exists("Item Price", {"item_code": code, "price_list": "Standard Selling"}):
            frappe.get_doc({"doctype": "Item Price", "item_code": code, "price_list": "Standard Selling",
                            "price_list_rate": price, "currency": "VND"}).insert()
        if not frappe.db.exists("CRM Product", code):
            frappe.get_doc({"doctype": "CRM Product", "product_code": code, "product_name": name,
                            "standard_rate": price}).insert()

    for name, phone, email, terr in CUSTOMERS[:3]:
        if not frappe.db.exists("Customer", name):
            frappe.get_doc({"doctype": "Customer", "customer_name": name, "customer_type": "Individual",
                            "customer_group": "Khách lẻ", "territory": terr, "default_currency": "VND",
                            "mobile_no": phone, "email_id": email}).insert()


def setup_sample_crm():
    log("Lead/Deal mẫu cho pipeline")
    if frappe.db.count("CRM Lead") >= 8:
        return
    owners = [m[0] for m in MEMBERS]
    leads = [
        # khách, nguồn, trạng thái lead, sản phẩm quan tâm
        (CUSTOMERS[0], "Website Điện Máy Xanh", "Mới", "Smart Tivi QLED 55 inch"),
        (CUSTOMERS[1], "Tổng đài 1800.1061", "Đã liên hệ", "Máy lạnh Daikin 1 HP x2"),
        (CUSTOMERS[2], "Zalo OA", "Đang chăm sóc", "Tủ lạnh 300 lít"),
        (CUSTOMERS[3], "Cửa hàng trực tiếp", "Mới", "Máy giặt 10 kg"),
        (CUSTOMERS[4], "Facebook Fanpage", "Đã liên hệ", "Combo gia dụng nhà bếp"),
        (CUSTOMERS[5], "Website Điện Máy Xanh", "Đang chăm sóc", "Lò vi sóng + nồi cơm"),
        (CUSTOMERS[6], "Khách hàng giới thiệu", "Không tiềm năng", "Tivi 75 inch"),
        (CUSTOMERS[7], "Tổng đài 1800.1061", "Mới", "Máy lạnh 1.5 HP"),
    ]
    for i, ((name, phone, email, terr), src, status, need) in enumerate(leads):
        frappe.get_doc({
            "doctype": "CRM Lead", "first_name": name, "last_name": "",
            "salutation": None, "mobile_no": phone.replace(" ", ""), "email": email,
            "source": src, "status": status, "territory": terr, "industry": "Bán lẻ điện máy",
            "lead_owner": owners[i % 4], "organization": "",
            "annual_revenue": 0,
            "lost_reason": "Khách thay đổi nhu cầu" if status == "Không tiềm năng" else None,
        }).insert(ignore_permissions=True)

    # (khách hàng/tổ chức, người liên hệ, giai đoạn, giá trị, phụ trách)
    deals = [
        ("Gia đình anh Nguyễn Minh Khang", "Nguyễn Minh Khang", "Tiếp nhận nhu cầu", 15_990_000, owners[1]),
        ("Gia đình chị Trần Thị Bảo Ngọc", "Trần Thị Bảo Ngọc", "Tư vấn sản phẩm", 21_580_000, owners[2]),
        ("Gia đình anh Lê Hoàng Nam", "Lê Hoàng Nam", "Gửi báo giá", 32_670_000, owners[1]),
        ("Gia đình chị Phạm Thu Hà", "Phạm Thu Hà", "Chốt đơn & Giao lắp", 8_990_000, owners[3]),
        ("Khách sạn Hoa Sen Quận 1", "Võ Quốc Bảo", "Hoàn tất", 104_900_000, owners[0]),
        ("Gia đình chị Đỗ Ngọc Anh", "Đỗ Ngọc Anh", "Thất bại", 12_890_000, owners[2]),
        ("Công ty TNHH Nội thất Minh Phát", "Bùi Thị Mai", "Tư vấn sản phẩm", 52_450_000, owners[3]),
        ("Gia đình anh Huỳnh Gia Huy", "Huỳnh Gia Huy", "Gửi báo giá", 18_380_000, owners[1]),
    ]
    for org, cname, stage, value, owner in deals:
        if not frappe.db.exists("CRM Organization", org):
            frappe.get_doc({"doctype": "CRM Organization", "organization_name": org,
                            "industry": "Bán lẻ điện máy", "territory": "TP. Hồ Chí Minh",
                            "currency": "VND"}).insert(ignore_permissions=True)
        contact = frappe.db.get_value("Contact", {"first_name": cname})
        if not contact:
            phone, email = next((c[1], c[2]) for c in CUSTOMERS if c[0] == cname)
            c = frappe.get_doc({"doctype": "Contact", "first_name": cname,
                                "phone_nos": [{"phone": phone.replace(" ", ""), "is_primary_mobile_no": 1}],
                                "email_ids": [{"email_id": email, "is_primary": 1}]})
            c.insert(ignore_permissions=True)
            contact = c.name
        lost = stage == "Thất bại"
        d = frappe.get_doc({
            "doctype": "CRM Deal", "organization": org, "status": stage,
            "deal_value": value, "expected_deal_value": value, "deal_owner": owner,
            "first_name": cname, "lead_name": cname,
            "probability": next(p for s, t, c, p in DEAL_STAGES if s == stage),
            "expected_closure_date": add_days(nowdate(), 14), "territory": "TP. Hồ Chí Minh",
            "source": "Website Điện Máy Xanh", "currency": "VND",
            "contacts": [{"contact": contact, "is_primary": 1}],
            "lost_reason": "Giá cao hơn đối thủ (Nguyễn Kim/Chợ Lớn)" if lost else None,
            "lost_notes": "Khách báo Nguyễn Kim giảm thêm 1,2 triệu cho cùng model tủ lạnh." if lost else None,
        })
        d.insert(ignore_permissions=True)

    # View Kanban "Pipeline Điện Máy Xanh" dùng chung cho cả nhóm
    if not frappe.db.exists("CRM View Settings", {"label": "Pipeline Điện Máy Xanh"}):
        frappe.get_doc({
            "doctype": "CRM View Settings", "label": "Pipeline Điện Máy Xanh", "dt": "CRM Deal",
            "type": "kanban", "is_standard": 1, "public": 0, "pinned": 0, "icon": "",
            "route_name": "Deals", "column_field": "status", "title_field": "organization",
            "kanban_fields": '["expected_deal_value", "lead_name", "mobile_no", "deal_owner"]',
            "kanban_columns": frappe.as_json([{"name": s[0], "color": s[2]} for s in DEAL_STAGES]),
            "filters": "{}", "order_by": "modified desc",
        }).insert(ignore_permissions=True)
    # view chuẩn dùng chung: CRM chỉ lấy các view có user = '' (rỗng, không phải NULL)
    frappe.db.sql("update `tabCRM View Settings` set user='' where label=%s", "Pipeline Điện Máy Xanh")


# ---------------------------------------------------------------- 8. Print format
def setup_print_format():
    log("Letter Head + Print Format 'Báo giá Điện Máy Xanh'")
    logo = frappe.db.get_value("Company", COMPANY, "company_logo")
    with open(os.path.join(REPO, "scripts", "print_format_bao_gia.html"), encoding="utf-8") as f:
        html = f.read()
    upsert("Print Format", "Báo giá Điện Máy Xanh", {
        "name": "Báo giá Điện Máy Xanh", "doc_type": "Quotation", "module": "Selling",
        "custom_format": 1, "standard": "No", "print_format_type": "Jinja", "html": html,
        "font_size": 12, "disabled": 0, "align_labels_right": 0, "show_section_headings": 0,
        "line_breaks": 0, "absolute_value": 0, "margin_top": 10, "margin_bottom": 10,
        "margin_left": 10, "margin_right": 10,
    })
    with open(os.path.join(REPO, "scripts", "print_format_hoa_don.html"), encoding="utf-8") as f:
        html_inv = f.read()
    upsert("Print Format", "Hóa đơn Điện Máy Xanh", {
        "name": "Hóa đơn Điện Máy Xanh", "doc_type": "Sales Invoice", "module": "Accounts",
        "custom_format": 1, "standard": "No", "print_format_type": "Jinja", "html": html_inv,
        "font_size": 12, "disabled": 0,
    })
    from frappe.custom.doctype.property_setter.property_setter import make_property_setter
    make_property_setter("Quotation", None, "default_print_format", "Báo giá Điện Máy Xanh", "Data",
                         for_doctype=True, validate_fields_for_doctype=False)
    make_property_setter("Sales Invoice", None, "default_print_format", "Hóa đơn Điện Máy Xanh", "Data",
                         for_doctype=True, validate_fields_for_doctype=False)
    ps = frappe.get_doc("Print Settings")
    ps.pdf_page_size = "A4"
    ps.with_letterhead = 0
    ps.save(ignore_permissions=True)

    # Báo giá mẫu để xem trước
    if not frappe.db.exists("Quotation", {"party_name": "Lê Hoàng Nam"}):
        q = frappe.get_doc({
            "doctype": "Quotation", "quotation_to": "Customer", "party_name": "Lê Hoàng Nam",
            "company": COMPANY, "transaction_date": nowdate(), "valid_till": add_days(nowdate(), 7),
            "currency": "VND", "selling_price_list": "Standard Selling", "order_type": "Sales",
            "items": [
                {"item_code": "TL-PN-322L", "qty": 1, "rate": 12_890_000},
                {"item_code": "ML-DK-1HP", "qty": 1, "rate": 10_490_000},
                {"item_code": "MG-LG-10KG", "qty": 1, "rate": 8_990_000},
                {"item_code": "DV-LAPDAT", "qty": 1, "rate": 300_000},
            ],
            "terms": "Giá đã bao gồm VAT. Miễn phí giao hàng trong bán kính 20 km. "
                     "Bảo hành chính hãng; 1 đổi 1 trong 30 ngày nếu lỗi do nhà sản xuất.",
        })
        q.insert(ignore_permissions=True)
        q.db_set("owner", "nnghan23@gmail.com")


def main():
    frappe.init(site=SITE, sites_path=".")
    frappe.connect()
    frappe.set_user("Administrator")
    steps = [setup_general, setup_users, set_avatar, setup_email, setup_sales_team, setup_pipeline,
             setup_lost_reasons, setup_master_data, setup_sample_crm, setup_print_format]
    only = os.environ.get("ONLY")
    for step in steps:
        if only and step.__name__ not in only.split(","):
            continue
        step()
        frappe.db.commit()
    frappe.clear_cache()
    log("HOÀN TẤT")
    frappe.destroy()


if __name__ == "__main__":
    main()
