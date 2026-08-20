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
    today = datetime.today().date()
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

        # Menyimpan SELURUH teks alert murni yang muncul di layar
        captured_dialogs = []

        def global_dialog_handler(dialog):
            raw_msg = dialog.message.strip()
            print(f"🔔 [ALERT DETECTED]: '{raw_msg}'")
            captured_dialogs.append(raw_msg)
            dialog.accept()

        page.on("dialog", global_dialog_handler)

        try:
            page.goto(URL, wait_until="networkidle")
            page.wait_for_timeout(random.randint(2000, 3000))

            # 1. Cari Frame di Google Apps Script
            frame = None
            for f in page.frames:
                if f.locator("#nik").count() > 0:
                    frame = f
                    break

            if frame is None:
                print("📣 RESPONSE FINAL : ❌ Form booking tidak ditemukan (Frame Error)")
                continue

            # 2. Input Data Utama
            frame.locator("#nik").fill(user["NIK"])
            short_delay()

            frame.locator("#nama").fill(user["NAMA"])
            short_delay()

            frame.locator("#divisi").fill(user["DIVISI"])
            short_delay()

            frame.locator("#email").fill(user["EMAIL"])
            short_delay()

            expect(frame.locator("#nik")).to_have_value(user["NIK"])

            # 3. Pilih Worksite
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
                    if(window.M){
                        M.FormSelect.init(select);
                    }
                }
                """,
                user["WORKSITE"],
            )

            page.wait_for_timeout(1500)

            # 4. Set Tanggal (Senin - Jumat)
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

                    if(window.M) {
                        M.updateTextFields();
                    }

                    checkRoom();
                }
                """,
                {"start": START_DATE, "end": END_DATE},
            )

            page.wait_for_timeout(4000)

            # 5. Cek Status Ruangan
            status = frame.locator("#statusRuangan").inner_text()

            # 6. Submit & Mengambil Teks Asli dari Alert Layar
            if "available" in status.lower():
                frame.locator("#submit-reservation-detail").click(force=True)

                raw_final_message = None

                # Polling 20 detik untuk menunggu alert final (mengabaikan alert 'uploading/please wait')
                for _ in range(20):
                    page.wait_for_timeout(1000)

                    for msg in reversed(captured_dialogs):
                        msg_lower = msg.lower()
                        if (
                            "uploading" not in msg_lower
                            and "please wait" not in msg_lower
                        ):
                            # Ambil MURNI string asli dari alert layar tanpa diubah
                            raw_final_message = msg
                            break

                    if raw_final_message:
                        break

                if raw_final_message:
                    print(f"\n📣 RESPONSE FINAL : '{raw_final_message}'")
                else:
                    print(
                        "\n📣 RESPONSE FINAL : ❌ Timeout 20 detik! Tidak ada alert status akhir dari layar."
                    )

            else:
                print(f"\n📣 RESPONSE FINAL : ❌ Ruangan Tidak Tersedia ({status})")

        except Exception as e:
            print(f"\n📣 RESPONSE FINAL : ❌ System Error: {e}")

        finally:
            page.close()

            # Jeda 10 detik sebelum lanjut ke orang berikutnya (kecuali di data terakhir)
            if idx < total_data:
                print("⏳ Menunggu jeda 10 detik sebelum lanjut ke data berikutnya...")
                time.sleep(10)

    browser.close()

print("\n✨ Seluruh eksekusi selesai!")
