"""Scrape Buford Dam hourly generation schedule from the USACE Mobile District page
and merge it into data/schedule.json (keeps a rolling 45 days)."""
import json, re, sys, html, urllib.request, urllib.parse, http.cookiejar, datetime, pathlib
URL = "https://spatialdata.usace.army.mil/hydropower/"
PLANT = "2"  # BUFORD DAM/LAKE SIDNEY LANIER
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "schedule.json"
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
opener.addheaders = [("User-Agent", "Mozilla/5.0 (river-watch schedule reader)")]

def hidden(page):
    return {m.group(1): html.unescape(m.group(2)) for m in re.finditer(r'<input[^>]+name="(__[A-Z]+)"[^>]*value="([^"]*)"', page)}

def post(page, fields):
    data = {**hidden(page), **fields}
    return opener.open(URL, urllib.parse.urlencode(data).encode(), timeout=40).read().decode("utf-8", "ignore")

def parse_hours(page):
    rows = re.findall(r'(\d{1,2}:\d\d [ap]m) - \d{1,2}:\d\d [ap]m\s*</td>\s*<td[^>]*>\s*([\d.]+)', page)
    out = []
    for t, mw in rows:
        h = datetime.datetime.strptime(t, "%I:%M %p").hour
        out.append({"hour": h, "mw": float(mw)})
    return out

page = opener.open(URL, timeout=40).read().decode("utf-8", "ignore")
page = post(page, {"__EVENTTARGET": "Plant_Selector", "Plant_Selector": PLANT})
dates = [d for d in re.findall(r'<option[^>]*value="(\d{1,2}/\d{1,2}/\d{4})"', page)]
store = json.loads(OUT.read_text()) if OUT.exists() else {"days": {}}
for d in dates:
    p = post(page, {"__EVENTTARGET": "Date_Selector", "Plant_Selector": PLANT, "Date_Selector": d})
    hrs = parse_hours(p)
    if len(hrs) >= 20:
        iso = datetime.datetime.strptime(d, "%m/%d/%Y").date().isoformat()
        store["days"][iso] = hrs
cut = (datetime.date.today() - datetime.timedelta(days=45)).isoformat()
store["days"] = {k: v for k, v in sorted(store["days"].items()) if k >= cut}
store["updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="minutes")
store["source"] = URL
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps(store, separators=(",", ":")))
print("dates offered:", dates, "| stored:", list(store["days"])[-7:])
