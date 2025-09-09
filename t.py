import asyncio
import httpx

url = "https://www.atptour.com/-/media/images/news/2025/09/08/20/07/draper-us-open-2025-ends-season.jpg"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Referer": "https://www.atptour.com/",
    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
}

async def download_image():
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        with open("draper.jpg", "wb") as f:
            f.write(resp.content)
    print("Downloaded successfully")

asyncio.run(download_image())
