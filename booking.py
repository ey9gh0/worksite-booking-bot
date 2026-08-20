from datetime import datetime, timedelta
import random
import sys
import time
from openpyxl import load_workbook
from playwright.sync_api import expect, sync_playwright

URL = "https://script.google.com/a/macros/banksinarmas.com/s/AKfycbyGVQZaMoU4Q4HOS51V2Tmt_nnO2UNu4QCfUbk6EWuGVYtamrhMMLoUv-kI1oGHU9-0Nw/exec?v=bookWorkSite"


# =====================================================
# DELAY FUNCTIONS
# =====================================================


def short_delay(min_ms=500, max_ms=1500):
    time.sleep(random.uniform(min_ms, max_ms) / 1000)


# =====================================================
# LOAD BOOKING DATA
# =====================================================


def load_booking_data():
    try:
        wb = load_workbook("booking.xlsx")
    except FileNotFoundError:
        print("❌ Error: File 'booking.xlsx' tidak ditemukan.")
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

    start_date_str = next_monday.strftime("%b %d, %Y")
    end_date_str = next_friday.strftime("%b %d, %Y")

    return start_date_str, end_date_str


# =====================================================
# MAIN EXECUTION
# =====================================================

booking_data = load_booking_data()
START_DATE, END_DATE = get_next_week_range()

print("\n📅 Periode Booking Minggu Depan:")
print(f"   Tanggal Mulai (Senin)  : {START_DATE}")
print(f"   Tanggal Selesai (Jumat): {END_DATE}\n")

# =====================================================
# PLAYWRIGHT AUTOMATION
# =====================================================

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    total_data = len(booking_data)

    for idx, user in enumerate(booking_data, start=1):
        print("\n" + "=" * 60)
        print(f"[{idx}/{total_data}] Processing Booking : {user['NAMA']}")

        page = browser.new_page()

        uploading_alert_dismissed = {"status": False}
        gas_network_finished = {"status": False}

        # 1. Listener Alert - Otomatis Accept jika muncul 'Uploading'
        def global_dialog_handler(dialog):
            msg = dialog.message.strip()
            print(f"🔔 [ALERT DETECTED]: '{msg}'")

            if (
                "uploading" in msg.lower()
                or "please wait" in msg.lower()
                or "loading" in msg.lower()
            ):
                uploading_alert_dismissed["status"] = True

            dialog.accept()

        page.on("dialog", global_dialog_handler)

        # 2. Listener Network - Deteksi saat transmisi data GAS selesai (Status 200)
        def handle_response(response):
            if "exec" in response.url or "google" in response.url:
                if response.status == 200:
                    gas_network_finished["status"] = True

        page.on("response", handle_response)

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
                print(
                    "📣 RESPONSE FINAL : ❌ Form booking tidak ditemukan (Frame Error)"
                )
                continue

            # Input Form
            frame.locator("#nik").fill(user["NIK"])
            short_delay()
            frame.locator("#nama").fill(user["NAMA"])
            short_delay()
            frame.locator("#divisi").fill(user["DIVISI"])
            short_delay()
            frame.locator("#email").fill(user["EMAIL"])
            short_delay()

            expect(frame.locator("#nik")).to_have_value(user["NIK"])

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

            page.wait_for_timeout(1000)

            # Set Tanggal & Trigger Check
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

            page.wait_for_timeout(5000)

            status_text = frame.locator("#statusRuangan").inner_text().strip()
            is_truly_available = (
                "available" in status_text.lower()
                and "not available" not in status_text.lower()
            )

            if is_truly_available:
                print("🔘 Mengeklik Tombol Submit...")

                # Reset status network sebelum memicu submit
                gas_network_finished["status"] = False

                frame.locator("#submit-reservation-detail").click(force=True)

                # Polling tunggu proses pengunggahan selesai (Maksimal 15 Detik)
                for _ in range(15):
                    page.wait_for_timeout(1000)

                    # Jika alert uploading sudah lewat DAN respon backend GAS selesai
                    if (
                        uploading_alert_dismissed["status"]
                        or gas_network_finished["status"]
                    ):
                        break

                # Jeda 1 detik singkat agar elemen loading di layar menghilang total
                page.wait_for_timeout(1000)

                # 📸 LANGSUNG SCREENSHOT BEGITU UPLOADING KELAR
                filename = f"booking_{user['NAMA']}_POST_UPLOAD.png"
                page.screenshot(path=filename, full_page=True)

                print(
                    f"\n📣 RESPONSE FINAL : ✔ Upload selesai! Screenshot tersimpan: {filename}"
                )

            else:
                print(
                    f"\n📣 RESPONSE FINAL : ❌ Ruangan Tidak Tersedia ({status_text if status_text else 'Not Available'})"
                )

        except Exception as e:
            print(f"\n📣 RESPONSE FINAL : ❌ System Error: {e}")

        finally:
            page.close()

            if idx < total_data:
                print(
                    "\n⏳ Menunggu jeda 10 detik sebelum lanjut ke data berikutnya..."
                )
                time.sleep(10)

    browser.close()

print("\n✨ Seluruh eksekusi selesai!")
