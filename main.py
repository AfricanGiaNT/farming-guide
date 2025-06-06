import logging
import os
from dotenv import load_dotenv

load_dotenv()

from telegram.ext import Application, CommandHandler, MessageHandler, filters
from ai_agent import process_query
from database import init_db

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update, context):
    """Handle the /start command"""
    welcome_message = (
        "🌾 Welcome to the Agricultural Advisor Bot for Malawi, Lilongwe! 🌾\n\n"
        "I'm here to help you with farming advice specific to your region.\n"
        "Just send me your agricultural questions and I'll do my best to help!\n\n"
        "Examples:\n"
        "• What crops grow best in Lilongwe?\n"
        "• How to manage pests in maize?\n"
        "• When is the best time to plant beans?"
    )
    await update.message.reply_text(welcome_message)

async def help_command(update, context):
    """Handle the /help command"""
    help_text = (
        "🔍 How to use this bot:\n\n"
        "Simply type your agricultural question and send it to me.\n"
        "I'll search my knowledge base and online resources to provide you with accurate advice.\n\n"
        "Commands:\n"
        "/start - Welcome message\n"
        "/help - Show this help message\n"
        "/about - Learn more about this bot"
    )
    await update.message.reply_text(help_text)

async def about_command(update, context):
    """Handle the /about command"""
    about_text = (
        "ℹ️ About Agricultural Advisor Bot\n\n"
        "This bot provides agricultural advice specifically for farmers in Lilongwe, Malawi.\n"
        "It uses AI technology to deliver accurate, region-specific farming information.\n\n"
        "Stay informed and improve your farming practices! 🌱"
    )
    await update.message.reply_text(about_text)

async def handle_message(update, context):
    """Handle regular text messages"""
    query = update.message.text
    user_name = update.message.from_user.first_name or "Farmer"
    
    logger.info(f"Received query from {user_name}: {query}")
    
    # Send typing indicator
    await update.message.chat.send_action("typing")
    
    try:
        response = process_query(query)
        logger.info(f"Sending response to {user_name}")
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        await update.message.reply_text(
            "❌ Sorry, I encountered an error while processing your request. "
            "Please try again later or rephrase your question."
        )

def main():
    """Main function to run the bot"""
    # --- DEBUGGING LINE ---
    logger.info(f"--- [DEBUG] DATABASE_URL from env is: {os.getenv('DATABASE_URL')} ---")
    # --- END DEBUGGING LINE ---

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return
    
    # Get bot token
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        return
    
    # Create application
    app = Application.builder().token(bot_token).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    logger.info("Starting bot...")
    app.run_polling(allowed_updates=["message"])

if __name__ == "__main__":
    main() 