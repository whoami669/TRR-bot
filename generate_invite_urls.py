import discord
import os
from dotenv import load_dotenv

load_dotenv()

# Your bot's client ID (from the logs)
CLIENT_ID = "1377680640023072838"

def generate_invite_urls():
    print("Discord Bot Invite URLs\n" + "="*50)
    
    # 1. Administrator permissions (simplest)
    admin_perms = discord.Permissions(administrator=True)
    admin_url = discord.utils.oauth_url(CLIENT_ID, permissions=admin_perms, scopes=["bot", "applications.commands"])
    print(f"1. ADMINISTRATOR (Recommended):")
    print(f"   {admin_url}\n")
    
    # 2. No permissions (basic)
    basic_url = discord.utils.oauth_url(CLIENT_ID, permissions=discord.Permissions.none(), scopes=["bot", "applications.commands"])
    print(f"2. NO PERMISSIONS (Basic):")
    print(f"   {basic_url}\n")
    
    # 3. Reaction support permissions (fixes reaction issues)
    reaction_perms = discord.Permissions(
        view_channel=True,
        send_messages=True,
        read_messages=True,
        read_message_history=True,
        add_reactions=True,  # Critical for reactions
        embed_links=True,
        attach_files=True,
        use_external_emojis=True,
        use_application_commands=True
    )
    reaction_url = discord.utils.oauth_url(CLIENT_ID, permissions=reaction_perms, scopes=["bot", "applications.commands"])
    print(f"3. REACTION SUPPORT (Fixes reaction issues):")
    print(f"   {reaction_url}\n")
    
    # 4. Full bot permissions (what your bot currently requests)
    full_perms = discord.Permissions(
        read_messages=True, send_messages=True, manage_messages=True,
        embed_links=True, attach_files=True, read_message_history=True,
        add_reactions=True, use_external_emojis=True, manage_channels=True,
        manage_roles=True, kick_members=True, ban_members=True,
        manage_guild=True, connect=True, speak=True, mute_members=True,
        deafen_members=True, move_members=True, use_voice_activation=True,
        manage_nicknames=True, manage_webhooks=True, view_audit_log=True
    )
    full_url = discord.utils.oauth_url(CLIENT_ID, permissions=full_perms, scopes=["bot", "applications.commands"])
    print(f"4. FULL PERMISSIONS (All Features):")
    print(f"   {full_url}\n")
    
    # 5. Bot scope only (no slash commands)
    bot_only_url = discord.utils.oauth_url(CLIENT_ID, permissions=admin_perms, scopes=["bot"])
    print(f"5. BOT SCOPE ONLY (No Slash Commands):")
    print(f"   {bot_only_url}\n")
    
    print("Try these URLs in order - start with #1 (Administrator) as it's the simplest.")
    print("If that doesn't work, try #2 (No Permissions) to test basic bot addition.")

if __name__ == "__main__":
    generate_invite_urls()