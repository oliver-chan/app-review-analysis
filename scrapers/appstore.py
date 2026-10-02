import requests
from datetime import datetime
from models.review import Review

# Apple's RSS feed gives up to 500 reviews across 10 pages of 50
RSS_URL = "https://itunes.apple.com/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"


def scrape(app_name: str, app_id: str, country: str, start_date: datetime, end_date: datetime) -> list[Review]:
    print(f"[App Store] Scraping reviews for '{app_name}'...")

    reviews = []
    for page in range(1, 11):  # Pages 1-10, 50 reviews each = 500 max
        url = RSS_URL.format(page=page, app_id=app_id)
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if resp.status_code != 200:
            break

        data = resp.json()
        entries = data.get("feed", {}).get("entry", [])
        if not entries:
            break

        # First entry is app metadata, skip it
        if isinstance(entries, list) and entries and "im:name" in entries[0]:
            entries = entries[1:]

        page_had_reviews_in_range = False
        for entry in entries:
            try:
                updated_str = entry.get("updated", {}).get("label", "")
                review_date = datetime.strptime(updated_str[:10], "%Y-%m-%d")
            except (ValueError, AttributeError):
                continue

            if review_date < start_date:
                # RSS is sorted newest-first; once we're past the start date we can stop
                print(f"[App Store] Reached reviews older than start date at page {page}.")
                print(f"[App Store] Found {len(reviews)} reviews in date range.")
                return reviews

            if review_date > end_date:
                continue

            page_had_reviews_in_range = True
            reviews.append(Review(
                id=entry.get("id", {}).get("label", ""),
                source="app_store",
                app_name=app_name,
                rating=int(entry.get("im:rating", {}).get("label", 0)),
                title=entry.get("title", {}).get("label", ""),
                body=entry.get("content", {}).get("label", ""),
                date=review_date,
                author=entry.get("author", {}).get("name", {}).get("label", ""),
                version=entry.get("im:version", {}).get("label"),
            ))

    print(f"[App Store] Found {len(reviews)} reviews in date range.")
    return reviews
