# Ultra Discord Bot - 94 Commands

A comprehensive Discord server management bot with maximum functionality and AI-powered automation.

## Features

### 🤖 AI & Intelligence (15 Commands)
- **AI Chat**: Conversational AI with OpenAI integration
- **AI Personas**: Different AI personalities (therapist, comedian, philosopher)
- **AI Games**: 20 Questions, riddles, trivia, word games
- **AI Stories**: Interactive storytelling with branching narratives
- **Autonomous Analytics**: Self-improving server insights

### 🛡️ Advanced Moderation (12 Commands)
- **Smart Moderation**: Warn, tempban, kick with database tracking
- **Channel Management**: Lock/unlock, slowmode, purge messages
- **Auto-Moderation**: Content filtering and spam detection
- **Logging**: Comprehensive moderation action tracking

### 🎮 Entertainment & Games (15 Commands)
- **Fun Commands**: Jokes, memes, random facts
- **Interactive Games**: Trivia, word games, puzzles
- **AI Entertainment**: Creative writing, debates, roasts
- **Random Generators**: Names, colors, numbers, quotes

### 💰 Economy System (8 Commands)
- **Virtual Currency**: Earn and spend server coins
- **Daily Rewards**: Login bonuses and streaks
- **Gambling**: Coinflip, dice games, slots
- **Leaderboards**: Top earners and statistics

### 🎁 Giveaway Management (6 Commands)
- **Automated Giveaways**: Create, manage, and draw winners
- **Multiple Entry Methods**: Reactions, requirements, time limits
- **Winner Selection**: Fair random selection with verification
- **Announcement System**: Automated winner notifications

### ⚙️ Server Management (20 Commands)
- **Role Management**: Reaction roles, bulk role operations
- **Channel Setup**: Auto-create channels and categories
- **Server Analytics**: Member statistics, activity tracking
- **Permission Management**: Automated permission fixing

### 🔧 Enhanced Utilities (18 Commands)
- **QR Codes**: Generate QR codes for text/URLs
- **Weather**: Real-time weather information
- **Encoding**: Base64 encoding/decoding
- **Hashing**: MD5, SHA256 hash generation
- **Timestamps**: Discord timestamp formatting
- **URL Tools**: Link validation and expansion

## Quick Deploy

### Heroku Deployment
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

1. Click the deploy button
2. Set environment variables:
   - `DISCORD_TOKEN`: Your Discord bot token
   - `OPENAI_API_KEY`: Your OpenAI API key
3. Deploy and scale worker dyno

### Manual Installation
```bash
git clone https://github.com/yourusername/Ultra-Discord-Bot.git
cd Ultra-Discord-Bot
pip install -r requirements.txt
python main.py
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DISCORD_TOKEN` | Your Discord bot token from Discord Developer Portal | Yes |
| `OPENAI_API_KEY` | OpenAI API key for AI features | Yes |

## Bot Permissions

The bot requires these Discord permissions:
- Send Messages
- Use Slash Commands
- Manage Messages
- Manage Roles
- Manage Channels
- View Message History
- Add Reactions
- Embed Links
- Attach Files

## Command Categories

### AI Commands
- `/ai` - Chat with AI
- `/ai_persona` - AI personalities
- `/ai_story` - Interactive stories
- `/ai_games` - AI-powered games
- `/twenty_questions` - Classic guessing game

### Moderation
- `/warn` - Warn users
- `/tempban` - Temporary bans
- `/purge` - Delete messages
- `/lock` - Lock channels
- `/slowmode` - Set message rate limits

### Economy
- `/balance` - Check coins
- `/daily` - Daily rewards
- `/coinflip` - Gambling games
- `/leaderboard` - Top users

### Utilities
- `/qr` - Generate QR codes
- `/weather` - Weather lookup
- `/hash` - Generate hashes
- `/timestamp` - Discord timestamps
- `/base64` - Encode/decode text

### Server Management
- `/reaction_roles` - Self-assignable roles
- `/setup_channels` - Auto-create channels
- `/server_info` - Server statistics
- `/user_info` - User information

## Database

The bot uses SQLite databases for:
- User economy data
- Moderation logs and warnings
- Reaction role configurations
- Giveaway management
- AI conversation history
- Server analytics

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

- Join our Discord server for support
- Report issues on GitHub
- Check the wiki for detailed documentation

## License

This project is open source and available under the MIT License.

---

**Ultra Discord Bot** - Built for maximum Discord server automation and community engagement with 94 commands at Discord's maximum capacity.