# Discord Bot Permission Fix

## Issue: Members can't use commands in any channel

This is a Discord server permission issue, not a bot code issue.

## Fix Steps:

### 1. Bot Role Permissions (Server Level)
1. Go to Server Settings → Roles
2. Find your bot's role (usually has the bot's name)
3. Enable these permissions:
   - View Channels
   - Send Messages
   - Use Slash Commands
   - Embed Links
   - Attach Files
   - Read Message History
   - Add Reactions

### 2. Channel-Specific Permissions
For each channel where the bot should work:
1. Right-click the channel → Edit Channel
2. Go to Permissions tab
3. Add the bot's role with these permissions:
   - View Channel: ✅
   - Send Messages: ✅
   - Use Slash Commands: ✅
   - Embed Links: ✅

### 3. Member Role Setup
1. Create a "Members" role if you don't have one
2. Give it these basic permissions:
   - View Channels
   - Send Messages
   - Use Slash Commands
   - Connect (for voice channels)
   - Speak (for voice channels)

### 4. Quick Test
After setting permissions, try these commands:
- `/ping` - Should work for everyone
- `/info` - Should work for everyone
- `/balance` - Should work for everyone

### 5. If Still Not Working
The bot might need to be re-invited with proper permissions:
1. Go to Discord Developer Portal
2. Select your application
3. Go to OAuth2 → URL Generator
4. Select "bot" and "applications.commands" scopes
5. Select these bot permissions:
   - Send Messages
   - Use Slash Commands
   - Embed Links
   - Read Message History
   - Connect
   - Speak
6. Use the generated URL to re-invite the bot

## Common Issues:
- Bot role is below other roles that deny permissions
- Channel-specific permission overrides blocking the bot
- Bot missing "Use Slash Commands" permission
- Server has slash commands disabled

Your bot code is correct - this is purely a Discord permission configuration issue.