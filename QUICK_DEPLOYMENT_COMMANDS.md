# Quick Deployment Commands

Your Discord bot is ready for deployment with 58 commands across 12 modules.

## GitHub Deployment

### Clean and Prepare
```bash
# Remove sensitive files
rm -f *.db
rm -rf viral_streamer_clips/
rm -rf attached_assets/

# Stage all files
git add .

# Commit changes
git commit -m "Complete Discord bot: AI automation, promotional engine, viral content system - 58 commands, 12 modules"

# Push to GitHub
git push origin main
```

## Heroku Deployment

### Setup App
```bash
heroku login
heroku create trrr-bot
heroku addons:create heroku-postgresql:essential-0
```

### Configure Environment
```bash
heroku config:set DISCORD_TOKEN="your_token_here"
heroku config:set OPENAI_API_KEY="your_openai_key_here"
```

### Deploy
```bash
git push heroku main
heroku logs --tail
```

## Required Environment Variables
- DISCORD_TOKEN: Your Discord bot token
- OPENAI_API_KEY: OpenAI API key for GPT-4o features
- DATABASE_URL: Auto-configured by Heroku PostgreSQL

## Post-Deployment Setup Commands
Run these in your Discord server after deployment:
- `/setup-welcome` - Configure server events
- `/setup-promotion` - Enable growth features
- `/setup-viral-automation` - Setup content automation
- `/fix-bot-permissions` - Resolve any permission issues

Your bot includes all advanced features and is production-ready.