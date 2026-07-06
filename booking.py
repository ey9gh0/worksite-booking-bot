from playwright.sync_api import sync_playwright, expect
from openpyxl import load_workbook
from datetime import datetime, timedelta

URL = "https://script.google.com/a/macros/banksinarmas.com/s/AKfycbyGVQZaMoU4Q4HOS51V2Tmt_nnO2UNu4QCfUbk6EWuGVYtamrhMMLoUv-kI1oGHU9-0Nw/exec?v=bookWorkSite"

# =====================================================
# LOAD BOOKING DATA
# =====================================================

def load_booking_data():
    wb = load_workbook("booking.xlsx")
    ws = wb.active

    data = []

    # Header harus:
    # NIK | NAMA | DIVISI | EMAIL | WORKSITE

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
# LOAD HOLIDAY
# =====================================================

def load_holiday():

    wb = load_workbook("holiday.xlsx")
    ws = wb.active

    holidays = set()

    for row in ws.iter_rows(min_row=2, values_only=True):

        if row[0] is None:
            continue

        if isinstance(row[0], datetime):
            holidays.add(row[0].date())

        else:
            holidays.add(
                datetime.strptime(str(row[0]), "%Y-%m-%d").date()
            )

    return holidays


# =====================================================
# NEXT WORKING DAY
# =====================================================

def get_next_working_day(holidays):

    target = datetime.today().date() + timedelta(days=1)

    while target.weekday() >= 5 or target in holidays:
        target += timedelta(days=1)

    return target.strftime("%b %d, %Y")


booking_data = load_booking_data()

holiday_list = load_holiday()

BOOKING_DATE = get_next_working_day(holiday_list)

print(f"Booking Date : {BOOKING_DATE}")


# =====================================================
# PLAYWRIGHT
# =====================================================

with sync_playwright() as p:

    browser = p.chromium.launch(headless=True)

    for user in booking_data:

        print("=" * 60)
        print(f"Booking : {user['NAMA']}")

        page = browser.new_page()

        page.goto(URL, wait_until="networkidle")

        page.wait_for_timeout(3000)

        frame = page.frames[2]

        # ============================================
        # INPUT
        # ============================================

        frame.locator("#nik").fill(user["NIK"])
        frame.locator("#nama").fill(user["NAMA"])
        frame.locator("#divisi").fill(user["DIVISI"])
        frame.locator("#email").fill(user["EMAIL"])

        expect(frame.locator("#nik")).to_have_value(user["NIK"])
        expect(frame.locator("#nama")).to_have_value(user["NAMA"])
        expect(frame.locator("#divisi")).to_have_value(user["DIVISI"])
        expect(frame.locator("#email")).to_have_value(user["EMAIL"])

        print("Form berhasil diisi.")

        # ============================================
        # WORKSITE
        # ============================================

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

        page.wait_for_timeout(1000)

        # ============================================
        # DATE
        # ============================================

        frame.evaluate(
            """
            (tgl)=>{

                meetingDate.value=tgl;
                meetingEnd.value=tgl;

                meetingDate.dispatchEvent(new Event("input",{bubbles:true}));
                meetingEnd.dispatchEvent(new Event("input",{bubbles:true}));

                meetingDate.dispatchEvent(new Event("change",{bubbles:true}));
                meetingEnd.dispatchEvent(new Event("change",{bubbles:true}));

                checkRoom();

            }
            """,
            BOOKING_DATE
        )

        page.wait_for_timeout(4000)

        print("Meeting Date :", frame.locator("#meetingDate").input_value())

        status = frame.locator("#statusRuangan").inner_text()

        print(status)

        # ============================================
        # SUBMIT
        # ============================================

        if "available" in status.lower():

            print("Ruangan tersedia.")

            def handle_dialog(dialog):
                print("========== ALERT ==========")
                print(dialog.message)
                dialog.accept()

            page.on("dialog", handle_dialog)

            frame.locator("#submit-reservation-detail").click(force=True)

            page.wait_for_timeout(5000)

            print(f"SUCCESS : {user['NAMA']}")

        else:

            print(f"FAILED : {user['NAMA']}")
            print("Ruangan belum tersedia.")

        page.close()

    browser.close()

print("Selesai.")
