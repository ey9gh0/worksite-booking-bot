from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import pandas as pd

URL = "https://script.google.com/a/macros/banksinarmas.com/s/AKfycbyGVQZaMoU4Q4HOS51V2Tmt_nnO2UNu4QCfUbk6EWuGVYtamrhMMLoUv-kI1oGHU9-0Nw/exec?v=bookWorkSite"

# =====================================================
# HITUNG HARI KERJA BERIKUTNYA
# =====================================================

today = datetime.today()

booking_date = today + timedelta(days=1)

while booking_date.weekday() >= 5:
    booking_date += timedelta(days=1)

TANGGAL = booking_date.strftime("%b %d, %Y").replace(" 0", " ")

print("=" * 60)
print("Tanggal Booking :", TANGGAL)
print("=" * 60)

# =====================================================
# BACA EXCEL
# =====================================================

df = pd.read_excel("booking.xlsx")

# =====================================================
# PLAYWRIGHT
# =====================================================

with sync_playwright() as p:

    browser = p.chromium.launch(headless=True)

    page = browser.new_page()

    page.on(
        "dialog",
        lambda dialog: (
            print("\n=== DIALOG ==="),
            print(dialog.message),
            dialog.accept()
        )
    )

    for index, row in df.iterrows():

        print("\n")
        print("=" * 60)
        print(f"USER {index+1}")
        print("=" * 60)

        NIK = str(row["NIK"]).strip()
        NAMA = str(row["NAMA"]).strip()
        DIVISI = str(row["DIVISI"]).strip()
        EMAIL = str(row["EMAIL"]).strip()
        WORKSITE = str(row["WORKSITE"]).strip()

        print("Nama :", NAMA)
        print("Worksite :", WORKSITE)

        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(3000)

        frame = page.frames[2]

        # =======================================
        # Isi Form
        # =======================================

        frame.locator("#nik").fill(NIK)
        frame.locator("#nama").fill(NAMA)
        frame.locator("#divisi").fill(DIVISI)
        frame.locator("#email").fill(EMAIL)

        # =======================================
        # WORKSITE
        # =======================================

        frame.evaluate(
            """
            (site)=>{

                const select=document.querySelector("#workSite");

                for(const opt of select.options){

                    if(opt.text.trim()==site){

                        select.value=opt.value || opt.text;
                        break;

                    }

                }

                select.dispatchEvent(new Event("change",{bubbles:true}));

                if(window.M){

                    const inst=M.FormSelect.getInstance(select);

                    if(inst) inst.destroy();

                    M.FormSelect.init(select);

                }

            }
            """,
            WORKSITE
        )

        page.wait_for_timeout(1000)

        # =======================================
        # TANGGAL
        # =======================================

        frame.evaluate(
            """
            (tgl)=>{

                const start=document.querySelector("#meetingDate");
                const end=document.querySelector("#meetingEnd");

                start.value=tgl;
                end.value=tgl;

                start.dispatchEvent(new Event("input",{bubbles:true}));
                end.dispatchEvent(new Event("input",{bubbles:true}));

                start.dispatchEvent(new Event("change",{bubbles:true}));
                end.dispatchEvent(new Event("change",{bubbles:true}));

                if(typeof checkRoom==="function"){
                    checkRoom();
                }

            }
            """,
            TANGGAL
        )

        page.wait_for_timeout(5000)

        status = frame.locator("#statusRuangan").inner_text()

        print("Status :", status)

        if "available" not in status.lower():

            print("Skip karena ruangan penuh.")
            continue

        print("Ruangan tersedia.")

        button = frame.locator("#submit-reservation-detail")

        button.click(force=True)

        page.wait_for_timeout(3000)

        # =======================================
        # Popup Materialize
        # =======================================

        try:

            modal = frame.locator(".modal.open")

            if modal.count() > 0:

                btns = modal.locator("button")

                for i in range(btns.count()):

                    text = btns.nth(i).inner_text().strip().lower()

                    if text in [
                        "ok",
                        "yes",
                        "submit",
                        "confirm",
                        "continue"
                    ]:

                        btns.nth(i).click(force=True)

                        print("Popup dikonfirmasi")

                        break

        except:
            pass

        page.wait_for_timeout(5000)

        print("Booking selesai.")

    browser.close()
