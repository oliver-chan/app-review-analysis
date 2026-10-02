import argparse
import json
import os
from datetime import datetime

from scrapers import appstore, playstore
from scrapers.lookup import find_ios_app, find_android_app
from analysis import analyzer


def parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y-%m-%d")


def main():
    parser = argparse.ArgumentParser(description="Scrape and analyze app reviews from App Store and Google Play.")
    parser.add_argument("--app-name", required=True, help="App name to search for (e.g. 'Instagram')")
    parser.add_argument("--start", required=True, help="Start date in YYYY-MM-DD format")
    parser.add_argument("--end", required=True, help="End date in YYYY-MM-DD format")
    parser.add_argument("--country", default="us", help="Country code (default: us)")
    parser.add_argument("--provider", default="anthropic", choices=["anthropic", "gemini"], help="LLM provider (default: anthropic)")
    parser.add_argument("--output", default="reviews.json", help="Raw reviews output file (default: reviews.json)")
    parser.add_argument("--report", default="report.md", help="PM report output file (default: report.md)")
    parser.add_argument("--skip-scrape", action="store_true", help="Skip scraping, reuse existing --output file")
    parser.add_argument("--skip-analysis", action="store_true", help="Scrape only, skip analysis")
    args = parser.parse_args()

    start_date = parse_date(args.start)
    end_date = parse_date(args.end)
    all_reviews = []

    # ── Scraping ────────────────────────────────────────────────────────────
    if args.skip_scrape:
        print(f"\nLoading reviews from '{args.output}'...")
        with open(args.output) as f:
            raw = json.load(f)
        from models.review import Review
        all_reviews = [
            Review(
                id=r["id"], source=r["source"], app_name=r["app_name"],
                rating=r["rating"], title=r["title"], body=r["body"],
                date=datetime.fromisoformat(r["date"]), author=r["author"],
                version=r.get("version"),
            )
            for r in raw
        ]
        print(f"Loaded {len(all_reviews)} reviews.")
    else:
        # iOS
        print(f"\nLooking up '{args.app_name}' on App Store...")
        ios_match = find_ios_app(args.app_name, country=args.country)
        if ios_match:
            print(f"  Found: {ios_match['app_name']} by {ios_match['developer']}")
            ios_reviews = appstore.scrape(
                app_name=ios_match["app_name"],
                app_id=ios_match["app_id"],
                country=args.country,
                start_date=start_date,
                end_date=end_date,
            )
            all_reviews.extend(ios_reviews)
        else:
            print("  No iOS app found.")

        # Android
        print(f"\nLooking up '{args.app_name}' on Google Play...")
        android_match = find_android_app(args.app_name, country=args.country)
        if android_match:
            print(f"  Found: {android_match['app_name']} by {android_match['developer']}")
            android_reviews = playstore.scrape(
                app_name=android_match["app_name"],
                package_id=android_match["package_id"],
                start_date=start_date,
                end_date=end_date,
                country=args.country,
            )
            all_reviews.extend(android_reviews)
        else:
            print("  No Android app found.")

        all_reviews.sort(key=lambda r: r.date, reverse=True)

        # Save raw reviews
        with open(args.output, "w") as f:
            json.dump([r.to_dict() for r in all_reviews], f, indent=2)

        print(f"\nScraped {len(all_reviews)} total reviews → '{args.output}'")
        print(f"  App Store:  {sum(1 for r in all_reviews if r.source == 'app_store')}")
        print(f"  Play Store: {sum(1 for r in all_reviews if r.source == 'play_store')}")

    if args.skip_analysis or not all_reviews:
        return

    # ── Analysis ────────────────────────────────────────────────────────────
    key_var = "GEMINI_API_KEY" if args.provider == "gemini" else "ANTHROPIC_API_KEY"
    if not os.environ.get(key_var):
        print(f"\nWarning: {key_var} not set. Skipping analysis.")
        return

    analyzer.init_provider(args.provider)
    print(f"\n[Analysis] Using provider: {args.provider}")

    report, stats = analyzer.run(
        app_name=args.app_name,
        reviews=all_reviews,
        start_date=args.start,
        end_date=args.end,
    )

    # Save report
    with open(args.report, "w") as f:
        f.write(f"# App Review Analysis: {args.app_name}\n")
        f.write(f"**Period:** {args.start} → {args.end}  \n")
        f.write(f"**Reviews analyzed:** {stats.get('total', 0)}  \n")
        f.write(f"**Average rating:** {stats.get('avg_rating', 'N/A')}★\n\n")
        f.write("---\n\n")
        f.write(report)

    # Save stats JSON
    stats_file = args.report.replace(".md", "_stats.json")
    with open(stats_file, "w") as f:
        json.dump(stats, f, indent=2)

    print(f"\nReport saved to '{args.report}'")
    print(f"Stats saved to '{stats_file}'")
    print("\n" + "=" * 60)
    print(report)


if __name__ == "__main__":
    main()
