import requests
from google_play_scraper import search as gp_search


def find_ios_app(app_name: str, country: str = "us") -> dict | None:
    """Search iTunes Search API and return the best match."""
    url = "https://itunes.apple.com/search"
    params = {"term": app_name, "entity": "software", "country": country, "limit": 5}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    results = resp.json().get("results", [])
    if not results:
        return None
    # Return top result
    r = results[0]
    return {
        "app_id": str(r["trackId"]),
        "app_name": r["trackName"],
        "developer": r["artistName"],
        "store_url": r["trackViewUrl"],
    }


def find_android_app(app_name: str, lang: str = "en", country: str = "us") -> dict | None:
    """Search Google Play and return the best match."""
    results = gp_search(app_name, lang=lang, country=country, n_hits=5)
    if not results:
        return None
    r = results[0]
    return {
        "package_id": r["appId"],
        "app_name": r["title"],
        "developer": r["developer"],
        "store_url": f"https://play.google.com/store/apps/details?id={r['appId']}",
    }
