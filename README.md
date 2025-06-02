# Agricultural Advisor Bot for Malawi, Lilongwe 🌾

An AI-powered Telegram bot that provides region-specific agricultural advice to farmers in Lilongwe, Malawi. The bot uses a local PostgreSQL knowledge base, Google Custom Search API for real-time information, and OpenAI's GPT model for intelligent responses.

## Features 🚀

- **Telegram Interface**: Easy-to-use chat interface for farmers
- **Local Knowledge Base**: PostgreSQL database with curated agricultural information
- **Smart Search**: Searches local database first, then online resources
- **AI-Powered Responses**: Uses OpenAI GPT to generate contextual advice
- **Self-Improving**: Saves new successful query-response pairs
- **Region-Specific**: Tailored for Lilongwe's climate and farming conditions

## Prerequisites 📋

- Python 3.9 or higher
- PostgreSQL database
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- OpenAI API Key
- Google Custom Search API Key and CSE ID

## Installation 🛠️

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/farming-guide.git
cd farming-guide
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up PostgreSQL Database

```bash
# Create a new database
createdb agri_bot

# Or using psql
psql -U postgres -c "CREATE DATABASE agri_bot;"
```

### 5. Configure Environment Variables

Copy `env.example` to `.env` and fill in your credentials:

```bash
cp env.example .env
```

Edit `.env` with your actual values:
```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_google_cse_id
DATABASE_URL=postgresql://username:password@localhost:5432/agri_bot
```

### 6. Run the Bot Locally

```bash
python main.py
```

## Setting Up External Services 🔧

### Telegram Bot
1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` and follow the instructions
3. Save the bot token provided

### OpenAI API
1. Sign up at [OpenAI](https://openai.com)
2. Navigate to [API Keys](https://platform.openai.com/api-keys)
3. Create a new API key

### Google Custom Search
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable Custom Search API
4. Create credentials (API Key)
5. Set up a Custom Search Engine at [CSE](https://programmablesearchengine.google.com)

## Deployment on Heroku 🚀

### 1. Install Heroku CLI
Download from [Heroku Dev Center](https://devcenter.heroku.com/articles/heroku-cli)

### 2. Create Heroku App

```bash
heroku create your-app-name
```

### 3. Add PostgreSQL

```bash
heroku addons:create heroku-postgresql:mini
```

### 4. Set Environment Variables

```bash
heroku config:set TELEGRAM_BOT_TOKEN=your_token
heroku config:set OPENAI_API_KEY=your_key
heroku config:set GOOGLE_API_KEY=your_key
heroku config:set GOOGLE_CSE_ID=your_cse_id
```

### 5. Deploy

```bash
git add .
git commit -m "Initial deployment"
git push heroku main
```

### 6. Scale the Worker

```bash
heroku ps:scale worker=1
```

### 7. Check Logs

```bash
heroku logs --tail
```

## Usage 💬

### Bot Commands
- `/start` - Welcome message and introduction
- `/help` - Display help information
- `/about` - Learn about the bot

### Example Queries
- "What crops grow best in Lilongwe?"
- "When should I plant maize?"
- "How to manage fall armyworm in my field?"
- "What fertilizer should I use for groundnuts?"
- "Best practices for tobacco farming"

## Project Structure 📁

```
farming-guide/
├── main.py           # Telegram bot setup and message handling
├── database.py       # Database operations and schema
├── ai_agent.py       # Query processing and AI integration
├── search.py         # Google Custom Search implementation
├── requirements.txt  # Python dependencies
├── Procfile         # Heroku deployment configuration
├── runtime.txt      # Python version specification
├── env.example      # Environment variables template
└── README.md        # Project documentation
```

## Database Schema 📊

### `advice` table
- `id` (SERIAL PRIMARY KEY)
- `query` (TEXT) - User's question
- `response` (TEXT) - Bot's response
- `created_at` (TIMESTAMP) - When the entry was created
- `search_count` (INTEGER) - How many times this query was searched

### `query_logs` table
- `id` (SERIAL PRIMARY KEY)
- `user_query` (TEXT) - Original user query
- `response_source` (VARCHAR) - Source of response (database/online/ai_generated)
- `created_at` (TIMESTAMP) - When the query was made

## Development Tips 🔨

### Adding New Agricultural Data

```python
# In database.py, add to insert_initial_data()
new_data = [
    ("Your question here", "Your detailed response here"),
    # Add more Q&A pairs
]
```

### Testing Locally

1. Set up a test database
2. Use a test bot token
3. Run with debug logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

### Monitoring Performance

- Check Heroku metrics: `heroku logs --tail`
- Monitor API usage in respective dashboards
- Review popular queries: Query the `advice` table by `search_count`

## Cost Management 💰

- **OpenAI**: Monitor token usage, consider using GPT-3.5-turbo for cost efficiency
- **Google Search**: Free tier allows 100 searches/day
- **Heroku**: Free tier discontinued, use Eco dynos ($5/month)
- **Database**: Heroku Postgres Mini plan (~$5/month)

## Contributing 🤝

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Future Enhancements 🔮

- [ ] Multi-language support (Chichewa)
- [ ] Weather API integration
- [ ] Image recognition for crop disease identification
- [ ] Voice message support
- [ ] SMS integration for farmers without internet
- [ ] Seasonal reminders and alerts
- [ ] Market price information
- [ ] Farmer community features

## Support 📞

For agricultural advice:
- Lilongwe ADD Office: +265 1 754 244
- Ministry of Agriculture: +265 1 789 033

For technical issues:
- Create an issue on GitHub
- Contact the development team

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments 🙏

- Ministry of Agriculture, Malawi
- Lilongwe Agricultural Development Division
- FAO and CGIAR for agricultural data
- The farming community of Lilongwe

---

Made with ❤️ for the farmers of Malawi # farming-guide
