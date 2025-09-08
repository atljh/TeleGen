import os
import requests
from time import sleep
from dotenv import load_dotenv

load_dotenv()

RSS_API_KEY = os.getenv("RSS_API_KEY")
RSS_API_SECRET = os.getenv("RSS_API_SECRET")
API_TOKEN = f"{RSS_API_KEY}:{RSS_API_SECRET}"
BASE_URL = "https://api.rss.app/v1"
LIMIT = 100

headers = {"Authorization": f"Bearer {API_TOKEN}"}


def get_all_feeds():
    feeds = []
    offset = 0

    while True:
        url = f"{BASE_URL}/feeds?limit={LIMIT}&offset={offset}"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print("❌ Error:", response.text)
            break

        data = response.json()
        batch = data.get("data", [])

        if not batch:
            break

        feeds.extend(batch)
        offset += LIMIT

        if len(feeds) >= data.get("total", 0):
            break

    return feeds


def delete_feed(feed_id):
    url = f"{BASE_URL}/feeds/{feed_id}"
    response = requests.delete(url, headers=headers)
    return response.status_code == 200


if __name__ == "__main__":
    feeds = get_all_feeds()
    print(f"Found {len(feeds)} feeds")

    for i, feed in enumerate(feeds, start=1):
        feed_id = feed["id"]
        title = feed.get("title", "Без названия")

        ok = delete_feed(feed_id)
        if ok:
            print(f"[{i}/{len(feeds)}] ✅ Deleted: {title} ({feed_id})")
        else:
            print(f"[{i}/{len(feeds)}] ⚠ Delete Error {title} ({feed_id})")

        sleep(1)
