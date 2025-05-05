import os
import asyncio
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("USERBOT_API_ID")
API_HASH = os.getenv("USERBOT_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")

async def main():
    print(PHONE, API_ID, API_HASH)
    client = TelegramClient('sessions/userbot', API_ID, API_HASH)
    await client.start(phone=PHONE)
    print("Авторизацiя пройшла успiшно.")
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
