import asyncio
import os
from telegram import Bot
from dotenv import load_dotenv

async def clear_webhook():
    """
    Clears the webhook for the Telegram bot.
    """
    load_dotenv()
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print("Error: TELEGRAM_BOT_TOKEN not found in environment variables.")
        return

    bot = Bot(token=bot_token)
    await bot.delete_webhook()
    print("Webhook has been cleared.")

if __name__ == "__main__":
    asyncio.run(clear_webhook()) 