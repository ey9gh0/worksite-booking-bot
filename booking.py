from playwright.sync_api import sync_playwright, expect
import pandas as pd
from datetime import datetime, timedelta

URL = "https://script.google.com/a/macros/banksinarmas.com/s/AKfycbyGVQZaMoU4Q4HOS51V2Tmt_nnO2UNu4QCfUbk6EWuGVYtamrhMMLoUv-kI1oGHU9-0Nw/exec?v=bookWorkSite"


# =====================================================
# LOAD DATA
# =====================================================

booking_df = pd.read_excel("booking.xlsx")

holiday_df = pd.read_excel("holiday.xlsx")

holiday_list = set(
    pd.to_datetime(holiday_df["DATE"]).dt.date
)


# =====================================================
# NEXT WORKING DAY
# =====================================================

def get_next_working_day():

    today = datetime.today().date()

    target = today + timedelta(days=1)

    while target.weekday() >= 5 or target in holiday_list:
        target += timedelta(days=1)

    return target.strftime("%b %d, %Y")


BOOKING_DATE = get_next_working_day()

print("Booking Date :", BOOKING_DATE)


# =====================================================
# LOOP DATA
# =====================================================

with sync_playwright() as p:

    browser = p.chromium.launch(headless=True)

    for _, row in booking_df.iterrows():

        print("=" * 50)
        print("Booking :", row["NAMA"])

        page = browser.new_page()

        page.goto(URL, wait_until="networkidle")

        page.wait_for_timeout(3000)

        frame = page.frames[2]

        # =====================================
        # INPUT
        # =====================================

        frame.locator("#nik").fill(str(row["NIK"]))

        frame.locator("#nama").fill(row["NAMA"])

        frame.locator("#divisi").fill(row["DIVISI"])

        frame.locator("#email").fill(row["EMAIL"])

        expect(frame.locator("#nik")).to_have_value(str(row["NIK"]))

        # =====================================
        # WORKSITE
        # =====================================

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
            row["WORKSITE"]
        )

        page.wait_for_timeout(1000)

        # =====================================
        # DATE
        # =====================================

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

        status = frame.locator("#statusRuangan").inner_text()

        print(status)

        if "available" in status.lower():

            print("Room Available")

            def handle_dialog(dialog):
                print(dialog.message)
                dialog.accept()

            page.on("dialog", handle_dialog)

            frame.locator("#submit-reservation-detail").click(force=True)

            page.wait_for_timeout(5000)

            print("SUCCESS :", row["NAMA"])

        else:

            print("FAILED :", row["NAMA"])

        page.close()

    browser.close()
