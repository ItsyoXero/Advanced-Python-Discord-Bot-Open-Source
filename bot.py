import discord
from discord.ext import commands
import asyncio
import random
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os
from discord.utils import oauth_url
import json
import os
from pathlib import Path
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
intents.messages = True
intents.message_content = True
intents.members = True
intents.presences = True
intents.guilds = True
intents.guild_messages = True
intents.dm_messages = True
intents.emojis = True
intents.bans = True
intents.invites = True
intents.voice_states = True
intents.webhooks = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    logging.info(f'Bot is ready! Logged in as {bot.user}')
    logging.info(f'Bot ID: {bot.user.id}')
    logging.info(f'Bot Name: {bot.user.name}')
    logging.info(f'Bot Discriminator: {bot.user.discriminator}')
    
    # Print guilds the bot is in
    for guild in bot.guilds:
        logging.info(f'Connected to guild: {guild.name} (ID: {guild.id})')

@bot.event
async def on_error(event, *args, **kwargs):
    logging.error(f'Error in {event}: {args} {kwargs}')
    raise

# Add OAuth2 URL command
@bot.command(name='invite')
async def invite(ctx):
    """Get the bot's invite link"""
    permissions = discord.Permissions(
        send_messages=True,
        embed_links=True,
        add_reactions=True,
        read_message_history=True,
        use_application_commands=True
    )
    
    url = discord.utils.oauth_url(
        bot.user.id,
        permissions=permissions,
        scopes=('bot', 'applications.commands')
    )
    
    embed = discord.Embed(
        title="🔗 Invite Link",
        description=f"[Click here to invite me to your server]({url})",
        color=discord.Color.blue()
    )
    
    await ctx.send(embed=embed)

class Giveaway:
    def __init__(self, prize, duration, channel_id, host_id, required_roles=None, blacklist=None):
        self.prize = prize
        self.start_time = datetime.now(pytz.utc)
        self.end_time = self.start_time + timedelta(minutes=duration)
        self.channel_id = channel_id
        self.host_id = host_id
        self.participants = set()
        self.required_roles = required_roles or []
        self.blacklist = blacklist or []
        self.message_id = None
        self.required_role_names = []

    def check_requirements(self, member):
        """Check if member meets requirements (roles and blacklist)"""
        if member.id in self.blacklist:
            return False

        if not self.required_roles:
            return True

        member_roles = [role.id for role in member.roles]
        
        # Check if user has any of the required roles
        has_required_role = any(role in self.required_roles for role in member_roles)
        
        # Get role names for the error message
        role_names = []
        for role_id in self.required_roles:
            role = discord.utils.get(member.guild.roles, id=role_id)
            if role:
                role_names.append(role.name)
        
        # Store role names for error message
        self.required_role_names = role_names
        
        return has_required_role

    def add_participant(self, user_id):
        self.participants.add(user_id)

    def remove_participant(self, user_id):
        self.participants.discard(user_id)

    def is_active(self):
        return datetime.now(pytz.utc) < self.end_time

    def select_winner(self):
        if not self.participants:
            return None
        return random.choice(list(self.participants))

active_giveaways = {}

@bot.event
async def on_ready():
    print(f'Bot is ready! Logged in as {bot.user}')

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return

    message_id = payload.message_id
    emoji = str(payload.emoji)

    for giveaway_id, giveaway in active_giveaways.items():
        if giveaway.message_id == message_id and emoji == '🎉':
            channel = bot.get_channel(giveaway.channel_id)
            member = channel.guild.get_member(payload.user_id)
            message = await channel.fetch_message(message_id)
            
            # Check requirements
            if not giveaway.check_requirements(member):
                # Remove their reaction
                await message.remove_reaction('🎉', member)
                # Notify them
                if member.id in giveaway.blacklist:
                    await member.send("❌ You are blacklisted from entering this giveaway!\n"
                                     "Please contact the giveaway host for more information.")
                else:
                    await member.send("❌ You don't meet the requirements to enter this giveaway!\n"
                                     f"Required roles: {', '.join(giveaway.required_role_names)}")
                return

            giveaway.add_participant(payload.user_id)
            await member.send(f"🎉 You've entered the giveaway for: {giveaway.prize}!")

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.user_id == bot.user.id:
        return

    message_id = payload.message_id
    emoji = str(payload.emoji)

    for giveaway_id, giveaway in active_giveaways.items():
        if giveaway.message_id == message_id and emoji == '🎉':
            giveaway.remove_participant(payload.user_id)
            
            # If the user is removing their reaction, check if they meet requirements
            channel = bot.get_channel(giveaway.channel_id)
            member = channel.guild.get_member(payload.user_id)
            
            if not giveaway.check_requirements(member):
                if member.id in giveaway.blacklist:
                    await member.send("❌ You are blacklisted from entering this giveaway!\n"
                                     "Please contact the giveaway host for more information.")
                else:
                    await member.send("❌ You don't meet the requirements to enter this giveaway!\n"
                                     f"Required roles: {', '.join(giveaway.required_role_names)}")

@bot.command(name='giveaway')
async def create_giveaway(ctx, duration: int, *, prize: str):
    """Create a new giveaway
    Usage: !giveaway [duration in minutes] [prize] [required_roles] [blacklist]
    
    Example: !giveaway 60 Nintendo Switch @Member @Premium @1234567890
    """
    
    # Get role mentions and blacklist users
    required_roles = []
    blacklist = []
    
    # Split the message to separate roles and blacklist
    parts = prize.split()
    
    # Process roles and blacklist
    for part in parts:
        if part.startswith('@') or part.isdigit():
            if part.startswith('@'):
                # Role mention
                role = discord.utils.get(ctx.guild.roles, name=part[1:])
                if role:
                    required_roles.append(role.id)
            else:
                # User ID (blacklist)
                blacklist.append(int(part))
        else:
            break
    
    # Get the actual prize text
    prize = ' '.join(parts[len(required_roles) + len(blacklist):])
    
    giveaway = Giveaway(
        prize=prize,
        duration=duration,
        channel_id=ctx.channel.id,
        host_id=ctx.author.id,
        required_roles=required_roles,
        blacklist=blacklist
    )

    embed = discord.Embed(
        title="🎉 New Giveaway! 🎉",
        description=f"**Prize:** {prize}\n"
                   f"**Hosted by:** {ctx.author.mention}\n"
                   f"**Duration:** {duration} minutes\n"
                   f"**Ends:** {giveaway.end_time.strftime('%Y-%m-%d %H:%M:%S')} UTC",
        color=discord.Color.gold()
    )
    embed.add_field(name="How to enter:", value="React with 🎉 to enter the giveaway!")

    message = await ctx.send(embed=embed)
    await message.add_reaction('🎉')
    giveaway.message_id = message.id
    active_giveaways[message.id] = giveaway

    await asyncio.sleep(duration * 60)
    await end_giveaway(message.id)

async def end_giveaway(message_id):
    giveaway = active_giveaways.get(message_id)
    if not giveaway or not giveaway.is_active():
        return

    channel = bot.get_channel(giveaway.channel_id)
    message = await channel.fetch_message(message_id)
    
    if not giveaway.participants:
        embed = discord.Embed(
            title="🎁 Giveaway Ended",
            description=f"No winners selected as no one participated",
            color=discord.Color.red()
        )
        await message.edit(embed=embed)
        del active_giveaways[message_id]
        return

    winner_id = giveaway.select_winner()
    winner = channel.guild.get_member(winner_id)
    
    embed = discord.Embed(
        title="🎁 Giveaway Ended",
        description=f"**Prize:** {giveaway.prize}\n"
                   f"**Winner:** {winner.mention}\n"
                   f"**Hosted by:** {giveaway.host_id}\n"
                   f"**Participants:** {len(giveaway.participants)}",
        color=discord.Color.green()
    )
    
    await message.edit(embed=embed)
    await channel.send(f"Congratulations {winner.mention}! You won the giveaway for {giveaway.prize}!")
    
    del active_giveaways[message_id]

@bot.command(name='reroll')
async def reroll_giveaway(ctx, message_id: int):
    """Reroll a giveaway winner
    Usage: !reroll [message_id]"""
    giveaway = active_giveaways.get(message_id)
    if not giveaway:
        await ctx.send("This giveaway has already ended or doesn't exist.")
        return

    if not giveaway.participants:
        await ctx.send("No participants to reroll from!")
        return

    winner_id = giveaway.select_winner()
    winner = ctx.guild.get_member(winner_id)
    await ctx.send(f"🎉 New winner is: {winner.mention}!")

@bot.command(name='end')
async def force_end_giveaway(ctx, message_id: int):
    """Force end a giveaway
    Usage: !end [message_id]"""
    await end_giveaway(message_id)

@bot.command(name='list')
async def list_giveaways(ctx):
    """List all active giveaways"""
    if not active_giveaways:
        await ctx.send("No active giveaways!")
        return

    embed = discord.Embed(
        title="Active Giveaways",
        color=discord.Color.blue()
    )
    
    for giveaway_id, giveaway in active_giveaways.items():
        channel = bot.get_channel(giveaway.channel_id)
        
        # Get role names for required roles
        role_names = []
        for role_id in giveaway.required_roles:
            role = discord.utils.get(ctx.guild.roles, id=role_id)
            if role:
                role_names.append(role.name)
        
        embed.add_field(
            name=f"#{channel.name} - {giveaway.prize}",
            value=f"Ends: {giveaway.end_time.strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
                  f"Participants: {len(giveaway.participants)}\n"
                  f"Required Roles: {', '.join(role_names) if role_names else 'None'}",
            inline=False
        )

    await ctx.send(embed=embed)

bot.run(os.getenv('DISCORD_TOKEN'))
