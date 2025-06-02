# Quick Start Guide 🚀

Get your Agricultural Advisor Bot running in 5 minutes!

## Prerequisites Checklist ✅

Before starting, ensure you have:
- [ ] Python 3.9+ installed
- [ ] PostgreSQL installed
- [ ] Telegram account
- [ ] OpenAI account
- [ ] Google Cloud account

## Step 1: Clone and Setup (1 minute)

```bash
# Clone the repository
git clone https://github.com/yourusername/farming-guide.git
cd farming-guide

# Run the setup script (macOS/Linux)
./setup.sh

# Or manually on Windows:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Step 2: Get Your API Keys (3 minutes)

### Telegram Bot Token
1. Open Telegram, search for **@BotFather**
2. Send `/newbot`
3. Choose a name (e.g., "Malawi Agri Bot")
4. Choose a username (e.g., "malawi_agri_bot")
5. Copy the token

### OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy the key

### Google Custom Search
1. Go to https://console.cloud.google.com
2. Create new project
3. Enable "Custom Search API"
4. Create credentials → API Key
5. Go to https://programmablesearchengine.google.com
6. Create new search engine
7. Copy the Search Engine ID

## Step 3: Configure Environment (30 seconds)

```bash
# Copy the example file
cp env.example .env

# Edit with your favorite editor
nano .env  # or vim, code, etc.
```

Add your keys:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
OPENAI_API_KEY=sk-your_openai_key_here
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_CSE_ID=your_search_engine_id_here
DATABASE_URL=postgresql://localhost/agri_bot
```

## Step 4: Test Everything (30 seconds)

```bash
python test_bot.py
```

All tests should pass ✅

## Step 5: Run the Bot! 🎉

```bash
python main.py
```

Open Telegram, search for your bot, and start chatting!

## Test Messages to Try

Send these to your bot:
- "What crops grow best in Lilongwe?"
- "When should I plant maize?"
- "How to manage pests in my garden?"

## Troubleshooting 🔧

### Database Connection Failed
```bash
# Create the database manually
createdb agri_bot

# Or with PostgreSQL running:
psql -U postgres -c "CREATE DATABASE agri_bot;"
```

### Bot Not Responding
- Check if the bot is running (terminal should show "Starting bot...")
- Verify your Telegram token is correct
- Make sure you started a conversation with `/start`

### API Errors
- Check your API keys are correctly copied
- Ensure you have credits/quota in your accounts
- Google Search allows 100 free queries/day

## Next Steps 📚

1. Read the full [README.md](README.md) for detailed documentation
2. Deploy to Heroku for 24/7 availability
3. Customize responses in `database.py`
4. Add more agricultural data
5. Join our community for support

## Need Help? 🤝

- Create an issue on GitHub
- Check existing issues for solutions
- Read the detailed setup in README.md

---

**Happy Farming! 🌾** 