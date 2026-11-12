"""Runs your Apify task, waits for it to finish, and merges the results into data/sales.json."""
import json, os, time, urllib.request, urllib.error

TOKEN = os.environ["APIFY_TOKEN"].strip()
TASK = os.environ["APIFY_TASK_ID"].strip()
API = "https://api.apify.com/v2"

def call(url, method="GET"):
    req = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)

def start():
    # Tries your ID as a Task first, then as an Actor, so either kind of ID works.
    for kind in ("actor-tasks", "acts"):
        try:
            run = call(f"{API}/{kind}/{TASK}/runs?token={TOKEN}", "POST")["data"]
            print("Started run using ID as:", kind)
            if kind == "acts":
                print("NOTE: ID is an Actor, so it ran with the Actor's default input.")
            return run
        except urllib.error.HTTPError as e:
            print(f"{kind}: HTTP {e.code} (ID length {len(TASK)})")
            if e.code != 404:
                raise
    raise SystemExit("Apify could not find that ID as a Task or an Actor. Re-check APIFY_TASK_ID.")

run = start()
run_id, dataset_id = run["id"], run["defaultDatasetId"]
print("Run id:", run_id)

while True:
    status = call(f"{API}/actor-runs/{run_id}?token={TOKEN}")["data"]["status"]
    if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
        break
    time.sleep(15)
if status != "SUCCEEDED":
    raise SystemExit(f"Apify run ended with status {status}")

items = call(f"{API}/datasets/{dataset_id}/items?token={TOKEN}&format=json&clean=true")
print("Got", len(items), "listings")

os.makedirs("data", exist_ok=True)
path = "data/sales.json"
old = json.load(open(path)) if os.path.exists(path) else []

def key(x):
    return x.get("url") or x.get("itemUrl") or x.get("itemId") or json.dumps(x, sort_keys=True)

merged = {key(x): x for x in old}
merged.update({key(x): x for x in items})
json.dump(list(merged.values()), open(path, "w"))
print("Total saved:", len(merged))

path = "data/sales.json"
old = json.load(open(path)) if os.path.exists(path) else []

def key(x):
    return x.get("url") or x.get("itemUrl") or x.get("itemId") or json.dumps(x, sort_keys=True)

merged = {key(x): x for x in old}
merged.update({key(x): x for x in items})
json.dump(list(merged.values()), open(path, "w"))
print("Total saved:", len(merged))
