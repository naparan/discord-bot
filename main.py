# インストールした discord.py を読み込む
import discord

# 自分のBotのアクセストークンに置き換えてください
TOKEN = 'MTMyNTE0NzMxNjIxODIzNzAwOQ.GYt56G.UDd8HlzHX50kBHHbw0Sq6mx5RiokSi88pq4x7c'

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

# 接続に必要なオブジェクトを生成
client = discord.Client(intents=intents)

# 起動時に動作する処理
@client.event
async def on_ready():
    # 起動したらターミナルにログイン通知が表示される
    print('ログインしました')

# メッセージ受信時に動作する処理
@client.event
async def on_message(message):
    print(f"受信メッセージ：{message.content}")
    # メッセージ送信者がBotだった場合は無視する
    if message.author.bot:
        return
    
    # 「/neko」と発言したら「にゃーん」が返る処理
    if message.content == '/np-schedule':
        await message.channel.send('イベントを作成します')
    elif message.content == '/np-neko':
        await message.channel.send('んにゃ=^_^=')
    

# Botの起動とDiscordサーバーへの接続
client.run(TOKEN)
