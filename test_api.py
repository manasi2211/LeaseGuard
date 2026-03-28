import urllib.request
import json

url = "https://data.cityofnewyork.us/resource/wvxf-dwi5.json?$limit=3"

try:
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
        print("SUCCESS! Got", len(data), "records")
        print(json.dumps(data[0], indent=2))
except Exception as e:
    print("FAILED:", e)