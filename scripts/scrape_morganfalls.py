"""Read Morgan Falls Dam (Georgia Power) current release and tentative turbine schedule
from Georgia Power's Hydro Real-Time Operations page into data/morganfalls.json.
Georgia Power's current-reading timestamp is Central time and is converted to Eastern here,
matching what their page displays."""
import json, re, urllib.request, datetime, pathlib
URL = "https://resources.georgiapower.com/content/tools/hydro-operations/index.cshtml"
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "morganfalls.json"
req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (river-watch schedule reader)"})
page = urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "ignore")
m = re.search(r"responseArray\s*=\s*(['\"])(.*?)\1\s*;", page, re.S)
if not m:
    raise SystemExit("Morgan Falls data not found on page")
raw = m.group(2)
if '\\"' in raw:
    raw = raw.encode().decode("unicode_escape")
data = json.loads(raw)
lake = next(l for r in data["data"] for l in r.get("lakes", []) if l.get("lakeName") == "MorganFalls")
east = lambda ts: (datetime.datetime.fromisoformat(ts) + datetime.timedelta(hours=1)).isoformat(timespec="minutes")
store = json.loads(OUT.read_text()) if OUT.exists() else {"schedule": {}}
cur = lake["current"]
store["current"] = {"time": east(cur["timestamp"]), "flow": cur["flow"], "units": cur["units"], "elevation": cur["elevation"]}
for s in lake.get("lakeSchedule", []):
    day = s["timestamp"][:10]
    hour = datetime.datetime.strptime(s["hourStart"], "%I:%M %p").hour
    # schedule hours are stored as Georgia Power displays them (their page shows these unshifted)
    t = datetime.datetime.fromisoformat(day) + datetime.timedelta(hours=hour)
    store["schedule"].setdefault(t.date().isoformat(), {})[t.strftime("%H:%M")] = s["units"]
cut = (datetime.date.today() - datetime.timedelta(days=45)).isoformat()
store["schedule"] = {k: v for k, v in sorted(store["schedule"].items()) if k >= cut}
store["updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="minutes")
store["source"] = URL
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps(store, separators=(",", ":")))
print("current:", store["current"], "| schedule:", store["schedule"])
