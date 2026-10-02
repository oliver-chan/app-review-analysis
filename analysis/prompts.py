THEME_DISCOVERY_PROMPT = """You are analyzing app store reviews for a product manager.

Below are reviews for the app "{app_name}". Your job is to identify the most important recurring themes.

Reviews:
{reviews}

Identify 6-10 distinct themes that appear across these reviews. Themes should be:
- Specific enough to be actionable (e.g. "checkout crashes" not just "bugs")
- Distinct from each other
- Cover both problems AND positive feedback

Return a JSON object with this exact structure:
{{
  "themes": [
    {{
      "id": "short_snake_case_id",
      "label": "Human readable label",
      "description": "One sentence describing what this theme covers"
    }}
  ]
}}

Return only valid JSON, no explanation."""


CLASSIFICATION_PROMPT = """You are analyzing app store reviews for a product manager.

App: {app_name}

Themes to classify into:
{themes}

Reviews to classify:
{reviews}

For each review, assign it to the ONE most relevant theme, and give a sentiment score.

Return a JSON object with this exact structure:
{{
  "classifications": [
    {{
      "review_id": "the review id",
      "theme_id": "theme id from the list above",
      "sentiment": "positive" | "negative" | "neutral" | "mixed",
      "key_point": "One sentence capturing the core of this review"
    }}
  ]
}}

Return only valid JSON, no explanation."""


REPORT_PROMPT = """You are a senior product analyst writing a briefing for a product manager.

App: {app_name}
Date range: {start_date} to {end_date}
Total reviews analyzed: {total_reviews}
Average rating: {avg_rating}★
iOS reviews: {ios_count} | Android reviews: {android_count}

Theme breakdown (sorted by frequency):
{theme_stats}

Store comparison:
{store_comparison}

Rating distribution:
{rating_distribution}

Write a PM briefing with these exact sections. Be direct, specific, and opinionated. Use the data.

## Executive Summary
2-3 sentences. Overall health of the app, single most important signal, any urgent flag.

## Fix Now 🔴
Issues that are high-frequency, low-rated, or spiking. For each: name it, give the data, say why it matters.

## Improve 🟡
UX friction and underperforming areas worth a sprint. Same format.

## Feature Requests 🔵
What users are asking for. Group similar asks.

## What's Working ✅
Genuine positives worth protecting when making changes.

## PM Recommendation
Your single most important recommendation for what to focus on next quarter. Be specific and opinionated — don't hedge.

Use the verbatim quotes below to support your points where relevant:
{verbatim_quotes}"""
