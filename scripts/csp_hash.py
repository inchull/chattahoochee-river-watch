"""Keep the Content-Security-Policy in index.html in step with its inline script.
The policy only lets the one inline <script> run, identified by the SHA-256 of its exact text,
so the hash must be refreshed after every edit to that script or the page stops working.

  python3 -I scripts/csp_hash.py          rewrite the hash in index.html
  python3 -I scripts/csp_hash.py --check  exit 1 if the hash is out of date (changes nothing)
"""
import base64, hashlib, pathlib, re, sys
PAGE = pathlib.Path(__file__).resolve().parent.parent / "index.html"
html = PAGE.read_bytes().decode("utf-8")
scripts = re.findall(r"<script>(.*?)</script>", html, re.S)
if len(scripts) != 1 or len(re.findall(r"<script\b", html)) != 1:
    raise SystemExit("expected exactly one inline <script> in index.html")
want = "sha256-" + base64.b64encode(hashlib.sha256(scripts[0].encode("utf-8")).digest()).decode()
found = re.findall(r"script-src '(sha256-[A-Za-z0-9+/=]*)'", html)
if len(found) != 1:
    raise SystemExit("expected exactly one script-src 'sha256-...' in index.html")
if found[0] == want:
    print("CSP hash is current:", want)
elif "--check" in sys.argv:
    raise SystemExit(f"CSP hash is out of date: index.html has {found[0]}, the script is {want}")
else:
    PAGE.write_bytes(html.replace(found[0], want).encode("utf-8"))
    print("CSP hash updated:", want)
