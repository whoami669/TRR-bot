# Discord Bot Deployment Guide

## Current Bot Status
- **Commands**: 58 slash commands across 12 modules
- **Members Served**: 1,599 
- **Features**: AI automation, promotional engine, server events, viral content system
- **All automated messaging eliminated**

## GitHub Deployment

### 1. Clean Repository (Remove Sensitive Files)
```bash
# Remove database files (will be recreated)
rm -f *.db
rm -f viral_streamer_clips/ -rf
rm -f attached_assets/ -rf

# Remove environment file
rm -f .env
```

### 2. Update .gitignore
```
# Environment and secrets
.env
*.env

# Database files
*.db
*.sqlite
*.sqlite3

# Downloaded content
viral_streamer_clips/
downloads/

# Python cache
__pycache__/
*.pyc
*.pyo

# Logs
*.log

# OS files
.DS_Store
Thumbs.db

# IDE files
.vscode/
.idea/
*.swp
*.swo

# Temporary files
temp/
tmp/
attached_assets/
```

### 3. Git Commands
```bash
git add .
git commit -m "Complete Discord bot with AI automation, promotional engine, and viral content system"
git push origin main
```

## Heroku Deployment

### 1. Heroku Configuration Files

**Procfile** (already exists):
```
worker: python main.py
```

**runtime.txt**:
```
python-3.11
```

**requirements.txt** (updated):
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
PyNaCl
soundcloud-lib
yt-dlp
playwright
snscrape
aiofiles
```

### 2. Environment Variables Setup
Set these in Heroku dashboard or CLI:

```bash
heroku config:set DISCORD_TOKEN="your_discord_token"
heroku config:set OPENAI_API_KEY="your_openai_key"
heroku config:set DATABASE_URL="your_postgres_url"
```

### 3. Heroku Commands
```bash
# Login to Heroku
heroku login

# Create app (if not exists)
heroku create trrr-bot

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:essential-0

# Deploy
git push heroku main

# Check logs
heroku logs --tail
```

## Important Notes

### Database Migration
- SQLite databases will be recreated automatically
- All bot data and configurations will be fresh
- User data (economy, levels) will reset

### Features Included
1. **AI Features**: GPT-4o integration, autonomous analysis
2. **Server Events**: Welcome/leave/boost messages in separate channels
3. **Promotional Engine**: Social media content generation
4. **Viral Content**: Automated content discovery and TikTok preparation
5. **Economy & Leveling**: Full user progression system
6. **Moderation**: Advanced tools and automation
7. **Entertainment**: Games, jokes, trivia, memes

### Post-Deployment Setup
1. Run `/setup-welcome` to configure server events
2. Run `/setup-promotion` to enable growth features  
3. Run `/setup-viral-automation` for content automation
4. Run `/fix-bot-permissions` if needed

## Monitoring
- Check Heroku logs for any issues
- Monitor Discord API rate limits
- Verify all slash commands sync properly

Your bot is ready for production deployment with all advanced features operational.