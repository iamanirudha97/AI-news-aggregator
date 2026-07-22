from typing import List
from .base import BaseScraper, Article


class OpenAIArticle(Article):
    pass


class OpenAIScraper(BaseScraper):
    @property
    def rss_urls(self) -> List[str]:
        return ["https://openai.com/news/rss.xml"]

    def get_articles(self, hours: int = 24) -> List[OpenAIArticle]:
        base_articles = super().get_articles(hours)
        openai_articles = []

        for article in base_articles:
            openai_article = OpenAIArticle(**article.model_dump())
            openai_articles.append(openai_article)

        return openai_articles


if __name__ == "__main__":
    scraper = OpenAIScraper()
    articles: List[OpenAIArticle] = scraper.get_articles(hours=50)
    print(f"Retrieved {len(articles)} OpenAI articles.")