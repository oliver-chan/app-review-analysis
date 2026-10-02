import re
import requests


def find_ios_app(app_name: str, country: str = "us") -> dict | None:
    """Search iTunes Search API and return the best match."""
    url = "https://itunes.apple.com/search"
    params = {"term": app_name, "entity": "software", "country": country, "limit": 5}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    results = resp.json().get("results", [])
    if not results:
        return None
    r = results[0]
    return {
        "app_id": str(r["trackId"]),
        "app_name": r["trackName"],
        "developer": r["artistName"],
        "store_url": r["trackViewUrl"],
    }


def find_android_app(app_name: str, lang: str = "en", country: str = "us") -> dict | None:
    """Search Google Play search page and extract the first result's package ID."""
    url = "https://play.google.com/store/search"
    params = {"q": app_name, "c": "apps", "hl": lang, "gl": country}
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    resp = requests.get(url, params=params, headers=headers, timeout=10)
    if resp.status_code != 200:
        return None

    # Extract package IDs from app detail links in the page
    package_ids = re.findall(r'/store/apps/details\?id=([\w.]+)', resp.text)
    if not package_ids:
        return None

    package_id = package_ids[0]
    return {
        "package_id": package_id,
        "app_name": app_name,
        "developer": "",
        "store_url": f"https://play.google.com/store/apps/details?id={package_id}",
    }
