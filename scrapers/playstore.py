from datetime import datetime
from google_play_scraper import Sort, reviews as gp_reviews
from models.review import Review


def scrape(app_name: str, package_id: str, start_date: datetime, end_date: datetime, lang: str = "en", country: str = "us") -> list[Review]:
    """
    Scrape Google Play reviews for a given app within a date range.
    package_id: the app's package name (e.g. "com.instagram.android")
    """
    print(f"[Play Store] Scraping reviews for '{app_name}' ({package_id})...")

    result, _ = gp_reviews(
        package_id,
        lang=lang,
        country=country,
        sort=Sort.NEWEST,
        count=1000,
    )

    reviews = []
    for r in result:
        review_date = r.get("at")
        if not isinstance(review_date, datetime):
            continue
        review_date = review_date.replace(tzinfo=None)
        if not (start_date <= review_date <= end_date):
            continue

        reviews.append(Review(
            id=str(r.get("reviewId", "")),
            source="play_store",
            app_name=app_name,
            rating=int(r.get("score", 0)),
            title="",  # Play Store reviews don't have titles
            body=r.get("content", ""),
            date=review_date,
            author=r.get("userName", ""),
            version=r.get("reviewCreatedVersion"),
        ))

    print(f"[Play Store] Found {len(reviews)} reviews in date range.")
    return reviews
