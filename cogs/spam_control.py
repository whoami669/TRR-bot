import discord
from discord.ext import commands
from discord import app_commands

class SpamControl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.automation_disabled = True  # Start with automation disabled

    @app_commands.command(name="toggle_automation", description="Enable/disable automated engagement messages")
    @app_commands.describe(enabled="True to enable automated messages, False to disable")
    async def toggle_automation(self, interaction: discord.Interaction, enabled: bool):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You need administrator permissions to use this command.", ephemeral=True)
            return
        
        self.automation_disabled = not enabled
        status = "enabled" if enabled else "disabled"
        
        # Store the setting in bot instance for other cogs to check
        self.bot.automation_disabled = self.automation_disabled
        
        embed = discord.Embed(
            title="🔧 Automation Control",
            description=f"Automated engagement messages are now **{status}**",
            color=discord.Color.green() if enabled else discord.Color.red()
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="automation_status", description="Check current automation status")
    async def automation_status(self, interaction: discord.Interaction):
        status = "disabled" if getattr(self.bot, 'automation_disabled', True) else "enabled"
        color = discord.Color.red() if status == "disabled" else discord.Color.green()
        
        embed = discord.Embed(
            title="🤖 Automation Status",
            description=f"Automated messages are currently **{status}**",
            color=color
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(SpamControl(bot))
    # Set initial state
    bot.automation_disabled = True