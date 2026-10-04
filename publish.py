"""Step 2: publish the committed image to Instagram via the Graph API."""
import json, os, time, requests

meta = json.load(open("meta.json"))
caption = open("caption.txt").read()
repo = os.environ["GITHUB_REPOSITORY"]
branch = os.environ.get("GITHUB_REF_NAME", "main")
image_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{meta['image_path']}"
ig = os.environ["IG_USER_ID"]
token = os.environ["IG_ACCESS_TOKEN"]
base = f"https://graph.facebook.com/v21.0/{ig}"

time.sleep(20)  # let raw.githubusercontent.com serve the new file
r = requests.post(f"{base}/media", data={"image_url": image_url, "caption": caption, "access_token": token}, timeout=60)
r.raise_for_status()
creation_id = r.json()["id"]
r = requests.post(f"{base}/media_publish", data={"creation_id": creation_id, "access_token": token}, timeout=60)
r.raise_for_status()
print("Published", r.json())
