from playwright.sync_api import sync_playwright
import time

URL = "https://script.google.com/a/macros/banksinarmas.com/s/AKfycbyGVQZaMoU4Q4HOS51V2Tmt_nnO2UNu4QCfUbk6EWuGVYtamrhMMLoUv-kI1oGHU9-0Nw/exec?v=bookWorkSite"

NIK = "12345678"
NAMA = "Nama Kamu"
DIVISI = "IT"
EMAIL = "email@banksinarmas.com"

WORKSITE = "L'Avenue"
TANGGAL = "22/07/2025"


with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=True
    )

    page = browser.new_page()

    print("Membuka website...")
    page.goto(URL, wait_until="networkidle")

    frame = page.frames[2]

    print("Mengisi data...")

    frame.locator("#nik").fill(NIK)
    frame.locator("#nama").fill(NAMA)
    frame.locator("#divisi").fill(DIVISI)
    frame.locator("#email").fill(EMAIL)

    # pilih worksite
    frame.locator("#workSite").select_option(label=WORKSITE)

    # isi tanggal mulai
    frame.locator("#meetingDate").fill(TANGGAL)
    frame.locator("#meetingDate").press("Tab")

    # isi tanggal selesai
    frame.locator("#meetingEnd").fill(TANGGAL)
    frame.locator("#meetingEnd").press("Tab")

    # trigger onchange
    frame.locator("#meetingDate").dispatch_event("change")
    frame.locator("#meetingEnd").dispatch_event("change")

    print("Menunggu pengecekan ruangan...")

    time.sleep(5)

    status = frame.locator("#statusRuangan").inner_text()

    print("STATUS:")
    print(status)

    if "Available" in status or "available" in status:
        print("Ruangan tersedia")
        frame.locator("#submit-reservation-detail").click()
        print("Reservasi dikirim")
    else:
        print("Ruangan belum tersedia")

    time.sleep(3)

    browser.close()
