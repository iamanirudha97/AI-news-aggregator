from typing import List, Optional
import requests
from html_to_markdown import convert
from .base import BaseScraper, Article


class AnthropicArticle(Article):
    pass


class AnthropicScraper(BaseScraper):
    @property
    def rss_urls(self) -> List[str]:
        return [
            "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml",
            "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_research.xml",
            "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_engineering.xml",
        ]

    def get_articles(self, hours: int = 24) -> List[AnthropicArticle]:
        base_articles = super().get_articles(hours)
        anthropic_articles = []

        for article in base_articles:
            anthropic_article = AnthropicArticle(**article.model_dump())
            anthropic_articles.append(anthropic_article)

        return anthropic_articles

    def url_to_markdown(self, url: str) -> Optional[str]:
        try:
            response = requests.get(
                url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30
            )
            response.raise_for_status()
            html = response.text
            markdown = convert(html)
            return markdown
        except Exception:
            return None


if __name__ == "__main__":
    scraper = AnthropicScraper()
    articles: List[AnthropicArticle] = scraper.get_articles(hours=100)

    if len(articles) > 1:
        markdown = scraper.url_to_markdown(articles[1].url)

        if markdown is not None:
            print(markdown)
        else:
            print("Could not convert the article.")