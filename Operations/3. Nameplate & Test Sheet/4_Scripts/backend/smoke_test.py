import json
import urllib.parse
import urllib.request


BASE = "http://127.0.0.1:8000"


def _get(path: str, params: dict | None = None) -> tuple[int, dict]:
    url = f"{BASE}{path}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"

    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req) as resp:
        body = json.loads(resp.read().decode("utf-8"))
        return resp.status, body


print("OPTIONS:", _get("/api/options")[0])
print("FLA:", _get("/api/fla", {"motor": "1.5", "pole": "4", "voltage": "380"})[1])
print("CONNECTION:", _get("/api/connection", {"motor": "1.5", "pole": "4", "voltage": "380"})[1])
