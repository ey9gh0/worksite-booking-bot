from playwright.sync_api import sync_playwright
import time

URL = "https://script.google.com/a/macros/banksinarmas.com/s/AKfycbyGVQZaMoU4Q4HOS51V2Tmt_nnO2UNu4QCfUbk6EWuGVYtamrhMMLoUv-kI1oGHU9-0Nw/exec?v=bookWorkSite"

# =========================
# DATA
# =========================
NIK = "12345678"
NAMA = "Nama Kamu"
DIVISI = "IT"
EMAIL = "email@banksinarmas.com"

WORKSITE = "L'Avenue"      # atau GOP 1
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

    # =========================
    # WORKSITE
    # =========================

    try:
        print("Memilih worksite dengan select_option...")

        frame.locator("#workSite").select_option(
            label=WORKSITE,
            force=True
        )

    except Exception as e:

        print("select_option gagal")
        print(e)

        print("Menggunakan JavaScript...")

        frame.locator("#workSite").evaluate(
            """(el, value) => {
                el.value = value;

                el.dispatchEvent(new Event('change', {
                    bubbles: true
                }));

                if (typeof checkRoom === 'function'){
                    checkRoom();
                }
            }""",
            WORKSITE
        )

    # =========================
    # TANGGAL
    # =========================

    frame.locator("#meetingDate").fill(TANGGAL)
    frame.locator("#meetingDate").dispatch_event("change")

    frame.locator("#meetingEnd").fill(TANGGAL)
    frame.locator("#meetingEnd").dispatch_event("change")

    print("Menunggu checkRoom()...")

    time.sleep(5)

    status = frame.locator("#statusRuangan").inner_text()

    print("===========================")
    print(status)
    print("===========================")

    if "available" in status.lower():
        print("Ruangan tersedia")

        frame.locator("#submit-reservation-detail").click()

        print("Reservasi berhasil dikirim")

    else:
        print("Ruangan belum tersedia")

    time.sleep(3)

    browser.close()
