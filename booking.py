from playwright.sync_api import sync_playwright

URL = "https://script.google.com/a/macros/banksinarmas.com/s/AKfycbyGVQZaMoU4Q4HOS51V2Tmt_nnO2UNu4QCfUbk6EWuGVYtamrhMMLoUv-kI1oGHU9-0Nw/exec?v=bookWorkSite"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    page = browser.new_page()

    page.goto(URL, wait_until="networkidle")

    frame = page.frames[2]

    print("========== WORKSITE ==========")
    print(frame.locator("#workSite").inner_html())

    print("========== MEETING DATE ==========")
    print(frame.locator("#meetingDate").evaluate("e => e.outerHTML"))

    browser.close()
