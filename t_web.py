import os
import json
import asyncio
from typing import Optional, List
from pydantic import BaseModel
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy

class NewsPost(BaseModel):
    title: str
    date: Optional[str]
    source: Optional[str]
    summary: str
    url: str
    images: Optional[List[str]]

async def main():
    llm_strat = LLMExtractionStrategy(
        llmConfig=LLMConfig(
            provider="openai/gpt-4o-mini",
            api_token=os.getenv("OPENAI_API_KEY"),
            base_url="https://api.openai.com/v1"  # Явно укажите URL API
        ),
        schema=NewsPost.model_json_schema(),
        extraction_type="schema",
        instruction=(
            "From this HTML page, extract a single structured news post with the following fields:\n"
            "- title (headline)\n"
            "- date (if present)\n"
            "- source (domain name or publication name)\n"
            "- summary (2-4 sentence overview of the content)\n"
            "- url (original page URL)\n"
            "- images (list of ALL relevant image URLs from the page)\n"
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
            try:
                # Парсим JSON
                parsed_data = json.loads(result.extracted_content)
                
                # Если пришел список - берем первый элемент
                if isinstance(parsed_data, list):
                    if len(parsed_data) > 0:
                        post_data = parsed_data[0]
                    else:
                        raise ValueError("Empty list in response")
                else:
                    post_data = parsed_data
                
                # Добавляем URL, если его нет
                if 'url' not in post_data:
                    post_data['url'] = url
                
                # Нормализуем images
                if 'images' not in post_data:
                    post_data['images'] = []
                elif not isinstance(post_data['images'], list):
                    post_data['images'] = [post_data['images']]
                
                # Создаем объект NewsPost
                news_post = NewsPost(**post_data)
                
                # Сохраняем в файл
                with open("sportarena_news_post.json", "w", encoding="utf-8") as f:
                    json.dump(post_data, f, indent=2, ensure_ascii=False)
                
                # Выводим информацию
                print("✅ Extraction successful!")
                print(f"Title: {news_post.title}")
                print(f"Source: {news_post.source}")
                print(f"URL: {news_post.url}")
                print("\nFound images:")
                if news_post.images:
                    for i, img_url in enumerate(news_post.images, 1):
                        print(f"{i}. {img_url}")
                else:
                    print("No images found")
                    
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON: {e}")
                print("Raw response:", result.extracted_content[:500] + "...")
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                print("Response content:", result.extracted_content[:500] + "...")
        else:
            print("❌ Crawl failed:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())