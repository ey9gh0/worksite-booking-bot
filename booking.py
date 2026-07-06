from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import os
import sys

URL = "https://script.google.com/a/macros/banksinarmas.com/s/AKfycbyGVQZaMoU4Q4HOS51V2Tmt_nnO2UNu4QCfUbk6EWuGVYtamrhMMLoUv-kI1oGHU9-0Nw/exec?v=bookWorkSite"

NIK = os.getenv("NIK")
NAMA = os.getenv("NAMA")
DIVISI = os.getenv("DIVISI")
EMAIL = os.getenv("EMAIL")


def next_workday():
    d = datetime.now() + timedelta(days=1)

    while d.weekday() >= 5:   # Sabtu=5, Minggu=6
        d += timedelta(days=1)

    return d.strftime("%d/%m/%Y")


BOOKING_DATE = next_workday()


def run():
    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        page = browser.new_page()

        print("Opening page...")
        page.goto(URL, wait_until="networkidle")

        page.wait_for_timeout(5000)

        # masuk iframe
        frame = page.frame_locator("iframe")

        print("Fill form...")

        frame.locator("#nik").fill(NIK)
        frame.locator("#nama").fill(NAMA)
        frame.locator("#divisi").fill(DIVISI)
        frame.locator("#email").fill(EMAIL)

        frame.locator("#workSite").select_option(label="GOP 1")

        # tanggal (sementara)
        frame.locator("#meetingDate").fill(BOOKING_DATE)
        frame.locator("#meetingEnd").fill(BOOKING_DATE)

        print("Submit booking...")

        frame.locator("#submit-reservation-detail").click()

        page.wait_for_timeout(8000)

        print(page.content())

        browser.close()


if __name__ == "__main__":
    try:
        run()
        sys.exit(0)
    except Exception as e:
        print(e)
        sys.exit(1)