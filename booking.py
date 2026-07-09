# Updated booking script
from playwright.sync_api import sync_playwright, expect
from openpyxl import load_workbook
from datetime import datetime, timedelta
import random
import time

URL = "https://script.google.com/a/macros/banksinarmas.com/s/AKfycbyGVQZaMoU4Q4HOS51V2Tmt_nnO2UNu4QCfUbk6EWuGVYtamrhMMLoUv-kI1oGHU9-0Nw/exec?v=bookWorkSite"

def random_delay(min_sec=2,max_sec=7):
    time.sleep(random.uniform(min_sec,max_sec))
def short_delay(min_ms=500,max_ms=1500):
    time.sleep(random.uniform(min_ms,max_ms)/1000)

def load_booking_data():
    wb=load_workbook("booking.xlsx")
    ws=wb.active
    data=[]
    for row in ws.iter_rows(min_row=2,values_only=True):
        if all(c is None for c in row):
            continue
        data.append({
            "NIK":str(row[0]).strip(),
            "NAMA":str(row[1]).strip(),
            "DIVISI":str(row[2]).strip(),
            "EMAIL":str(row[3]).strip(),
            "WORKSITE":str(row[4]).strip()
        })
    return data

def get_next_week_dates():
    today=datetime.today().date()
    days=(7-today.weekday())%7
    if days==0:
        days=7
    start=today+timedelta(days=days)
    end=start+timedelta(days=4)
    return start.strftime("%b %d, %Y"), end.strftime("%b %d, %Y")

booking_data=load_booking_data()
BOOKING_START_DATE,BOOKING_END_DATE=get_next_week_dates()
print(BOOKING_START_DATE,BOOKING_END_DATE)

results=[]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    for user in booking_data:
        page=browser.new_page()
        page.goto(URL,wait_until="networkidle")
        frame=None
        for f in page.frames:
            if f.locator("#nik").count()>0:
                frame=f;break
        if not frame:
            page.close();continue
        frame.locator("#nik").fill(user["NIK"])
        short_delay()
        frame.locator("#nama").fill(user["NAMA"])
        short_delay()
        frame.locator("#divisi").fill(user["DIVISI"])
        short_delay()
        frame.locator("#email").fill(user["EMAIL"])
        expect(frame.locator("#nik")).to_have_value(user["NIK"])
        frame.evaluate("""(site)=>{
            const select=document.querySelector("#workSite");
            for(const opt of select.options){
                if(opt.text.trim()==site){select.value=opt.value||opt.text;break;}
            }
            select.dispatchEvent(new Event("change",{bubbles:true}));
            if(window.M){M.FormSelect.init(select);}
        }""",user["WORKSITE"])
        frame.evaluate("""(d)=>{
            meetingDate.value=d.start;
            meetingEnd.value=d.end;
            meetingDate.dispatchEvent(new Event("input",{bubbles:true}));
            meetingEnd.dispatchEvent(new Event("input",{bubbles:true}));
            meetingDate.dispatchEvent(new Event("change",{bubbles:true}));
            meetingEnd.dispatchEvent(new Event("change",{bubbles:true}));
            checkRoom();
        }""",{"start":BOOKING_START_DATE,"end":BOOKING_END_DATE})
        page.wait_for_timeout(3000)
        status=frame.locator("#statusRuangan").inner_text()
        if "available" in status.lower():
            page.on("dialog",lambda d:d.accept())
            frame.locator("#submit-reservation-detail").click(force=True)
            results.append({"name":user["NAMA"],"status":"SUCCESS"})
        else:
            results.append({"name":user["NAMA"],"status":"FAILED"})
        page.close()
    browser.close()
print(results)
