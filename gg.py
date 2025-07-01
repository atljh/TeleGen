import os
import json
import asyncio
import logging
from typing import List, Optional
from pydantic import BaseModel
from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

os.environ["LITELLM_PROXY"] = "False"
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["LITELLM_MODEL"] = "gpt-4o-mini"

class WebPost(BaseModel):
    title: str
    content: str
    date: Optional[str]
    source: Optional[str]
    url: str
    images: Optional[List[str]]

async def parse_with_llm(url: str, openai_key: str = None) -> Optional[WebPost]:
    logger.info(f"Starting LLM parsing for URL: {url}")
    
    model_name = "openai/gpt-4o-mini"
    logger.info(f"🔄 Using LLM model: {model_name} (provider: Ollama)")
    logger.info(f"API key: {'provided' if openai_key else 'not provided'}")

    llm_strat = LLMExtractionStrategy(
        llmConfig=LLMConfig(
            provider=model_name,
            api_token=openai_key
        ),
        schema=WebPost.model_json_schema(),
        extraction_type="schema",
        instruction=(
            "From this HTML page, extract structured content with fields:\n"
            "- title (main headline)\n"
            "- content (full article text, 5-10 paragraphs)\n"
            "- date (publication date if available)\n"
            "- source (website or publisher name)\n"
            "- url (original page URL)\n"
            "- images (list of relevant image URLs)\n"
            "Keep the content detailed and well-structured. "
            "Respond only with valid JSON matching the schema."
        ),
        chunk_token_threshold=2000,
        apply_chunking=False,
        input_format="html",
        extra_args={
            "temperature": 0.2,
            "max_tokens": 2000,
            "top_p": 0.9
        }
    )

    crawl_config = CrawlerRunConfig(
        extraction_strategy=llm_strat,
        cache_mode=CacheMode.BYPASS
    )

    try:
        async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
            logger.info("Crawler initialized, starting page processing...")
            result = await crawler.arun(url=url, config=crawl_config)

            if not result.success:
                logger.error(f"LLM parsing failed: {result.error_message}")
                return None

            try:
                parsed_data = json.loads(result.extracted_content)
                logger.info("Successfully parsed JSON response")
                
                if isinstance(parsed_data, list):
                    if len(parsed_data) > 0:
                        parsed_data = parsed_data[0]
                    else:
                        logger.error("Empty list in response")
                        return None
                
                if 'url' not in parsed_data:
                    parsed_data['url'] = url
                
                if 'images' not in parsed_data:
                    parsed_data['images'] = []
                elif not isinstance(parsed_data['images'], list):
                    parsed_data['images'] = [parsed_data['images']]
                
                logger.info(f"Extracted data: {json.dumps(parsed_data, indent=2, ensure_ascii=False)}")
                return WebPost(**parsed_data)
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {str(e)}\nRaw response: {result.extracted_content[:200]}...")
                return None
            except Exception as e:
                logger.error(f"Parsing error: {str(e)}")
                return None
                
    except Exception as e:
        logger.error(f"General error: {str(e)}")
        return None

async def main():
    test_url = "https://minfin.com.ua/ua/currency/articles/grazhdanestva/"
    
    openai_key = os.getenv("OPENAI_API_KEY") or input("Enter your OpenAI API key (if needed): ")
    
    logger.info(f"\n{'='*50}\nTesting LLM parser with URL: {test_url}\n{'='*50}")
    
    result = await parse_with_llm(test_url, openai_key)
    
    if result:
        logger.info("\n✅ Successfully extracted post:")
        logger.info(f"Title: {result.title}")
        logger.info(f"Content length: {len(result.content)} chars")
        logger.info(f"Images found: {len(result.images) if result.images else 0}")
    else:
        logger.error("❌ Failed to extract post")

if __name__ == "__main__":
    asyncio.run(main())