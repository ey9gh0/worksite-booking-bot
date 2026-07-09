from playwright.sync_api import sync_playwright, expect
from openpyxl import load_workbook
from datetime import datetime, timedelta
import random
import time

URL = "https://script.google.com/a/macros/banksinarmas.com/s/AKfycbyGVQZaMoU4Q4HOS51V2Tmt_nnO2UNu4QCfUbk6EWuGVYtamrhMMLoUv-kI1oGHU9-0Nw/exec?v=bookWorkSite"


# =====================================================
# RANDOM DELAY (HUMAN-LIKE)
# =====================================================

def random_delay(min_sec=2, max_sec=7):
    delay = random.uniform(min_sec, max_sec)
    print(f"⏳ Delay {delay:.2f} seconds...")
    time.sleep(delay)


def short_delay(min_ms=500, max_ms=1500):
    time.sleep(random.uniform(min_ms, max_ms) / 1000)


# =====================================================
# LOAD BOOKING DATA
# =====================================================

def load_booking_data():
    wb = load_workbook("booking.xlsx")
    ws = wb.active

    data = []

    for row in ws.iter_rows(min_row=2, values_only=True):

        if all(cell is None for cell in row):
            continue

        data.append({
            "NIK": str(row[0]).strip(),
            "NAMA": str(row[1]).strip(),
            "DIVISI": str(row[2]).strip(),
            "EMAIL": str(row[3]).strip(),
            "WORKSITE": str(row[4]).strip()
        })

    return data


# =====================================================
# NEXT WEEK MONDAY & FRIDAY GENERATOR
# =====================================================

def get_next_week_range():
    today = datetime.today().date()
    # Menghitung jumlah hari menuju hari Senin di minggu depan
    days_until_next_monday = 7 - today.weekday()
    
    next_monday = today + timedelta(days=days_until_next_monday)
    next_friday = next_monday + timedelta(days=4)
    
    # Format sesuai kebutuhan Materialize Datepicker (Contoh: "Jul 13, 2026")
    start_date_str = next_monday.strftime("%b %d, %Y")
    end_date_str = next_friday.strftime("%b %d, %Y")
    
    return start_date_str, end_date_str


# =====================================================
# MAIN DATA
# =====================================================

booking_data = load_booking_data()
START_DATE, END_DATE = get_next_week_range()

print(f"\n📅 Booking Periode Minggu Depan:")
print(f"   Tanggal Mulai (Senin) : {START_DATE}")
print(f"   Tanggal Selesai (Jumat): {END_DATE}\n")

results = []


# =====================================================
# PLAYWRIGHT
# =====================================================

with sync_playwright() as p:

    browser = p.chromium.launch(headless=True)

    for idx, user in enumerate(booking_data, start=1):

        print("\n" + "=" * 60)
        print(f"[{idx}/{len(booking_data)}] Booking : {user['NAMA']}")

        # delay antar user (biar tidak burst)
        random_delay(3, 10)

        page = browser.new_page()

        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(random.randint(2000, 4000))

        # =================================================
        # FIND FRAME
        # =================================================

        frame = None
        for f in page.frames:
            if f.locator("#nik").count() > 0:
                frame = f
                break

        if frame is None:
            print("❌ Form booking tidak ditemukan.")
            results.append({
                "name": user["NAMA"],
                "status": "FAILED (Frame)"
            })
            page.close()
            continue

        # =================================================
        # INPUT FORM
        # =================================================

        frame.locator("#nik").fill(user["NIK"])
        short_delay()

        frame.locator("#nama").fill(user["NAMA"])
        short_delay()

        frame.locator("#divisi").fill(user["DIVISI"])
        short_delay()

        frame.locator("#email").fill(user["EMAIL"])
        short_delay()

        expect(frame.locator("#nik")).to_have_value(user["NIK"])

        print("✔ Form berhasil diisi")

        # =================================================
        # WORKSITE
        # =================================================

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

                    M.FormSelect.init(select);

                }

            }
            """,
            user["WORKSITE"]
        )

        page.wait_for_timeout(random.randint(1000, 2500))

        # =================================================
        # DATE SET (Monday to Friday)
        # =================================================

        frame.evaluate(
            """
            (dates)=>{

                const startInput = document.getElementById("meetingDate");
                const endInput = document.getElementById("meetingEnd");

                startInput.value = dates.start;
                endInput.value = dates.end;

                startInput.dispatchEvent(new Event("input",{bubbles:true}));
                endInput.dispatchEvent(new Event("input",{bubbles:true}));

                startInput.dispatchEvent(new Event("change",{bubbles:true}));
                endInput.dispatchEvent(new Event("change",{bubbles:true}));

                if(window.M) {
                    M.updateTextFields();
                }

                checkRoom();

            }
            """,
            {"start": START_DATE, "end": END_DATE}
        )

        page.wait_for_timeout(random.randint(3000, 6000))

        # =================================================
        # CHECK STATUS
        # =================================================

        status = frame.locator("#statusRuangan").inner_text()
        print(f"Status: {status}")

        page.wait_for_timeout(random.randint(1000, 2000))

        # =================================================
        # BOOKING LOGIC
        # =================================================

        if "available" in status.lower():

            print("✔ Room Available")

            def handle_dialog(dialog):
                print("ALERT:", dialog.message)
                dialog.accept()

            page.on("dialog", handle_dialog)

            random_delay(2, 5)

            frame.locator("#submit-reservation-detail").click(force=True)

            page.wait_for_timeout(random.randint(4000, 7000))

            print("✔ Booking Success")

            results.append({
                "name": user["NAMA"],
                "status": "SUCCESS"
            })

        else:

            print("✖ Room Not Available")

            results.append({
                "name": user["NAMA"],
                "status": "FAILED"
            })

        page.close()


    browser.close()


# =====================================================
# SUMMARY REPORT
# =====================================================

print("\n" + "=" * 60)
print("📊 BOOKING SUMMARY")
print("=" * 60)

success = 0
failed = 0

for r in results:
    print(f"{r['status']:<12} {r['name']}")

    if r["status"] == "SUCCESS":
        success += 1
    else:
        failed += 1

print("\n" + "-" * 60)
print(f"Total   : {len(results)}")
print(f"Success : {success}")
print(f"Failed  : {failed}")
print("=" * 60)
