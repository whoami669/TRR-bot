import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import asyncio
import re
from datetime import datetime, timezone, timedelta
from typing import Optional

class ProductivityTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="todo", description="Manage your todo list")
    @app_commands.describe(
        action="What to do with your todo list",
        task="Task description (for add action)",
        task_id="Task ID (for complete/delete actions)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Add Task", value="add"),
        app_commands.Choice(name="List Tasks", value="list"),
        app_commands.Choice(name="Complete Task", value="complete"),
        app_commands.Choice(name="Delete Task", value="delete"),
        app_commands.Choice(name="Clear All", value="clear")
    ])
    async def todo_list(self, interaction: discord.Interaction, 
                       action: str, task: str = None, task_id: int = None):
        
        async with aiosqlite.connect('ultrabot.db') as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS todo_lists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    guild_id INTEGER,
                    task TEXT,
                    completed BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            if action == "add":
                if not task:
                    await interaction.response.send_message("❌ Please provide a task description!", ephemeral=True)
                    return
                
                await db.execute('''
                    INSERT INTO todo_lists (user_id, guild_id, task)
                    VALUES (?, ?, ?)
                ''', (interaction.user.id, interaction.guild.id, task))
                await db.commit()
                
                embed = discord.Embed(
                    title="✅ Task Added",
                    description=f"Added: **{task}**",
                    color=discord.Color.green()
                )
                
            elif action == "list":
                async with db.execute('''
                    SELECT id, task, completed FROM todo_lists 
                    WHERE user_id = ? AND guild_id = ?
                    ORDER BY completed ASC, created_at ASC
                ''', (interaction.user.id, interaction.guild.id)) as cursor:
                    tasks = await cursor.fetchall()
                
                if not tasks:
                    await interaction.response.send_message("📝 Your todo list is empty!", ephemeral=True)
                    return
                
                embed = discord.Embed(
                    title="📝 Your Todo List",
                    color=discord.Color.blue()
                )
                
                pending_tasks = [t for t in tasks if not t[2]]
                completed_tasks = [t for t in tasks if t[2]]
                
                if pending_tasks:
                    pending_text = "\n".join([f"`{t[0]}` {t[1]}" for t in pending_tasks[:10]])
                    embed.add_field(name="📋 Pending", value=pending_text, inline=False)
                
                if completed_tasks:
                    completed_text = "\n".join([f"~~`{t[0]}` {t[1]}~~" for t in completed_tasks[:5]])
                    embed.add_field(name="✅ Completed", value=completed_text, inline=False)
                
            elif action == "complete":
                if task_id is None:
                    await interaction.response.send_message("❌ Please provide a task ID!", ephemeral=True)
                    return
                
                await db.execute('''
                    UPDATE todo_lists SET completed = 1 
                    WHERE id = ? AND user_id = ? AND guild_id = ?
                ''', (task_id, interaction.user.id, interaction.guild.id))
                await db.commit()
                
                embed = discord.Embed(
                    title="✅ Task Completed",
                    description=f"Marked task `{task_id}` as completed",
                    color=discord.Color.green()
                )
                
            elif action == "delete":
                if task_id is None:
                    await interaction.response.send_message("❌ Please provide a task ID!", ephemeral=True)
                    return
                
                await db.execute('''
                    DELETE FROM todo_lists 
                    WHERE id = ? AND user_id = ? AND guild_id = ?
                ''', (task_id, interaction.user.id, interaction.guild.id))
                await db.commit()
                
                embed = discord.Embed(
                    title="🗑️ Task Deleted",
                    description=f"Deleted task `{task_id}`",
                    color=discord.Color.red()
                )
                
            elif action == "clear":
                await db.execute('''
                    DELETE FROM todo_lists 
                    WHERE user_id = ? AND guild_id = ?
                ''', (interaction.user.id, interaction.guild.id))
                await db.commit()
                
                embed = discord.Embed(
                    title="🧹 Todo List Cleared",
                    description="All tasks have been removed",
                    color=discord.Color.orange()
                )
            
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="study-session", description="Start a focused study session with breaks")
    @app_commands.describe(
        duration="Study duration in minutes",
        break_duration="Break duration in minutes",
        subject="Subject you're studying"
    )
    async def study_session(self, interaction: discord.Interaction, 
                           duration: int = 25, break_duration: int = 5, 
                           subject: str = "General Study"):
        
        if duration > 120 or duration < 5:
            await interaction.response.send_message("❌ Study duration must be between 5-120 minutes!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📚 Study Session Started",
            description=f"**Subject:** {subject}\n**Duration:** {duration} minutes\n**Break:** {break_duration} minutes",
            color=discord.Color.blue()
        )
        embed.add_field(name="Status", value="🔴 Studying...", inline=False)
        embed.set_footer(text="Good luck with your studies!")
        
        message = await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        
        # Study period
        await asyncio.sleep(duration * 60)
        
        # Update for break
        embed.set_field_at(0, name="Status", value="🟢 Break time!", inline=False)
        embed.color = discord.Color.green()
        
        await message.edit(embed=embed)
        
        # Break period
        await asyncio.sleep(break_duration * 60)
        
        # Session complete
        embed.set_field_at(0, name="Status", value="✅ Session Complete!", inline=False)
        embed.color = discord.Color.gold()
        
        await message.edit(embed=embed)

    @app_commands.command(name="note", description="Save and manage notes")
    @app_commands.describe(
        action="What to do with notes",
        title="Note title",
        content="Note content"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Create Note", value="create"),
        app_commands.Choice(name="List Notes", value="list"),
        app_commands.Choice(name="View Note", value="view"),
        app_commands.Choice(name="Delete Note", value="delete")
    ])
    async def manage_notes(self, interaction: discord.Interaction,
                          action: str, title: str = None, content: str = None):
        
        async with aiosqlite.connect('ultrabot.db') as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    guild_id INTEGER,
                    title TEXT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            if action == "create":
                if not title or not content:
                    await interaction.response.send_message("❌ Please provide both title and content!", ephemeral=True)
                    return
                
                await db.execute('''
                    INSERT INTO user_notes (user_id, guild_id, title, content)
                    VALUES (?, ?, ?, ?)
                ''', (interaction.user.id, interaction.guild.id, title, content))
                await db.commit()
                
                embed = discord.Embed(
                    title="📝 Note Created",
                    description=f"**Title:** {title}",
                    color=discord.Color.green()
                )
                embed.add_field(name="Content Preview", value=content[:100] + ("..." if len(content) > 100 else ""), inline=False)
                
            elif action == "list":
                async with db.execute('''
                    SELECT id, title, created_at FROM user_notes 
                    WHERE user_id = ? AND guild_id = ?
                    ORDER BY created_at DESC LIMIT 10
                ''', (interaction.user.id, interaction.guild.id)) as cursor:
                    notes = await cursor.fetchall()
                
                if not notes:
                    await interaction.response.send_message("📝 No notes found!", ephemeral=True)
                    return
                
                embed = discord.Embed(
                    title="📚 Your Notes",
                    color=discord.Color.blue()
                )
                
                for note_id, note_title, created in notes:
                    created_date = datetime.fromisoformat(created).strftime("%m/%d/%Y")
                    embed.add_field(name=f"`{note_id}` {note_title}", value=f"Created: {created_date}", inline=False)
                
            elif action == "view":
                if not title:
                    await interaction.response.send_message("❌ Please provide note title or ID!", ephemeral=True)
                    return
                
                # Try to find by ID first, then by title
                query = '''
                    SELECT title, content, created_at FROM user_notes 
                    WHERE user_id = ? AND guild_id = ? AND (id = ? OR title LIKE ?)
                    LIMIT 1
                '''
                
                try:
                    note_id = int(title)
                    params = (interaction.user.id, interaction.guild.id, note_id, f"%{title}%")
                except:
                    params = (interaction.user.id, interaction.guild.id, -1, f"%{title}%")
                
                async with db.execute(query, params) as cursor:
                    note = await cursor.fetchone()
                
                if not note:
                    await interaction.response.send_message("❌ Note not found!", ephemeral=True)
                    return
                
                embed = discord.Embed(
                    title=f"📝 {note[0]}",
                    description=note[1],
                    color=discord.Color.blue()
                )
                embed.set_footer(text=f"Created: {datetime.fromisoformat(note[2]).strftime('%B %d, %Y at %I:%M %p')}")
                
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="habit-tracker", description="Track your daily habits")
    @app_commands.describe(
        action="What to do with habit tracking",
        habit="Habit name",
        target="Target count/frequency"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Add Habit", value="add"),
        app_commands.Choice(name="Log Habit", value="log"),
        app_commands.Choice(name="View Progress", value="progress"),
        app_commands.Choice(name="Remove Habit", value="remove")
    ])
    async def habit_tracker(self, interaction: discord.Interaction,
                           action: str, habit: str = None, target: int = 1):
        
        async with aiosqlite.connect('ultrabot.db') as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS habits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    guild_id INTEGER,
                    habit_name TEXT,
                    target_count INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS habit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    habit_id INTEGER,
                    user_id INTEGER,
                    log_date DATE,
                    count INTEGER DEFAULT 1,
                    FOREIGN KEY (habit_id) REFERENCES habits (id)
                )
            ''')
            
            if action == "add":
                if not habit:
                    await interaction.response.send_message("❌ Please provide a habit name!", ephemeral=True)
                    return
                
                await db.execute('''
                    INSERT INTO habits (user_id, guild_id, habit_name, target_count)
                    VALUES (?, ?, ?, ?)
                ''', (interaction.user.id, interaction.guild.id, habit, target))
                await db.commit()
                
                embed = discord.Embed(
                    title="🎯 Habit Added",
                    description=f"**Habit:** {habit}\n**Daily Target:** {target}",
                    color=discord.Color.green()
                )
                
            elif action == "log":
                if not habit:
                    await interaction.response.send_message("❌ Please provide a habit name!", ephemeral=True)
                    return
                
                # Find habit
                async with db.execute('''
                    SELECT id FROM habits 
                    WHERE user_id = ? AND guild_id = ? AND habit_name LIKE ?
                ''', (interaction.user.id, interaction.guild.id, f"%{habit}%")) as cursor:
                    habit_result = await cursor.fetchone()
                
                if not habit_result:
                    await interaction.response.send_message("❌ Habit not found!", ephemeral=True)
                    return
                
                habit_id = habit_result[0]
                today = datetime.now(timezone.utc).date()
                
                # Log or update today's entry
                await db.execute('''
                    INSERT OR REPLACE INTO habit_logs (habit_id, user_id, log_date, count)
                    VALUES (?, ?, ?, COALESCE((
                        SELECT count + 1 FROM habit_logs 
                        WHERE habit_id = ? AND user_id = ? AND log_date = ?
                    ), 1))
                ''', (habit_id, interaction.user.id, today, habit_id, interaction.user.id, today))
                await db.commit()
                
                embed = discord.Embed(
                    title="✅ Habit Logged",
                    description=f"Logged progress for **{habit}** today!",
                    color=discord.Color.green()
                )
                
            elif action == "progress":
                async with db.execute('''
                    SELECT h.habit_name, h.target_count, 
                           COUNT(hl.id) as days_logged,
                           COALESCE(SUM(hl.count), 0) as total_count
                    FROM habits h
                    LEFT JOIN habit_logs hl ON h.id = hl.habit_id 
                        AND hl.log_date >= date('now', '-30 days')
                    WHERE h.user_id = ? AND h.guild_id = ?
                    GROUP BY h.id, h.habit_name, h.target_count
                ''', (interaction.user.id, interaction.guild.id)) as cursor:
                    habits = await cursor.fetchall()
                
                if not habits:
                    await interaction.response.send_message("📊 No habits tracked yet!", ephemeral=True)
                    return
                
                embed = discord.Embed(
                    title="📊 Habit Progress (Last 30 Days)",
                    color=discord.Color.blue()
                )
                
                for habit_name, target, days_logged, total_count in habits:
                    expected_total = target * 30
                    completion_rate = (total_count / expected_total * 100) if expected_total > 0 else 0
                    
                    progress_bar = "▓" * int(completion_rate // 10) + "░" * (10 - int(completion_rate // 10))
                    
                    embed.add_field(
                        name=f"🎯 {habit_name}",
                        value=f"{progress_bar} {completion_rate:.1f}%\n"
                              f"Days logged: {days_logged}/30 | Total: {total_count}/{expected_total}",
                        inline=False
                    )
            
            await interaction.response.send_message(embed=embed)

    @app_commands.command(name="goal", description="Set and track long-term goals")
    @app_commands.describe(
        action="What to do with goals",
        title="Goal title",
        description="Goal description",
        deadline="Deadline (YYYY-MM-DD format)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Create Goal", value="create"),
        app_commands.Choice(name="List Goals", value="list"),
        app_commands.Choice(name="Update Progress", value="update"),
        app_commands.Choice(name="Complete Goal", value="complete")
    ])
    async def goal_management(self, interaction: discord.Interaction,
                             action: str, title: str = None, description: str = None, 
                             deadline: str = None):
        
        async with aiosqlite.connect('ultrabot.db') as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    guild_id INTEGER,
                    title TEXT,
                    description TEXT,
                    deadline DATE,
                    progress INTEGER DEFAULT 0,
                    completed BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            if action == "create":
                if not title:
                    await interaction.response.send_message("❌ Please provide a goal title!", ephemeral=True)
                    return
                
                deadline_date = None
                if deadline:
                    try:
                        deadline_date = datetime.strptime(deadline, "%Y-%m-%d").date()
                    except:
                        await interaction.response.send_message("❌ Invalid date format! Use YYYY-MM-DD", ephemeral=True)
                        return
                
                await db.execute('''
                    INSERT INTO goals (user_id, guild_id, title, description, deadline)
                    VALUES (?, ?, ?, ?, ?)
                ''', (interaction.user.id, interaction.guild.id, title, description, deadline_date))
                await db.commit()
                
                embed = discord.Embed(
                    title="🎯 Goal Created",
                    description=f"**{title}**",
                    color=discord.Color.green()
                )
                if description:
                    embed.add_field(name="Description", value=description, inline=False)
                if deadline_date:
                    embed.add_field(name="Deadline", value=deadline_date.strftime("%B %d, %Y"), inline=True)
                
            elif action == "list":
                async with db.execute('''
                    SELECT id, title, deadline, progress, completed 
                    FROM goals 
                    WHERE user_id = ? AND guild_id = ?
                    ORDER BY completed ASC, deadline ASC
                ''', (interaction.user.id, interaction.guild.id)) as cursor:
                    goals = await cursor.fetchall()
                
                if not goals:
                    await interaction.response.send_message("🎯 No goals set yet!", ephemeral=True)
                    return
                
                embed = discord.Embed(
                    title="🎯 Your Goals",
                    color=discord.Color.blue()
                )
                
                for goal_id, goal_title, goal_deadline, progress, completed in goals[:5]:
                    status = "✅ Completed" if completed else f"🔄 {progress}% complete"
                    deadline_text = f" (Due: {goal_deadline})" if goal_deadline else ""
                    
                    embed.add_field(
                        name=f"`{goal_id}` {goal_title}",
                        value=f"{status}{deadline_text}",
                        inline=False
                    )
            
            await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ProductivityTools(bot))