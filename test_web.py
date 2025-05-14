import feedparser
import json
import asyncio
import os
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel
from typing import Optional

DATA_FILE = "sources.json"
OUTPUT_FILE = "news_posts.json"

class NewsPost(BaseModel):
    title: str
    date: Optional[str]
    source: Optional[str]
    summary: str
    url: str

def load_sources():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_sources(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_news_posts():
    if not os.path.exists("new_posts.json"):
        return []
    with open("new_posts.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_news_posts(data):
    with open("new_posts.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

async def parse_with_llm(url: str):
    llm_strat = LLMExtractionStrategy(
        llmConfig=LLMConfig(
            provider="openai/gpt-4o-mini",
            api_token=os.getenv("OPENAI_API_KEY")
        ),
        schema=NewsPost.model_json_schema(),
        extraction_type="schema",
        instruction=(
            "From this HTML page, extract a single structured news post with the following fields:\n"
            "- title (headline)\n"
            "- date (if present)\n"
            "- source (domain name or publication name)\n"
            "- summary (2–4 sentence overview of the content)\n"
            "- url (original page URL)\n"
            "Respond only with a valid JSON matching the schema."
        ),
        chunk_token_threshold=1400,
        apply_chunking=False,
        input_format="html",
        extra_args={"temperature": 0.1, "max_tokens": 1000}
    )

    crawl_config = CrawlerRunConfig(
        extraction_strategy=llm_strat,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
        result = await crawler.arun(url=url, config=crawl_config)
        if result.success:
            news_post = json.loads(result.extracted_content)
            return news_post
        else:
            print(f"❌ Crawl failed: {result.error_message}")
            return None

async def check_rss_updates():
    sources = load_sources()
    updated_sources = []

    news_posts = load_news_posts()

    for item in sources:
        print(f"🔍 Checking RSS for {item['rss']}")
        feed = feedparser.parse(item['rss'])

        if not feed.entries:
            print("⚠️ No entries in RSS feed.")
            updated_sources.append(item)
            continue

        latest_entries = feed.entries[:10]

        for entry in latest_entries:
            latest_link = entry.link
            if item.get("last_link") != latest_link:
                print(f"[+] New article found: {entry.title}")
                news_post = await parse_with_llm(latest_link)
                if news_post:
                    news_posts.append(news_post)
                    print(f"✅ New post added: {news_post[0]['title']}")
                item["last_link"] = latest_link
            else:
                print("[-] No new updates.")

        updated_sources.append(item)

    save_sources(updated_sources)
    save_news_posts(news_posts)

if __name__ == "__main__":
    asyncio.run(check_rss_updates())
