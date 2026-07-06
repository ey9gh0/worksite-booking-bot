from playwright.sync_api import sync_playwright

URL = "https://script.google.com/a/macros/banksinarmas.com/s/AKfycbyGVQZaMoU4Q4HOS51V2Tmt_nnO2UNu4QCfUbk6EWuGVYtamrhMMLoUv-kI1oGHU9-0Nw/exec?v=bookWorkSite"

# ==============================
# DATA BOOKING
# ==============================

NIK = "12345678"
NAMA = "Nama Kamu"
DIVISI = "IT"
EMAIL = "email@banksinarmas.com"

WORKSITE = "L'Avenue"
TANGGAL = "Jul 22, 2025"

# ==============================

with sync_playwright() as p:

    browser = p.chromium.launch(headless=True)

    page = browser.new_page()

    # kalau muncul alert javascript
    page.on(
        "dialog",
        lambda dialog: (
            print("\n=== DIALOG ==="),
            print(dialog.message),
            dialog.accept()
        )
    )

    print("Membuka website...")

    page.goto(URL, wait_until="networkidle")

    page.wait_for_timeout(3000)

    frame = page.frames[2]

    print("Mengisi data...")

    frame.locator("#nik").fill(NIK)
    frame.locator("#nama").fill(NAMA)
    frame.locator("#divisi").fill(DIVISI)
    frame.locator("#email").fill(EMAIL)

    # =====================================
    # WORKSITE
    # =====================================

    print("Memilih Work Site...")

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

                if(inst){
                    inst.destroy();
                }

                M.FormSelect.init(select);

            }

        }
        """,
        WORKSITE,
    )

    page.wait_for_timeout(1000)

    # =====================================
    # DATEPICKER INFO
    # =====================================

    print("\n=== DATEPICKER INFO ===")

    try:

        info = frame.evaluate(
            """
            () => {

                const inst=M.Datepicker.getInstance(
                    document.querySelector("#meetingDate")
                );

                if(!inst)
                    return "Datepicker belum siap";

                return {
                    format:inst.options.format,
                    minDate:inst.options.minDate,
                    maxDate:inst.options.maxDate
                };

            }
            """
        )

        print(info)

    except Exception as e:

        print(e)

    # =====================================
    # ISI TANGGAL
    # =====================================

    print("\nMengisi tanggal...")

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
        TANGGAL,
    )

    page.wait_for_timeout(5000)

    print("\n=== VALUE ===")

    print("Meeting Date :", frame.locator("#meetingDate").input_value())
    print("Meeting End  :", frame.locator("#meetingEnd").input_value())

    # =====================================
    # STATUS
    # =====================================

    status = frame.locator("#statusRuangan").inner_text()

    print("\n============================")
    print("Room status :", status)
    print("============================")

    if "available" in status.lower():

        print("Ruangan tersedia.")

        button = frame.locator("#submit-reservation-detail")

        print("\n=== BUTTON HTML ===")
        print(button.evaluate("e=>e.outerHTML"))

        page.wait_for_timeout(1000)

        print("\nKlik Make Reservation...")

        button.click(force=True)

        page.wait_for_timeout(3000)

        # =====================================
        # Popup Materialize
        # =====================================

        try:

            modal = frame.locator(".modal.open")

            if modal.count() > 0:

                print("\n=== POPUP ===")
                print(modal.inner_text())

                btns = modal.locator("button")

                for i in range(btns.count()):

                    text = btns.nth(i).inner_text().strip()

                    print("Button:", text)

                    if text.lower() in [
                        "ok",
                        "yes",
                        "submit",
                        "confirm",
                        "continue"
                    ]:

                        btns.nth(i).click(force=True)

                        print("Popup dikonfirmasi")

                        break

        except Exception as e:

            print("Tidak ada popup:", e)

        page.wait_for_timeout(5000)

        try:

            print("\n=== STATUS AKHIR ===")
            print(frame.locator("#statusRuangan").inner_text())
        except:
            pass

        print("\nBooking selesai.")

    else:

        print("Ruangan belum tersedia.")

    browser.close()
