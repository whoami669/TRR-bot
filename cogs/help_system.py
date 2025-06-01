import discord
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger(__name__)

class HelpSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="help", description="Comprehensive bot help and command list")
    @app_commands.describe(category="Specific help category")
    @app_commands.choices(category=[
        app_commands.Choice(name="AI & Intelligence", value="ai"),
        app_commands.Choice(name="Server Management", value="server"),
        app_commands.Choice(name="Games & Entertainment", value="games"),
        app_commands.Choice(name="Web Tools", value="web"),
        app_commands.Choice(name="Utilities", value="utilities"),
        app_commands.Choice(name="Moderation", value="moderation"),
        app_commands.Choice(name="Analytics", value="analytics"),
        app_commands.Choice(name="All Commands", value="all")
    ])
    async def help_command(self, interaction: discord.Interaction, category: str = "overview"):
        await interaction.response.defer()
        
        try:
            if category == "overview":
                embed = self.create_overview_embed()
            elif category == "ai":
                embed = self.create_ai_help_embed()
            elif category == "server":
                embed = self.create_server_help_embed()
            elif category == "games":
                embed = self.create_games_help_embed()
            elif category == "web":
                embed = self.create_web_help_embed()
            elif category == "utilities":
                embed = self.create_utilities_help_embed()
            elif category == "moderation":
                embed = self.create_moderation_help_embed()
            elif category == "analytics":
                embed = self.create_analytics_help_embed()
            elif category == "all":
                embed = self.create_all_commands_embed()
            else:
                embed = self.create_overview_embed()
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Help command error: {e}")
            await interaction.followup.send("Failed to display help information.")

    def create_overview_embed(self):
        embed = discord.Embed(
            title="🤖 Ultra Discord Bot - Command Overview",
            description="A comprehensive Discord bot with advanced AI, server management, games, and web tools.",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🧠 AI & Intelligence",
            value="• `/ai` - Chat with GPT-4o with memory\n• `/ai-clear` - Clear conversation\n• `/analyze-image` - AI vision analysis\n• `/generate-image` - DALL-E image generation\n• `/code-review` - AI code analysis",
            inline=False
        )
        
        embed.add_field(
            name="🎮 Games & Entertainment",
            value="• `/trivia` - Multi-category trivia\n• `/word-chain` - Word association game\n• `/guess-number` - Number guessing\n• `/rock-paper-scissors` - RPS with tournaments\n• `/riddle` - Riddles with hints",
            inline=False
        )
        
        embed.add_field(
            name="🌐 Web Tools",
            value="• `/url-info` - Website analysis\n• `/ip-lookup` - IP geolocation\n• `/speed-test` - Connection speed\n• `/http-headers` - Header analysis\n• `/ssl-check` - Certificate info",
            inline=False
        )
        
        embed.add_field(
            name="🛠️ Utilities",
            value="• `/qr-code` - Generate QR codes\n• `/password-generator` - Secure passwords\n• `/reminder` - Smart reminders\n• `/text-analysis` - Text metrics\n• `/color-palette` - Color tools",
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Server Management",
            value="• `/server-stats` - Detailed analytics\n• `/cleanup-channels` - Remove inactive\n• `/role-manager` - Advanced roles\n• `/backup-server` - Configuration backup\n• `/member-activity` - Activity analysis",
            inline=False
        )
        
        embed.set_footer(text="Use '/help category' for detailed command information")
        return embed

    def create_ai_help_embed(self):
        embed = discord.Embed(
            title="🧠 AI & Intelligence Commands",
            description="Advanced AI-powered features with OpenAI integration",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="💬 `/ai`",
            value="**Enhanced AI Chat with Memory**\n• Conversation memory per channel\n• Multiple model options (GPT-4o, GPT-4, GPT-3.5)\n• Custom system prompts\n• Response time tracking\n• Token usage analytics",
            inline=False
        )
        
        embed.add_field(
            name="🧹 `/ai-clear`",
            value="**Clear Conversation Memory**\n• Reset AI context for current channel\n• Fresh conversation start\n• Useful for topic changes",
            inline=False
        )
        
        embed.add_field(
            name="📸 `/analyze-image`",
            value="**AI Vision Analysis**\n• Upload any image for analysis\n• Detailed descriptions\n• Object recognition\n• Scene understanding\n• High/low detail options",
            inline=False
        )
        
        embed.add_field(
            name="🎨 `/generate-image`",
            value="**DALL-E Image Generation**\n• Create images from text\n• Multiple sizes and styles\n• HD quality options\n• Vivid or natural styles",
            inline=False
        )
        
        embed.add_field(
            name="🔍 `/code-review`",
            value="**AI Code Analysis**\n• Review code quality\n• Security suggestions\n• Best practices\n• Performance optimization tips",
            inline=False
        )
        
        embed.add_field(
            name="📊 `/ai-stats`",
            value="**Usage Statistics**\n• Personal AI usage tracking\n• Token consumption\n• Command frequency\n• Historical data",
            inline=False
        )
        
        embed.set_footer(text="All AI features require valid OpenAI API key")
        return embed

    def create_games_help_embed(self):
        embed = discord.Embed(
            title="🎮 Games & Entertainment Commands",
            description="Interactive games and entertainment features",
            color=discord.Color.orange()
        )
        
        embed.add_field(
            name="🧠 `/trivia`",
            value="**Multi-Category Trivia**\n• Categories: General, Science, History, Gaming, Tech\n• Difficulty levels: Easy, Medium, Hard\n• Customizable question count\n• Scoring system with leaderboards",
            inline=False
        )
        
        embed.add_field(
            name="🔗 `/word-chain`",
            value="**Word Association Game**\n• Multi-player word chains\n• Themed categories available\n• Time limits per turn\n• Anti-repeat protection\n• Turn-based gameplay",
            inline=False
        )
        
        embed.add_field(
            name="🎯 `/guess-number`",
            value="**Number Guessing Challenge**\n• Customizable number ranges\n• Adjustable guess limits\n• Hint system (too high/low)\n• Time tracking\n• Personal best scores",
            inline=False
        )
        
        embed.add_field(
            name="✂️ `/rock-paper-scissors`",
            value="**Enhanced RPS**\n• 1v1 battles\n• Tournament mode\n• Best-of-series format\n• DM-based moves\n• Elimination brackets",
            inline=False
        )
        
        embed.add_field(
            name="🧩 `/riddle`",
            value="**Riddle Challenges**\n• Difficulty levels\n• Progressive hint system\n• Scoring based on hints used\n• Time tracking\n• Various riddle categories",
            inline=False
        )
        
        embed.add_field(
            name="💡 `/hint`",
            value="**Get Riddle Hints**\n• Progressive clue system\n• Limited hints per riddle\n• Score impact tracking",
            inline=False
        )
        
        embed.set_footer(text="All games support score tracking and leaderboards")
        return embed

    def create_web_help_embed(self):
        embed = discord.Embed(
            title="🌐 Web Tools Commands",
            description="Comprehensive web analysis and testing tools",
            color=discord.Color.purple()
        )
        
        embed.add_field(
            name="🔍 `/url-info`",
            value="**Website Analysis**\n• Page title extraction\n• Meta description\n• Server information\n• Response codes\n• Security headers check\n• Content type analysis",
            inline=False
        )
        
        embed.add_field(
            name="🌍 `/ip-lookup`",
            value="**IP Geolocation**\n• Geographic location\n• ISP information\n• Organization details\n• Timezone data\n• Proxy/VPN detection\n• AS number lookup",
            inline=False
        )
        
        embed.add_field(
            name="⚡ `/speed-test`",
            value="**Connection Speed Test**\n• Download speed measurement\n• Server response time\n• Connection quality analysis\n• Real-time testing",
            inline=False
        )
        
        embed.add_field(
            name="📋 `/http-headers`",
            value="**HTTP Header Analysis**\n• Complete header listing\n• Security header verification\n• Cache configuration\n• Server technology detection\n• Categorized display",
            inline=False
        )
        
        embed.add_field(
            name="🔒 `/ssl-check`",
            value="**SSL Certificate Info**\n• Certificate validity\n• Expiration dates\n• Issuer information\n• Security algorithms\n• Chain verification",
            inline=False
        )
        
        embed.add_field(
            name="🌐 `/domain-whois`",
            value="**Domain WHOIS Lookup**\n• Registration information\n• Expiration dates\n• Registrar details\n• DNS servers\n• Contact information",
            inline=False
        )
        
        embed.set_footer(text="Web tools provide real-time data from external services")
        return embed

    def create_utilities_help_embed(self):
        embed = discord.Embed(
            title="🛠️ Utility Commands",
            description="Powerful productivity and utility tools",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="📱 `/qr-code`",
            value="**QR Code Generator**\n• Custom text encoding\n• Adjustable sizes\n• Color customization\n• Background options\n• High-quality output",
            inline=False
        )
        
        embed.add_field(
            name="🔐 `/password-generator`",
            value="**Secure Password Creation**\n• Customizable length (8-128)\n• Symbol inclusion options\n• Number preferences\n• Ambiguous character filtering\n• Strength analysis",
            inline=False
        )
        
        embed.add_field(
            name="⏰ `/reminder`",
            value="**Smart Reminder System**\n• Flexible time formats (5m, 2h, 1d)\n• Repeat intervals\n• Private DM options\n• Channel notifications\n• Persistent storage",
            inline=False
        )
        
        embed.add_field(
            name="📊 `/text-analysis`",
            value="**Advanced Text Metrics**\n• Word/character counts\n• Reading time estimation\n• Language detection\n• Readability scoring\n• Frequency analysis",
            inline=False
        )
        
        embed.add_field(
            name="🎨 `/color-palette`",
            value="**Color Tools**\n• Palette generation\n• Color format conversion\n• Complementary schemes\n• Monochromatic variations\n• Visual swatches",
            inline=False
        )
        
        embed.add_field(
            name="🔗 `/url-shortener`",
            value="**URL Shortening**\n• Custom aliases\n• Click tracking\n• Analytics dashboard\n• Expiration options",
            inline=False
        )
        
        embed.set_footer(text="Utilities are designed for maximum productivity")
        return embed

    def create_server_help_embed(self):
        embed = discord.Embed(
            title="⚙️ Server Management Commands",
            description="Advanced server administration and analytics",
            color=discord.Color.red()
        )
        
        embed.add_field(
            name="📊 `/server-stats`",
            value="**Comprehensive Server Analytics**\n• Member statistics\n• Channel breakdown\n• Activity metrics\n• Growth tracking\n• Most active users\n• Server information",
            inline=False
        )
        
        embed.add_field(
            name="🧹 `/cleanup-channels`",
            value="**Channel Cleanup Tool**\n• Identify inactive channels\n• Customizable inactivity period\n• Dry-run preview mode\n• Batch deletion\n• Safety confirmations",
            inline=False
        )
        
        embed.add_field(
            name="👑 `/role-manager`",
            value="**Advanced Role Management**\n• Assign/remove roles\n• Role information display\n• Bulk operations\n• Permission analysis\n• Audit logging",
            inline=False
        )
        
        embed.add_field(
            name="💾 `/backup-server`",
            value="**Server Configuration Backup**\n• Complete server settings\n• Channel structure\n• Role configurations\n• Permission overwrites\n• Downloadable files",
            inline=False
        )
        
        embed.add_field(
            name="📈 `/member-activity`",
            value="**Activity Pattern Analysis**\n• Individual user metrics\n• Server-wide statistics\n• Activity trends\n• Engagement scoring\n• Historical data",
            inline=False
        )
        
        embed.set_footer(text="Server management requires appropriate permissions")
        return embed

    def create_moderation_help_embed(self):
        embed = discord.Embed(
            title="🛡️ Moderation Commands",
            description="Advanced moderation and security features",
            color=discord.Color.dark_red()
        )
        
        embed.add_field(
            name="🔍 `/ai-review`",
            value="**AI-Powered User Analysis**\n• Behavior pattern detection\n• Risk assessment\n• Content analysis\n• Automated reports\n• Recommendation system",
            inline=False
        )
        
        embed.add_field(
            name="🔒 `/lockdown`",
            value="**Server Lockdown System**\n• Multiple intensity levels\n• Timed restrictions\n• Automatic unlock\n• Emergency protocols",
            inline=False
        )
        
        embed.add_field(
            name="🚫 `/content-filter`",
            value="**Advanced Content Filtering**\n• Custom pattern detection\n• Severity levels\n• Automated actions\n• Whitelist management",
            inline=False
        )
        
        embed.add_field(
            name="⚖️ `/ban-appeal`",
            value="**Ban Appeal System**\n• Structured appeal process\n• AI-assisted review\n• Decision tracking\n• Automated notifications",
            inline=False
        )
        
        embed.set_footer(text="Moderation features require moderator permissions")
        return embed

    def create_analytics_help_embed(self):
        embed = discord.Embed(
            title="📊 Analytics Commands",
            description="Detailed server and user analytics",
            color=discord.Color.teal()
        )
        
        embed.add_field(
            name="📈 `/view-analytics`",
            value="**Server Analytics Dashboard**\n• Message trends\n• User activity patterns\n• Growth metrics\n• Engagement rates",
            inline=False
        )
        
        embed.add_field(
            name="👤 `/user-statistics`",
            value="**Individual User Metrics**\n• Message frequency\n• Activity periods\n• Engagement scoring\n• Historical trends",
            inline=False
        )
        
        embed.add_field(
            name="🏥 `/server-health`",
            value="**Server Health Monitor**\n• Performance metrics\n• System status\n• Resource usage\n• Optimization suggestions",
            inline=False
        )
        
        embed.add_field(
            name="📤 `/export-data`",
            value="**Data Export Tools**\n• Analytics exports\n• Report generation\n• Historical data\n• Custom formats",
            inline=False
        )
        
        embed.set_footer(text="Analytics provide insights for server optimization")
        return embed

    def create_all_commands_embed(self):
        embed = discord.Embed(
            title="📚 Complete Command Reference",
            description="All available bot commands organized by category",
            color=discord.Color.blurple()
        )
        
        ai_commands = "ai, ai-clear, analyze-image, generate-image, code-review, ai-stats"
        games_commands = "trivia, word-chain, guess-number, rock-paper-scissors, riddle, hint"
        web_commands = "url-info, ip-lookup, speed-test, http-headers, ssl-check, domain-whois"
        utility_commands = "qr-code, password-generator, reminder, text-analysis, color-palette, url-shortener"
        server_commands = "server-stats, cleanup-channels, role-manager, backup-server, member-activity"
        mod_commands = "ai-review, lockdown, content-filter, ban-appeal, suspicious-alert"
        
        embed.add_field(name="🧠 AI Commands", value=f"`/{ai_commands.replace(', ', '`, `/') + '`'}", inline=False)
        embed.add_field(name="🎮 Games", value=f"`/{games_commands.replace(', ', '`, `/') + '`'}", inline=False)
        embed.add_field(name="🌐 Web Tools", value=f"`/{web_commands.replace(', ', '`, `/') + '`'}", inline=False)
        embed.add_field(name="🛠️ Utilities", value=f"`/{utility_commands.replace(', ', '`, `/') + '`'}", inline=False)
        embed.add_field(name="⚙️ Server Mgmt", value=f"`/{server_commands.replace(', ', '`, `/') + '`'}", inline=False)
        embed.add_field(name="🛡️ Moderation", value=f"`/{mod_commands.replace(', ', '`, `/') + '`'}", inline=False)
        
        embed.add_field(
            name="📊 Quick Stats",
            value=f"**Total Commands:** 100+\n**Categories:** 6\n**Active Features:** All modules loaded",
            inline=False
        )
        
        embed.set_footer(text="Use '/help category' for detailed information about each category")
        return embed

async def setup(bot):
    await bot.add_cog(HelpSystem(bot))