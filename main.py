import discord
from discord.ext import commands
import asyncio
import pytz
import os
from datetime import datetime
import aiohttp

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
        await asyncio.sleep(60)

# 起動時に動作する処理
@bot.event
async def on_ready():
    print('ログインしました')
    for guild in bot.guilds:
        asyncio.create_task(update_event_cache(guild))

@bot.event
async def on_command_error(ctx,error):
    if isinstance(error,commands.MissingRequiredArgument):
        await ctx.send("引数が不足しています")
    elif isinstance(error,commands.CommandNotFound):
        await ctx.send("存在しないコマンドです")
    else:
        await ctx.send("予期せぬエラーが発生しました")
        raise error
    
@bot.group(name='event',invoke_without_command=True)
async def event(ctx):
    await ctx.send("使いかた\n"
             "`!event create`：新規イベントを作成\n"
             "`!event ls`：予定イベントを表示")

@event.command(name='ls')
async def list(ctx):
    if ctx.guild:
        if event_cache:
            response = "\n".join(event_cache)            
            await ctx.send(f"現在のイベント一覧：\n{response}")
        else:
            await ctx.send("現在設定されているイベントはありません")
    else:
        await ctx.send("このコマンドはDMで実行できません")
        
@event.command(name='create')
async def create(ctx, name: str, start: str, description: str='説明なし'):
    try:
        tz = pytz.timezone('Asia/Tokyo')
        scheduled_time = tz.localize(datetime.fromisoformat(start))
        scheduled_time = scheduled_time.astimezone(pytz.utc)
        
        guild = ctx.guild.id
        channel = 1034068769343033348
        url = f"https://discord.com/api/v10/guilds/{guild}/scheduled-events"
        channel = discord.utils.get(ctx.guild.channels, id=1034068769343033348)
        if channel is None or not isinstance(channel, discord.VoiceChannel):
            await ctx.send("指定されたチャンネルはボイスチャンネルではありません。")
            return
        
        headers = {
            "Authorization" : f"Bot {bot.http.token}",
            "Content-Type" : "application/json",
        }
        
        event_data = {
            "name": name,
            "description" : description,
            "scheduled_start_time" : scheduled_time.isoformat(),
            "privacy_level" : 2, #guild only
            "entity_type" : 2, #voice
            "channel_id" : channel.id,
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url,headers=headers, json = event_data) as res:
                if res.status == 201 or res.status == 200:
                    await ctx.send(f"イベント{name}が作成されました")
                else:
                    error = await res.json()
                    await ctx.send(f"イベント作成に失敗しました")
                    print(f"{error}\nstatus code:{res.status}")
    except Exception as e:
        await ctx.send("イベント作成中にエラーが発生しました")
        print(f"error in 'def create()' :\n{e}")
    

# Botの起動とDiscordサーバーへの接続
bot.run(TOKEN)