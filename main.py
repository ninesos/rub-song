import discord
import re
import requests
import asyncio
import os
from flask import Flask
import threading

TOKEN = os.getenv('TOKEN')
TARGET_CHANNEL_ID = 1358457724941373480
ROLE_ID = 1358656350254530630

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# สร้าง Flask server สำหรับ keep-alive
app = Flask('')
@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    threading.Thread(target=run, daemon=True).start()

# สร้าง Lock เพื่อ serialize API calls
api_lock = asyncio.Lock()

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # หา link ที่ขึ้นต้นด้วย https://gift.truemoney.com
    match = re.search(r'(https://gift\.truemoney\.com\S+)', message.content)
    if not match:
        return

    song = match.group(1)
    api_url = f'https://tw-eh4404.onrender.com/?phone=0618038247&link={song}'

    # รอ lock ก่อนจะยิง API
    async with api_lock:
        try:
            # รัน requests.get ใน thread pool ไม่บล็อก event loop
            response = await asyncio.to_thread(requests.get, api_url)
            data = response.json()

            if data.get('status') == 'SUCCESS':
                amount = data.get('amount', '0')
                target_channel = client.get_channel(TARGET_CHANNEL_ID)
                if target_channel:
                    await target_channel.send(
                        f'<@&{ROLE_ID}>\n'
                        f'ได้รับเงิน **{amount}** บาท\n'
                        f'จาก {song}'
                    )
        except Exception as e:
            print(f'เกิดข้อผิดพลาด: {e}')

        # ตอบกลับใต้ข้อความต้นทางว่าเช็คแล้ว
        await message.reply('เช็คแล้ว')

# เรียก keep-alive แล้วค่อย run บอท
keep_alive()
client.run(TOKEN)
