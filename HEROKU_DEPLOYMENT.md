# Heroku Deployment Instructions

## Prerequisites
- Heroku CLI installed
- Git repository ready
- Heroku account created

## Step 1: Heroku App Setup

```bash
# Login to Heroku
heroku login

# Create new app (or use existing)
heroku create trrr-bot

# Add PostgreSQL database
heroku addons:create heroku-postgresql:essential-0
```

## Step 2: Environment Variables

Set these configuration variables in Heroku dashboard or via CLI:

```bash
heroku config:set DISCORD_TOKEN="your_discord_bot_token_here"
heroku config:set OPENAI_API_KEY="your_openai_api_key_here"
```

The DATABASE_URL will be automatically set by the PostgreSQL addon.

## Step 3: Prepare Files

Ensure these files exist in your repository root:

**Procfile**:
```
worker: python main.py
```

**runtime.txt**:
```
python-3.11
```

**requirements.txt**:
```
discord.py==2.5.2
python-dotenv==1.1.0
aiosqlite==0.21.0
youtube-dl==2021.12.17
Pillow==11.2.1
aiohttp==3.12.4
openai
psutil
spotipy
PyNaCl>=1.5.0
soundcloud-lib
yt-dlp
playwright
snscrape
aiofiles
```

## Step 4: Deploy

```bash
# Add Heroku remote (if not already added)
heroku git:remote -a trrr-bot

# Deploy to Heroku
git push heroku main

# Check deployment logs
heroku logs --tail

# Restart the worker if needed
heroku ps:restart worker
```

## Step 5: Post-Deployment Verification

```bash
# Check app status
heroku ps

# View logs
heroku logs --tail

# Check config vars
heroku config
```

## Database Configuration

The bot uses SQLite for development but will automatically create PostgreSQL tables on Heroku:
- User data (economy, levels, analytics)
- Server configurations
- AI decision tracking
- Content automation data

## Scaling

```bash
# Scale worker dynos
heroku ps:scale worker=1

# For high-traffic servers, consider upgrading:
heroku ps:scale worker=2
```

## Monitoring

```bash
# Real-time logs
heroku logs --tail

# Check dyno status
heroku ps

# View app metrics
heroku logs --source app
```

## Troubleshooting

Common issues and solutions:

1. **Bot not responding**: Check DISCORD_TOKEN is set correctly
2. **AI features failing**: Verify OPENAI_API_KEY is configured
3. **Database errors**: Ensure PostgreSQL addon is active
4. **Memory issues**: Consider upgrading dyno type

## Environment Variables Reference

- `DISCORD_TOKEN`: Discord bot authentication token
- `OPENAI_API_KEY`: OpenAI API key for GPT-4o features
- `DATABASE_URL`: PostgreSQL connection (auto-set by addon)

## Features Active After Deployment

- 58 slash commands across 12 modules
- Autonomous AI system with daily analysis
- Server events (welcome/leave/boost channels)
- Promotional content generation
- Viral content automation
- Advanced moderation tools
- Economy and leveling systems
- Real-time analytics and insights

Your bot will be fully operational on Heroku with all advanced features enabled.