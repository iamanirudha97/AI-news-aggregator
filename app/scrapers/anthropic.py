from typing import List, Optional
import requests
# pyrefly: ignore [missing-import]
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
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,*/*;q=0.8"
            ),
        }

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            result = convert(response.text)
            markdown = result.content

            if not markdown or not markdown.strip():
                print(f"Empty markdown returned for {url}")
                return None

            return markdown.strip()

        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

        except Exception as e:
            print(
                f"Error converting {url}: "
                f"{type(e).__name__}: {e}"
            )
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