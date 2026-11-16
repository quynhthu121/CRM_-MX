"""
Tự động đăng nhập Frappe CRM và chụp 8 ảnh minh chứng cho tiêu chí A4.2.1.

    pip install playwright pillow
    python -m playwright install chromium
    python scripts/take_screenshots.py --base http://dmx.localhost:8000 \
        --user quynhthu3677@gmail.com --password admin123

Mỗi ảnh có thanh địa chỉ (URL thật của trang) phía trên để thấy rõ đường dẫn.
Ảnh nhiều phần được ghép dọc thành 1 file.
"""
import argparse
import os
import time
from urllib.parse import quote

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "docs", "screenshots")
W, H = 1440, 900


def font(size, bold=False):
    for p in ([r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
               "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def add_browser_bar(img: Image.Image, url: str, title: str) -> Image.Image:
    """Vẽ khung trình duyệt (tab + thanh URL) với URL thật của trang."""
    bar_h = 84
    out = Image.new("RGB", (img.width, img.height + bar_h), "#dee1e6")
    d = ImageDraw.Draw(out)
    # tab
    d.rounded_rectangle((12, 8, 380, 44), radius=8, fill="#ffffff")
    d.text((28, 16), (title[:38] + "…") if len(title) > 39 else title, font=font(15), fill="#202124")
    for i, c in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
        d.ellipse((img.width - 90 + i * 26, 18, img.width - 76 + i * 26, 32), fill=c)
    # toolbar + url
    d.rectangle((0, 44, img.width, bar_h), fill="#ffffff")
    d.text((18, 52), "←   →   ⟳", font=font(17), fill="#5f6368")
    d.rounded_rectangle((120, 50, img.width - 20, 78), radius=14, fill="#f1f3f4")
    d.text((140, 54), url, font=font(16), fill="#202124")
    out.paste(img, (0, bar_h))
    return out


def stack(images, gap=18):
    width = max(i.width for i in images)
    height = sum(i.height for i in images) + gap * (len(images) - 1)
    out = Image.new("RGB", (width, height), "#9aa0a6")
    y = 0
    for im in images:
        out.paste(im, (0, y))
        y += im.height + gap
    return out


class Shooter:
    def __init__(self, page, base):
        self.page, self.base = page, base.rstrip("/")

    def go(self, path, wait=2.5, selector=None):
        self.page.goto(self.base + path, wait_until="networkidle")
        if selector:
            self.page.wait_for_selector(selector, timeout=20000)
        time.sleep(wait)
        if path.startswith("/crm"):  # tắt bảng "Getting started" của Frappe CRM nếu đang mở
            for btn in self.page.query_selector_all("button[aria-label='Close']"):
                if btn.is_visible():
                    btn.click()
                    time.sleep(1)

    def shot(self, full=False, clip_h=None, js=None, width=None):
        if js:
            self.page.evaluate(js)
            time.sleep(0.8)
        path = os.path.join(OUT, "_tmp.png")
        if clip_h or width:
            self.page.set_viewport_size({"width": width or W, "height": clip_h or H})
            time.sleep(1.5)
        self.page.screenshot(path=path, full_page=full)
        if clip_h or width:
            self.page.set_viewport_size({"width": W, "height": H})
        img = Image.open(path).convert("RGB")
        if width and width != W:  # chụp rộng rồi thu nhỏ về khổ chuẩn
            img = img.resize((W, round(img.height * W / width)), Image.LANCZOS)
        os.remove(path)
        return add_browser_bar(img, self.page.url, self.page.title())

    def save(self, name, images):
        img = images[0] if len(images) == 1 else stack(images)
        img.save(os.path.join(OUT, name), optimize=True)
        print("saved", name, img.size)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://dmx.localhost:8000")
    ap.add_argument("--user", default="quynhthu3677@gmail.com")
    ap.add_argument("--password", default="admin123")
    ap.add_argument("--only", default="")
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--channel", default="chrome", help="chrome | msedge (khi không có chromium của Playwright)")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    only = set(a.only.split(",")) if a.only else None

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=not a.headed)
        except Exception:  # dùng Chrome/Edge có sẵn trên máy nếu chưa cài chromium của Playwright
            browser = p.chromium.launch(headless=not a.headed, channel=a.channel)
        ctx = browser.new_context(viewport={"width": W, "height": H}, locale="vi-VN",
                                  timezone_id="Asia/Ho_Chi_Minh", device_scale_factor=1)
        page = ctx.new_page()
        page.goto(a.base + "/login", wait_until="domcontentloaded")
        page.fill("#login_email", a.user)
        page.fill("#login_password", a.password)
        page.click(".btn-login")
        try:
            page.wait_for_function("document.cookie.includes('user_id=') && !document.cookie.includes('user_id=Guest')",
                                   timeout=30000)
        except Exception:
            raise SystemExit("Đăng nhập thất bại – kiểm tra email/mật khẩu")
        page.goto(a.base + "/app", wait_until="domcontentloaded")
        page.wait_for_function("window.frappe && frappe.boot && frappe.boot.user", timeout=60000)
        s = Shooter(page, a.base)
        hide_sidebar = "document.querySelector('.layout-side-section') && (document.querySelector('.layout-side-section').style.display='none')"

        def want(n):
            return only is None or n in only

        if want("01"):
            s.go("/app/system-settings", selector=".frappe-control[data-fieldname='time_zone']")
            a1 = s.shot(clip_h=1000)
            s.go("/app/global-defaults")
            a2 = s.shot(clip_h=520)
            s.go("/app/language?enabled=1", selector=".list-row")
            a3 = s.shot(clip_h=420)
            s.save("01_cau_hinh_chung.png", [a1, a2, a3])

        if want("02"):
            s.go("/app/user?user_type=System%20User", selector=".list-row")
            b1 = s.shot(clip_h=560)
            s.go("/app/employee?status=Active", selector=".list-row")
            b2 = s.shot(clip_h=500)
            s.go("/app/user/nnghan23@gmail.com")
            page.click("#user-roles_permissions_tab-tab", timeout=8000)
            time.sleep(1.5)
            b3 = s.shot(clip_h=900)
            s.save("02_nguoi_dung_phan_quyen.png", [b1, b2, b3])

        if want("03"):
            s.go("/app/user/quynhthu3677@gmail.com")
            c1 = s.shot(clip_h=760)
            s.go("/crm/leads")
            c2 = s.shot(clip_h=520)
            s.save("03_avatar_admin.png", [c1, c2])

        if want("04"):
            s.go("/app/email-account/" + quote("Điện Máy Xanh CSKH"))
            d1 = s.shot(clip_h=1500)
            s.go("/app/email-domain", selector=".list-row")
            d2 = s.shot(clip_h=380)
            s.save("04_cau_hinh_mail.png", [d1, d2])

        if want("05"):
            s.go("/app/sales-person/view/tree", wait=3)
            # mở rộng toàn bộ cây
            page.click("button:has-text('Mở rộng tất cả'), button:has-text('Expand All')")
            time.sleep(3)
            e1 = s.shot(clip_h=620)
            s.go("/app/sales-person/" + quote("Nguyễn Ngô Gia Hân"))
            page.evaluate("document.querySelector(\"[data-fieldname='targets']\").scrollIntoView({block: 'center'})")
            time.sleep(1.5)
            e2 = s.shot(clip_h=760)
            s.save("05_sales_teams.png", [e1, e2])

        if want("06"):
            s.go("/crm/deals/view/kanban", wait=4)
            f1 = s.shot(clip_h=900, width=1960)
            s.go("/crm/leads/view/list", wait=4)
            f2 = s.shot(clip_h=620)
            s.go("/app/crm-deal-status?order_by=position%20asc", selector=".list-row")
            f3 = s.shot(clip_h=480)
            s.go("/app/crm-lead-source", selector=".list-row")
            f4 = s.shot(clip_h=480)
            s.save("06_pipeline_lead.png", [f1, f2, f3, f4])

        if want("07"):
            s.go("/app/crm-lost-reason", selector=".list-row")
            g1 = s.shot(clip_h=520)
            deal = page.evaluate("""() => frappe.db.get_value('CRM Deal', {status: 'Thất bại'}, 'name').then(r => r.message.name)""")
            s.go(f"/crm/deals/{deal}", wait=4)
            g2 = s.shot(clip_h=620)
            s.go(f"/app/crm-deal/{deal}", wait=3)
            tab = page.query_selector(".form-tabs .nav-link:has-text('thất bại'), .form-tabs .nav-link:has-text('Lost')")
            if tab:
                tab.click()
                time.sleep(1.5)
            g3 = s.shot(clip_h=620)
            s.save("07_nguyen_nhan_that_bai.png", [g1, g2, g3])

        if want("08"):
            s.go("/app/quotation", selector=".list-row")
            q = page.evaluate("""() => frappe.db.get_value('Quotation', {party_name: 'Lê Hoàng Nam'}, 'name').then(r => r.message.name)""")
            s.go(f"/app/print/Quotation/{q}", wait=5)
            h1 = s.shot(clip_h=1500)
            s.save("08_layout_tai_lieu.png", [h1])

        browser.close()


if __name__ == "__main__":
    main()
