import json
import os
import math
from collections import defaultdict
from models.review import Review
from analysis.prompts import THEME_DISCOVERY_PROMPT, CLASSIFICATION_PROMPT, REPORT_PROMPT

BATCH_SIZE = 75  # Reviews per classification batch

# Provider is set once at startup via init_provider()
_provider = None


def init_provider(provider: str):
    global _provider
    _provider = provider


def _call_llm(prompt: str) -> str:
    if _provider == "gemini":
        from google import genai
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        return response.text
    else:
        from anthropic import Anthropic
        client = Anthropic()
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text


def _reviews_to_text(reviews: list[Review]) -> str:
    lines = []
    for r in reviews:
        title = f" | Title: {r.title}" if r.title else ""
        lines.append(
            f"[{r.id}] ★{r.rating} ({r.source}){title}\n{r.body}"
        )
    return "\n\n---\n\n".join(lines)


def _themes_to_text(themes: list[dict]) -> str:
    return "\n".join(f"- {t['id']}: {t['label']} — {t['description']}" for t in themes)


def discover_themes(app_name: str, reviews: list[Review]) -> list[dict]:
    """Send a sample of reviews to Claude to discover themes."""
    print(f"\n[Analysis] Discovering themes from {min(len(reviews), 150)} reviews...")
    sample = reviews[:150]
    prompt = THEME_DISCOVERY_PROMPT.format(
        app_name=app_name,
        reviews=_reviews_to_text(sample),
    )
    raw = _call_llm(prompt)
    data = json.loads(raw)
    themes = data["themes"]
    print(f"[Analysis] Found {len(themes)} themes: {', '.join(t['label'] for t in themes)}")
    return themes


def classify_reviews(app_name: str, reviews: list[Review], themes: list[dict]) -> list[dict]:
    """Classify all reviews into themes in batches."""
    num_batches = math.ceil(len(reviews) / BATCH_SIZE)
    print(f"\n[Analysis] Classifying {len(reviews)} reviews in {num_batches} batch(es)...")

    all_classifications = []
    themes_text = _themes_to_text(themes)

    for i in range(num_batches):
        batch = reviews[i * BATCH_SIZE:(i + 1) * BATCH_SIZE]
        print(f"  Batch {i + 1}/{num_batches} ({len(batch)} reviews)...")
        prompt = CLASSIFICATION_PROMPT.format(
            app_name=app_name,
            themes=themes_text,
            reviews=_reviews_to_text(batch),
        )
        raw = _call_llm(prompt)
        data = json.loads(raw)
        all_classifications.extend(data["classifications"])

    return all_classifications


def build_stats(
    reviews: list[Review],
    themes: list[dict],
    classifications: list[dict],
) -> dict:
    """Aggregate classifications into stats for the report."""
    review_map = {r.id: r for r in reviews}
    theme_map = {t["id"]: t for t in themes}

    # Per-theme buckets
    theme_reviews: dict[str, list] = defaultdict(list)
    theme_sentiments: dict[str, list] = defaultdict(list)

    for c in classifications:
        rid = c["review_id"]
        tid = c["theme_id"]
        if rid not in review_map or tid not in theme_map:
            continue
        r = review_map[rid]
        theme_reviews[tid].append(r)
        theme_sentiments[tid].append(c["sentiment"])

    total = len(reviews)
    theme_stats = []
    for t in themes:
        tid = t["id"]
        bucket = theme_reviews[tid]
        sentiments = theme_sentiments[tid]
        count = len(bucket)
        avg_rating = round(sum(r.rating for r in bucket) / count, 1) if bucket else 0
        pct = round(count / total * 100, 1) if total else 0
        neg_pct = round(sentiments.count("negative") / len(sentiments) * 100) if sentiments else 0

        # Pick one representative verbatim (lowest rated, longest body)
        verbatim = None
        if bucket:
            candidate = sorted(bucket, key=lambda r: (r.rating, -len(r.body)))[0]
            verbatim = f'"{candidate.body[:200]}..." — ★{candidate.rating}, {candidate.source}'

        theme_stats.append({
            "id": tid,
            "label": t["label"],
            "description": t["description"],
            "count": count,
            "pct": pct,
            "avg_rating": avg_rating,
            "neg_pct": neg_pct,
            "verbatim": verbatim,
        })

    theme_stats.sort(key=lambda x: x["count"], reverse=True)

    # Store comparison
    store_themes = defaultdict(lambda: defaultdict(int))
    for c in classifications:
        rid = c["review_id"]
        tid = c["theme_id"]
        if rid in review_map and tid in theme_map:
            store_themes[review_map[rid].source][tid] += 1

    # Rating distribution
    rating_dist = defaultdict(int)
    for r in reviews:
        rating_dist[r.rating] += 1

    # Overall avg rating
    avg_rating = round(sum(r.rating for r in reviews) / total, 2) if total else 0

    return {
        "total": total,
        "avg_rating": avg_rating,
        "ios_count": sum(1 for r in reviews if r.source == "app_store"),
        "android_count": sum(1 for r in reviews if r.source == "play_store"),
        "theme_stats": theme_stats,
        "store_themes": {k: dict(v) for k, v in store_themes.items()},
        "rating_dist": dict(rating_dist),
    }


def generate_report(
    app_name: str,
    start_date: str,
    end_date: str,
    stats: dict,
) -> str:
    """Ask Claude to write the final PM briefing."""
    print("\n[Analysis] Generating PM report...")

    # Format theme stats for prompt
    theme_lines = []
    for t in stats["theme_stats"]:
        theme_lines.append(
            f"- {t['label']}: {t['count']} reviews ({t['pct']}%), avg ★{t['avg_rating']}, {t['neg_pct']}% negative"
        )

    # Store comparison
    store_lines = []
    store_themes = stats["store_themes"]
    all_tids = set()
    for s in store_themes.values():
        all_tids.update(s.keys())
    theme_label = {t["id"]: t["label"] for t in stats["theme_stats"]}
    for tid in sorted(all_tids, key=lambda x: sum(store_themes[s].get(x, 0) for s in store_themes), reverse=True):
        ios = store_themes.get("app_store", {}).get(tid, 0)
        android = store_themes.get("play_store", {}).get(tid, 0)
        store_lines.append(f"- {theme_label.get(tid, tid)}: iOS={ios}, Android={android}")

    # Rating distribution
    dist = stats["rating_dist"]
    dist_lines = [f"★{i}: {dist.get(i, 0)} reviews" for i in range(5, 0, -1)]

    # Verbatim quotes
    quotes = [t["verbatim"] for t in stats["theme_stats"] if t["verbatim"]]

    prompt = REPORT_PROMPT.format(
        app_name=app_name,
        start_date=start_date,
        end_date=end_date,
        total_reviews=stats["total"],
        avg_rating=stats["avg_rating"],
        ios_count=stats["ios_count"],
        android_count=stats["android_count"],
        theme_stats="\n".join(theme_lines),
        store_comparison="\n".join(store_lines) or "Single store only.",
        rating_distribution="\n".join(dist_lines),
        verbatim_quotes="\n\n".join(quotes),
    )

    return _call_llm(prompt)


def run(
    app_name: str,
    reviews: list[Review],
    start_date: str,
    end_date: str,
) -> tuple[str, dict]:
    """Full analysis pipeline. Returns (report_text, stats)."""
    if not reviews:
        return "No reviews found in the given date range.", {}

    themes = discover_themes(app_name, reviews)
    classifications = classify_reviews(app_name, reviews, themes)
    stats = build_stats(reviews, themes, classifications)
    report = generate_report(app_name, start_date, end_date, stats)
    return report, stats
