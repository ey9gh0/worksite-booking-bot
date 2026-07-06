from playwright.sync_api import sync_playwright
import os
import sys

URL = "https://script.google.com/a/macros/banksinarmas.com/s/AKfycbyGVQZaMoU4Q4HOS51V2Tmt_nnO2UNu4QCfUbk6EWuGVYtamrhMMLoUv-kI1oGHU9-0Nw/exec?v=bookWorkSite"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True
        )

        page = browser.new_page(
            viewport={"width": 1920, "height": 1080}
        )

        print("Opening website...")
        page.goto(URL, wait_until="networkidle", timeout=120000)

        page.screenshot(path="page.png", full_page=True)

        print("=" * 50)
        print("TITLE :", page.title())
        print("URL   :", page.url)
        print("=" * 50)

        frames = page.frames

        print(f"Total Frames : {len(frames)}")

        for i, frame in enumerate(frames):
            print("-" * 50)
            print(f"Frame {i}")
            print(frame.url)

            try:
                ids = frame.locator("[id]").evaluate_all(
                    """els => els.map(e => e.id)"""
                )

                print(ids)

            except Exception as e:
                print(e)

        browser.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
        sys.exit(1)
