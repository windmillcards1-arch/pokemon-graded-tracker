"""Runs your Apify task, waits for it to finish, and merges the results into data/sales.json."""
import json, os, time, urllib.request, urllib.error

TOKEN = os.environ["APIFY_TOKEN"]
TASK = os.environ["APIFY_TASK_ID"]
API = "https://api.apify.com/v2"

def call(url, method="GET"):
    req = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)

run = call(f"{API}/actor-tasks/{TASK}/runs?token={TOKEN}", "POST")["data"]
run_id, dataset_id = run["id"], run["defaultDatasetId"]
print("Started run", run_id)

while True:
    status = call(f"{API}/actor-runs/{run_id}?token={TOKEN}")["data"]["status"]
    if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
        break
    time.sleep(15)
if status != "SUCCEEDED":
    raise SystemExit(f"Apify run ended with status {status}")

items = call(f"{API}/datasets/{dataset_id}/items?token={TOKEN}&format=json&clean=true")
print("Got", len(items), "listings")

path = "data/sales.json"
old = json.load(open(path)) if os.path.exists(path) else []

def key(x):
    return x.get("url") or x.get("itemUrl") or x.get("itemId") or json.dumps(x, sort_keys=True)

merged = {key(x): x for x in old}
merged.update({key(x): x for x in items})
json.dump(list(merged.values()), open(path, "w"))
print("Total saved:", len(merged))
