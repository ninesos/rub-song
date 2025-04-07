import discord
import re
import requests
import asyncio
import os
from flask import Flask
import threading

TOKEN = os.getenv('TOKEN')

TARGET_CHANNEL_ID = 1358457724941373480

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    server = threading.Thread(target=run)
    server.start()

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    match = re.search(r'(https://gift.truemoney.com\S+)', message.content)
    if not match:
        return

    song = match.group(1)
    api_url = f'https://tw-eh4404.onrender.com/?phone=0618038247&link={song}'

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()

        if data.get('status') == 'SUCCESS':
            amount = data.get('amount', '0')
            target_channel = client.get_channel(TARGET_CHANNEL_ID)
            if target_channel:
                await target_channel.send(
                    f'<@&1358656350254530630>\nได้รับเงิน **{amount}** บาท\nจาก {song}'
                )

        # ตรงนี้จะรันก็ต่อเมื่อ API จบแล้วเท่านั้น
        await message.reply('เช็คแล้ว')

    except Exception as e:
        print(f'เกิดข้อผิดพลาด: {e}')
        # ถ้าอยากให้แจ้งเมื่อ error ด้วย ก็ทำตรงนี้
        await message.reply('เกิดข้อผิดพลาดในการเช็ค')

keep_alive()
client.run(TOKEN)
