
import asyncio
import sys
from bot import Bot, web_app
from pyrogram import compose
from config import *

# Fix for Windows event loop
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    app = []

    # Create bot instance using config.py values
    app.append(
        Bot(
            SESSION,
            WORKERS,
            DB_CHANNEL,
            FSUBS,
            TOKEN,
            ADMINS,
            MESSAGES,
            AUTO_DEL,
            DB_URI,
            DB_NAME,
            API_ID,
            API_HASH,
            PROTECT,
            DISABLE_BTN
        )
    )

    await compose(app)


async def runner():
    await asyncio.gather(
        main(),
        web_app()
    )

asyncio.run(runner())
