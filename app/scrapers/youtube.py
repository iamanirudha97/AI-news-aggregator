from datetime import datetime, timedelta, timezone
from typing import Optional
import os
import re
import requests
from bs4 import BeautifulSoup
import feedparser
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from youtube_transcript_api.proxies import WebshareProxyConfig


class Transcript(BaseModel):
    text: str


class ChannelVideo(BaseModel):
    title: str
    url: str
    video_id: str
    published_at: datetime
    description: str
    transcript: Optional[str] = None


class YouTubeScraper:
    def __init__(self):
        proxy_config = None
        proxy_username = os.getenv("PROXY_USERNAME")
        proxy_password = os.getenv("PROXY_PASSWORD")
        
        if proxy_username and proxy_password:
            proxy_config = WebshareProxyConfig(
                proxy_username=proxy_username,
                proxy_password=proxy_password
            )
        
        self.transcript_api = YouTubeTranscriptApi(proxy_config=proxy_config)

    def _get_channel_id(self, channel_url: str) -> str:
        """
        Scrapes a YouTube channel URL to find its unique Channel ID.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        try:
            response = requests.get(channel_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Primary check: Look for the canonical link
            canonical_link = soup.find('link', rel='canonical')
            if canonical_link and 'href' in canonical_link.attrs:
                href = canonical_link['href']
                if '/channel/' in href:
                    return href.split('/channel/')[1]
            
            # Fallback check: Search the raw HTML for the browseId metadata
            match = re.search(r'"browseId":"(UC[^"]+)"', response.text)
            if match:
                return match.group(1)
                
            return "Channel ID not found."
            
        except requests.RequestException as e:
            return f"Error fetching the URL: {e}"

    def _get_rss_url(self, channel_id: str) -> str:
        return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

    def _extract_video_id(self, video_url: str) -> str:
        if "youtube.com/watch?v=" in video_url:
            return video_url.split("v=")[1].split("&")[0]
        if "youtube.com/shorts/" in video_url:
            return video_url.split("shorts/")[1].split("?")[0]
        if "youtu.be/" in video_url:
            return video_url.split("youtu.be/")[1].split("?")[0]
        return video_url

    def get_transcript(self, video_id: str) -> Optional[Transcript]:
        try:
            transcript = self.transcript_api.fetch(video_id)
            text = " ".join([snippet.text for snippet in transcript.snippets])
            return Transcript(text=text)
        except (TranscriptsDisabled, NoTranscriptFound):
            return None
        except Exception:
            return None

    def get_latest_videos(self, channel_id: str, hours: int = 24) -> list[ChannelVideo]:
        feed = feedparser.parse(self._get_rss_url(channel_id))
        if not feed.entries:
            return []
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        videos = []
        
        for entry in feed.entries:
            if "/shorts/" in entry.link:
                continue
            published_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            if published_time >= cutoff_time:
                video_id = self._extract_video_id(entry.link)
                videos.append(ChannelVideo(
                    title=entry.title,
                    url=entry.link,
                    video_id=video_id,
                    published_at=published_time,
                    description=entry.get("summary", "")
                ))
        
        return videos

    def scrape_channel(self, channel_id: str, hours: int = 48) -> list[ChannelVideo]:
        videos = self.get_latest_videos(channel_id, hours)
        result = []
        for video in videos:
            transcript = self.get_transcript(video.video_id)
            result.append(video.model_copy(update={"transcript": transcript.text if transcript else None}))
        return result  
    
if __name__ == "__main__":
    scraper = YouTubeScraper()
    channels = ["https://www.youtube.com/@Fireship"]

    print("\n" + "=" * 80)
    print("YOUTUBE SCRAPER TEST RUN".center(80))
    print("=" * 80 + "\n")

    for i, channel_url in enumerate(channels, 1):
        print(f"[{i}/{len(channels)}] Processing: {channel_url}")
        print("-" * 80)

        print("Resolving channel ID...")
        channel_id = scraper._get_channel_id(channel_url)

        if not channel_id.startswith("UC"):
            print(f"Error resolving ID: {channel_id}\n")
            continue

        print(f"  ↳ Resolved ID: {channel_id}")
        print("  • Scraping videos and transcripts (last 120 hours)...")
        videos = scraper.scrape_channel(channel_id, hours=12)
        print(f"  ↳ Found {len(videos)} video(s).")
        print("-" * 80)

        print(f"\n--- SCRAPE RESULTS: {channel_url} ---")
        if not videos:
            print("No videos found in the specified timeframe.")
        else:
            for idx, video in enumerate(videos, 1):
                print(f"\n  {idx:02d}. Title:     {video.title}")
                print(f"      URL:       {video.url}")
                print(f"      Published: {video.published_at.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                
                if video.transcript:
                    snippet = video.transcript[:150].strip().replace('\n', ' ')
                    print(f"      Transcript (Preview):")
                    print(f"        \"{snippet}...\"")
                else:
                    print(f"      Transcript: [Not Available]")
        print("\n" + "=" * 80 + "\n")