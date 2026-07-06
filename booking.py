from playwright.sync_api import sync_playwright
import time

URL = "https://script.google.com/a/macros/banksinarmas.com/s/AKfycbyGVQZaMoU4Q4HOS51V2Tmt_nnO2UNu4QCfUbk6EWuGVYtamrhMMLoUv-kI1oGHU9-0Nw/exec?v=bookWorkSite"

# ==========================
# DATA
# ==========================
NIK = "12345678"
NAMA = "Nama Kamu"
DIVISI = "IT"
EMAIL = "email@banksinarmas.com"

WORKSITE = "L'Avenue"      # atau GOP 1
TANGGAL = "22/07/2025"

with sync_playwright() as p:

    browser = p.chromium.launch(headless=True)

    page = browser.new_page()

    print("Membuka website...")
    page.goto(URL, wait_until="networkidle")

    frame = page.frames[2]

    # ==========================
    # Isi data
    # ==========================

    print("Mengisi data...")

    frame.locator("#nik").fill(NIK)
    frame.locator("#nama").fill(NAMA)
    frame.locator("#divisi").fill(DIVISI)
    frame.locator("#email").fill(EMAIL)

    # ==========================
    # Work Site
    # ==========================

    print("Memilih Work Site...")

    frame.locator("#workSite").select_option(
        label=WORKSITE,
        force=True
    )

    # ==========================
    # Cek DatePicker
    # ==========================

    print("\n=== DATEPICKER INFO ===")

    try:

        info = frame.evaluate("""
        () => {
            const el = document.querySelector('#meetingDate');

            if (!window.M)
                return "Materialize tidak ditemukan";

            const inst = M.Datepicker.getInstance(el);

            if (!inst)
                return "Datepicker belum diinisialisasi";

            return {
                format: inst.options.format,
                minDate: inst.options.minDate,
                maxDate: inst.options.maxDate
            };
        }
        """)

        print(info)

    except Exception as e:
        print(e)

    # ==========================
    # Isi tanggal
    # ==========================

    print("\nMengisi tanggal...")

    frame.locator("#meetingDate").click()
    frame.locator("#meetingDate").fill(TANGGAL)
    frame.locator("#meetingDate").press("Enter")

    frame.locator("#meetingEnd").click()
    frame.locator("#meetingEnd").fill(TANGGAL)
    frame.locator("#meetingEnd").press("Enter")

    frame.locator("#meetingDate").dispatch_event("change")
    frame.locator("#meetingEnd").dispatch_event("change")

    time.sleep(3)

    print("\n=== VALUE YANG TERSIMPAN ===")

    print("Meeting Date :", frame.locator("#meetingDate").input_value())
    print("Meeting End  :", frame.locator("#meetingEnd").input_value())

    # ==========================
    # Status
    # ==========================

    time.sleep(3)

    status = frame.locator("#statusRuangan").inner_text()

    print("\n=== STATUS ===")
    print(status)

    browser.close()
