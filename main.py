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
session = None

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
        print(f"Event information updated{datetime.now(tz)}")
        await asyncio.sleep(60)

# 起動時に動作する処理
@bot.event
async def on_ready():
    global session
    session = aiohttp.ClientSession()
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

@bot.event
async def on_disconnect():
    global session
    if session:
        await session.close()

@bot.group(name='event',invoke_without_command=True)
async def event(ctx):
    await ctx.send("使いかた\n"
             "`!event c`：新規イベントを作成\n"
             "`!event d`：イベントを削除\n"
             "`!event l`：予定イベントを表示\n"
             "`!event s`：イベントを開始")

@event.command(name='l')
async def list(ctx):
    if ctx.guild:
        if event_cache:
            response = "\n".join(event_cache)            
            await ctx.send(f"現在のイベント一覧：\n{response}")
        else:
            await ctx.send("現在設定されているイベントはありません")
    else:
        await ctx.send("このコマンドはDMで実行できません")
        
@event.command(name='c')
async def create(ctx, name: str, start: str, description: str='説明なし'):
    try:
        tz = pytz.timezone('Asia/Tokyo')
        scheduled_time = tz.localize(datetime.fromisoformat(start))
        print(f"TOKYO:{scheduled_time}")
        scheduled_time = scheduled_time.astimezone(pytz.utc)
        print(f"UTC:{scheduled_time}")

        now = datetime.now(pytz.utc)
        if scheduled_time < now:
            await ctx.send("指定された日時は過去のものです")
            return
        
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

@event.command(name='d')
async def delete(ctx, name: str):
    try:
        guild = ctx.guild.id
        url = f"https://discord.com/api/v10/guilds/{guild}/scheduled-events"

        headers = {
            "Authorization" : f"Bot {bot.http.token}",
            "Content-Type" : "application/json",
        }

        #対象のイベントを検索
        async def fetch_events():
            async with session.get(url, headers=headers) as res:
                if res.status == 429:
                    retry = float(res.headers.get("Retry-After","1"))
                    await ctx.send(f"リクエスト過多 {retry}秒後に再試行します")
                    await asyncio.sleep(retry)
                    return await fetch_events()
                elif res.status == 200:
                    return await res.json()
                else:
                    await ctx.send(f"イベントの取得に失敗しました\nステータスコード{res.status}")
                    return None
        
        async def delete_event(id):
            delete_url = f"{url}/{id}"
            async with session.delete(delete_url, headers=headers) as res:
                if res.status == 429:
                    retry = float(res.headers.get("Retry-After","1"))
                    await ctx.send(f"削除リクエスト過多 {retry}秒後に再試行します")
                    await asyncio.sleep(retry)
                    return delete_event(id)
                elif res.status == 204:
                    return True
                else:
                    await ctx.send(f"イベントの削除に失敗しました\nステータスコード{res.status}")
                    return False

        events = await fetch_events()
        if not events:
            return

        target_event = next((event for event in events if event['name'] == name),None) 
        if not target_event:
            await ctx.send(f"イベント{name}は見つかりませんでした")
            return
        
        event_id = target_event['id']
        if await delete_event(event_id):
            await ctx.send(f"イベント{name}が削除されました")
        else:
            await ctx.send(f"イベント{name}の削除に失敗しました")

    except Exception as e:
        await ctx.send("イベント削除中にエラーが発生しました")
        print(f"error in 'def delete()' :\n{e}")
    
@event.command(name='s')
async def start(ctx,name: str):
    
    try:
        guild = ctx.guild.id
        url = f"https://discord.com/api/v10/guilds/{guild}/scheduled-events"
        
        headers = {
            "Authorization" : f"Bot {bot.http.token}",
            "Content-Type" : "application/json",
        }
        
        async def fetch():
            async with session.get(url,headers=headers) as res:
                if res.status == 429:
                    retry = float(res.headers.get("Retry-After","1"))
                    await ctx.send(f"リクエスト過多 {retry}秒後に再試行します")
                    await asyncio.sleep(retry)
                    return await fetch()
                elif res.status == 200:
                    return await res.json()
                else:
                    await ctx.send("リクエストに失敗しました")
                    return None
                
        async def start_event(event_id):
            event_url = f"{url}/{event_id}"
            event_data = {"status":2}
            async with session.patch(event_url, headers=headers,json=event_data) as res:
                if res.status == 429:
                    retry = float(res.headers.get("Retry-After","1"))
                    await ctx.send(f"リクエスト過多 {retry}秒後に再試行します")
                    await asyncio.sleep(retry)
                    return await start_event(event_id)
                elif res.status == 200 or 204:
                    return True
                else:
                    return False
        
        events = await fetch()
        if not events:
            return
        
        target = next((event for event in events if event['name'] == name),None)
        if not target:
            await ctx.send(f"イベント{name}が見つかりませんでした")
            return
        
        event_id = target['id']
        if await start_event(event_id):
            await ctx.send(f"イベント{name}が開始されました")
        else:
            await ctx.send(f"イベント{name}の開始に失敗しました")
    except Exception as e:
        await ctx.send("イベント開始中にエラーが発生しました")
        print(f"error in 'def start()'：\n{e}")
# Botの起動とDiscordサーバーへの接続
bot.run(TOKEN)