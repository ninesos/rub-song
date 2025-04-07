import discord
import re
import requests
import asyncio
import os
import threading
from flask import Flask

TOKEN = os.getenv('TOKEN')

TARGET_CHANNEL_ID = 1358457724941373480

app = Flask('')

@app.route('/')
def home():
    return "ยังออนไลน์อยู่จ้าาาา"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'ล็อกอินเป็น {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    match = re.search(r'(https://gift.truemoney.com\S+)', message.content)
    if match:
        song = match.group(1)

        api_url = f'https://tw-eh4404.onrender.com/?phone=0618038247&link={song}'
        try:
            response = requests.get(api_url)
            data = response.json()

            if data.get('status') == 'SUCCESS':
                amount = data.get('amount', '0')
                
                target_channel = client.get_channel(TARGET_CHANNEL_ID)
                if target_channel:
                    await target_channel.send(f'<@&1358656350254530630>\nได้รับเงิน **{amount}** บาท\nจาก {song}')
                else:
                    print('ไม่พบช่องที่กำหนด')

        except Exception as e:
            print(f'เกิดข้อผิดพลาด: {e}')

        await message.reply('เช็คแล้ว')
        
keep_alive()
client.run(TOKEN)