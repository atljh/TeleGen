import os
import json
import asyncio
from typing import Optional
from pydantic import BaseModel
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy

class NewsPost(BaseModel):
    title: str
    date: Optional[str]
    source: Optional[str]
    summary: str
    url: str

async def main():
    llm_strat = LLMExtractionStrategy(
        llmConfig=LLMConfig(provider="openai/gpt-4o-mini", api_token=os.getenv("OPENAI_API_KEY")),
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
        url = "https://sportarena.com/uk/boxing/shon-porter-bij-z-barriosom-match-stvorenij-dlya/"
        result = await crawler.arun(url=url, config=crawl_config)

        if result.success:
            with open("sportarena_news_post.json", "w", encoding="utf-8") as f:
                f.write(result.extracted_content)
            print("✅ Extracted and saved to sportarena_news_post.json")
            llm_strat.show_usage()
        else:
            print("❌ Crawl failed:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
