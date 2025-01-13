import discord
from discord.ext import commands
import asyncio
import pytz
import os

TOKEN = os.getenv("discord_token")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix="!",intents=intents)
event_cache = []

async def update_event_cache(guild):
    await bot.wait_until_ready()
    tz = pytz.timezone('Asia/Tokyo')
    while not bot.is_closed():
        if guild:
            global event_cache
            events = await guild.fetch_scheduled_events()
            event_cache = [
                f"{event.name} - {event.start_time.astimezone(tz).strftime('%Y-%m-%d %H:%M:%S')} - 説明：{event.description if event.description else '説明なし'}" for event in events
            ]
        await asyncio.sleep(60*5)

# 起動時に動作する処理
@bot.event
async def on_ready():
    print('ログインしました')
    for guild in bot.guilds:
        asyncio.create_task(update_event_cache(guild))

@bot.command(name='event')
async def event(ctx,subcommand=None):
    if subcommand == 'ls':
        if ctx.guild:
            if event_cache:
                response = "\n".join(event_cache)            
                await ctx.send(f"現在のイベント一覧：\n{response}")
            else:
                await ctx.send("現在設定されているイベントはありません")
        else:
            await ctx.send("このコマンドはDMで実行できません")
    
    if subcommand == 'test':
        await ctx.send(f"ほげ")

    else:
        await ctx.send(f"サブコマンド[{subcommand}]は存在しません")

# Botの起動とDiscordサーバーへの接続
bot.run(TOKEN)