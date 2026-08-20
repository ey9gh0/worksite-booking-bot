from datetime import datetime, timedelta
import os
import random
import sys
import time
from openpyxl import load_workbook
from playwright.sync_api import sync_playwright

URL = "https://script.google.com/a/macros/banksinarmas.com/s/AKfycbyGVQZaMoU4Q4HOS51V2Tmt_nnO2UNu4QCfUbk6EWuGVYtamrhMMLoUv-kI1oGHU9-0Nw/exec?v=bookWorkSite"


# =====================================================
# LOAD BOOKING DATA
# =====================================================


def load_booking_data():
    try:
        wb = load_workbook("booking.xlsx")
    except FileNotFoundError:
        print("❌ File 'booking.xlsx' tidak ditemukan.")
        sys.exit(1)

    ws = wb.active
    data = []

    for row in ws.iter_rows(min_row=2, values_only=True):
        if all(cell is None for cell in row):
            continue

        data.append(
            {
                "NIK": str(row[0]).strip(),
                "NAMA": str(row[1]).strip(),
                "DIVISI": str(row[2]).strip(),
                "EMAIL": str(row[3]).strip(),
                "WORKSITE": str(row[4]).strip(),
            }
        )

    return data


# =====================================================
# GENERATE SENIN - JUMAT MINGGU DEPAN
# =====================================================


def get_next_week_range():
    today = datetime.now().date()
    days_until_next_monday = 7 - today.weekday()

    next_monday = today + timedelta(days=days_until_next_monday)
    next_friday = next_monday + timedelta(days=4)

    return next_monday.strftime("%b %d, %Y"), next_friday.strftime("%b %d, %Y")


# =====================================================
# MAIN EXECUTION
# =====================================================

booking_data = load_booking_data()
START_DATE, END_DATE = get_next_week_range()

if not os.path.exists("videos"):
    os.makedirs("videos")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    total_data = len(booking_data)

    for idx, user in enumerate(booking_data, start=1):
        print(f"[{idx}/{total_data}] Memproses & Merekam: {user['NAMA']}...")

        # Merekam Video Browser HD
        context = browser.new_context(
            record_video_dir="videos/",
            record_video_size={"width": 1280, "height": 720},
        )
        page = context.new_page()

        # Auto accept semua alert agar rekaman berjalan lancar
        page.on("dialog", lambda dialog: dialog.accept())

        try:
            page.goto(URL, wait_until="networkidle")
            page.wait_for_timeout(2000)

            # Cari Frame
            frame = None
            for f in page.frames:
                if f.locator("#nik").count() > 0:
                    frame = f
                    break

            if frame is None:
                continue

            # Input Form Profil
            frame.locator("#nik").fill(user["NIK"])
            frame.locator("#nama").fill(user["NAMA"])
            frame.locator("#divisi").fill(user["DIVISI"])
            frame.locator("#email").fill(user["EMAIL"])

            # Select Worksite
            frame.evaluate(
                """
                (site)=>{
                    const select = document.querySelector("#workSite");
                    for(const opt of select.options){
                        if(opt.text.trim() == site){
                            select.value = opt.value || opt.text;
                            break;
                        }
                    }
                    select.dispatchEvent(new Event("change", {bubbles:true}));
                    if(window.M){ M.FormSelect.init(select); }
                }
                """,
                user["WORKSITE"],
            )

            # Set Tanggal
            frame.evaluate(
                """
                (dates)=>{
                    const startInput = document.getElementById("meetingDate");
                    const endInput = document.getElementById("meetingEnd");

                    startInput.value = dates.start;
                    endInput.value = dates.end;

                    startInput.dispatchEvent(new Event("input", {bubbles:true}));
                    endInput.dispatchEvent(new Event("input", {bubbles:true}));
                    startInput.dispatchEvent(new Event("change", {bubbles:true}));
                    endInput.dispatchEvent(new Event("change", {bubbles:true}));

                    if(window.M) { M.updateTextFields(); }
                    checkRoom();
                }
                """,
                {"start": START_DATE, "end": END_DATE},
            )

            page.wait_for_timeout(4000)

            # Klik Submit
            frame.locator("#submit-reservation-detail").click(force=True)

            # Beri waktu 5 detik agar rekaman menangkap proses submit hingga selesai
            page.wait_for_timeout(5000)

        except Exception as e:
            pass

        finally:
            video_obj = page.video
            video_path_original = video_obj.path() if video_obj else None

            page.close()
            context.close()

            # Simpan file video dengan nama pengguna
            if video_path_original and os.path.exists(video_path_original):
                target_video_path = f"videos/booking_{user['NAMA']}.webm"
                if os.path.exists(target_video_path):
                    os.remove(target_video_path)
                os.rename(video_path_original, target_video_path)

            # Jeda 10 detik antar pengguna
            if idx < total_data:
                time.sleep(10)

    browser.close()

print("\n✨ Seluruh proses booking dan rekaman video selesai disimpandi folder 'videos/'!")
