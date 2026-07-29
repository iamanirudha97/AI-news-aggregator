from typing import List
from app.scrapers.youtube import YouTubeScraper
from app.scrapers.openai import OpenAIScraper
from app.scrapers.anthropic import AnthropicScraper
from app.database.repository import Repository

DEFAULT_YOUTUBE_CHANNELS = [
    "https://www.youtube.com/@Fireship",
    "https://www.youtube.com/@matthew_berman",
]


def run_all_scrapers(hours: int = 168) -> dict:
    """
    Runs YouTube, OpenAI, and Anthropic scrapers and pushes newly scraped data to PostgreSQL.
    """
    repo = Repository()
    summary = {"youtube": 0, "openai": 0, "anthropic": 0}

    # 1. Scrape YouTube Channels
    print("--- Scraping YouTube Channels ---")
    yt_scraper = YouTubeScraper()
    yt_videos_data = []

    for channel_url in DEFAULT_YOUTUBE_CHANNELS:
        print(f"Processing YouTube Channel: {channel_url}")
        channel_id = yt_scraper._get_channel_id(channel_url)
        if channel_id and channel_id.startswith("UC"):
            videos = yt_scraper.scrape_channel(channel_id, hours=hours)
            for v in videos:
                yt_videos_data.append({
                    "video_id": v.video_id,
                    "title": v.title,
                    "url": v.url,
                    "channel_id": channel_id,
                    "published_at": v.published_at,
                    "description": v.description,
                    "transcript": v.transcript,
                })

    if yt_videos_data:
        new_yt_count = repo.bulk_create_youtube_videos(yt_videos_data)
        summary["youtube"] = new_yt_count
        print(f"Saved {new_yt_count} new YouTube video(s) to database.")

    # 2. Scrape OpenAI News Feed
    print("\n--- Scraping OpenAI News Feed ---")
    openai_scraper = OpenAIScraper()
    openai_articles = openai_scraper.get_articles(hours=hours)
    openai_dicts = [
        {
            "guid": a.guid,
            "title": a.title,
            "url": a.url,
            "published_at": a.published_at,
            "description": a.description,
            "category": a.category,
        }
        for a in openai_articles
    ]

    if openai_dicts:
        new_openai_count = repo.bulk_create_openai_articles(openai_dicts)
        summary["openai"] = new_openai_count
        print(f"Saved {new_openai_count} new OpenAI article(s) to database.")

    # 3. Scrape Anthropic News & Engineering Feeds
    print("\n--- Scraping Anthropic News Feeds ---")
    anthropic_scraper = AnthropicScraper()
    anthropic_articles = anthropic_scraper.get_articles(hours=hours)
    anthropic_dicts = [
        {
            "guid": a.guid,
            "title": a.title,
            "url": a.url,
            "published_at": a.published_at,
            "description": a.description,
            "category": a.category,
        }
        for a in anthropic_articles
    ]

    if anthropic_dicts:
        new_anthropic_count = repo.bulk_create_anthropic_articles(anthropic_dicts)
        summary["anthropic"] = new_anthropic_count
        print(f"Saved {new_anthropic_count} new Anthropic article(s) to database.")

        # Update full markdown content for Anthropic articles if missing
        unfetched = repo.get_anthropic_articles_without_markdown()
        for article in unfetched:
            markdown = anthropic_scraper.url_to_markdown(article.url)
            if markdown:
                repo.update_anthropic_article_markdown(article.guid, str(markdown))

    print("\n=== SCRAPE RUN SUMMARY ===")
    print(f"YouTube videos added:   {summary['youtube']}")
    print(f"OpenAI articles added:  {summary['openai']}")
    print(f"Anthropic articles added:{summary['anthropic']}")

    return summary


if __name__ == "__main__":
    run_all_scrapers(hours=168)
