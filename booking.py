from playwright.sync_api import sync_playwright, expect

URL = "https://script.google.com/a/macros/banksinarmas.com/s/AKfycbyGVQZaMoU4Q4HOS51V2Tmt_nnO2UNu4QCfUbk6EWuGVYtamrhMMLoUv-kI1oGHU9-0Nw/exec?v=bookWorkSite"

# ======================================================
# DATA
# ======================================================

NIK = "12345678"          # ganti dengan NIK asli
NAMA = "Nama Kamu"
DIVISI = "IT"
EMAIL = "email@banksinarmas.com"

WORKSITE = "L'Avenue"
TANGGAL = "Jul 22, 2025"

# ======================================================

with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=True
    )

    page = browser.new_page()

    print("Membuka website...")

    page.goto(URL, wait_until="networkidle")

    page.wait_for_timeout(3000)

    frame = page.frames[2]

    # ======================================================
    # Isi Form
    # ======================================================

    print("Mengisi data...")

    frame.locator("#nik").fill(NIK)
    frame.locator("#nama").fill(NAMA)
    frame.locator("#divisi").fill(DIVISI)
    frame.locator("#email").fill(EMAIL)

    # pastikan benar-benar masuk

    expect(frame.locator("#nik")).to_have_value(NIK)
    expect(frame.locator("#nama")).to_have_value(NAMA)
    expect(frame.locator("#divisi")).to_have_value(DIVISI)
    expect(frame.locator("#email")).to_have_value(EMAIL)

    print("Semua field terisi.")

    # ======================================================
    # Worksite
    # ======================================================

    print("Memilih Worksite...")

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
        WORKSITE
    )

    page.wait_for_timeout(1000)

    # ======================================================
    # Tanggal
    # ======================================================

    print("Mengisi tanggal...")

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
        TANGGAL
    )

    page.wait_for_timeout(4000)

    print("Meeting Date :", frame.locator("#meetingDate").input_value())
    print("Meeting End  :", frame.locator("#meetingEnd").input_value())

    status = frame.locator("#statusRuangan").inner_text()

    print(status)

    # ======================================================
    # Submit
    # ======================================================

    if "available" in status.lower():

        print("Ruangan tersedia.")

        def handle_dialog(dialog):
            print("\n========== ALERT ==========")
            print(dialog.message)
            dialog.accept()

        page.on("dialog", handle_dialog)

        print("Klik Make Reservation")

        frame.locator("#submit-reservation-detail").click(force=True)

        page.wait_for_timeout(5000)

        print("\n========== VALUE TERKIRIM ==========")

        print("NIK   :", frame.locator("#nik").input_value())
        print("Nama  :", frame.locator("#nama").input_value())
        print("Divisi:", frame.locator("#divisi").input_value())
        print("Email :", frame.locator("#email").input_value())

        print("\n========== STATUS ==========")
        print(frame.locator("#statusRuangan").inner_text())

    else:

        print("Ruangan belum tersedia.")

    browser.close()
