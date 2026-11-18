# Hoo-Watch

Phone-friendly page for planning trout trips on the Chattahoochee below Buford Dam, from Buford Dam down to Medlock Bridge. It shows:

- release timing at each ramp
- a launch score for your whole trip, either motor up and float back, or drift to the next ramp
- live USGS turbidity, E. coli estimate and water temperature at Medlock
- a 30-day log

Live at https://river.inchull.com

- `index.html` is the whole app. It reads live USGS gauge data in the browser.
- `scripts/scrape_schedule.py` copies the Buford Dam generation schedule from the USACE Mobile District page into `data/schedule.json`.
- `.github/workflows/schedule.yml` runs the scraper every hour.
- `scripts/scrape_morganfalls.py` does the same for Georgia Power's Morgan Falls Dam readings, into `data/morganfalls.json`.
- `index.html` carries a Content-Security-Policy that allows only its own inline script, identified by a hash. After any edit to that script, run `python3 -I scripts/csp_hash.py` before committing, or the page will load blank.

Data: USGS gauges 02334430, 02334500, 02334653 and 02335000, and the USACE Mobile District hydropower schedule. The Corps can change releases without notice. Check before you go.
