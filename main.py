import discord
from discord.ext import commands
import re
import requests
import json
import time
import threading
import os
from flask import Flask
from threading import Thread

# Flask app for keep-alive
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True  # Set the thread as daemon so it exits when the main program exits
    t.start()

# Discord bot configuration
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# ===== คอนฟิกของบอท (แก้ไขตรงนี้) =====
DISCORD_TOKEN = os.getenv('TOKEN')  # โทเคนของบอทดิสคอร์ด
NOTIFICATION_CHANNEL_ID = 1358457724941373480  # ใส่ ID ของช่องที่ต้องการให้แจ้งเตือน
MENTION_ROLE_ID = 1358656350254530630  # ID ของบทบาทที่จะถูกแท็ก (@mention)
PHONE_NUMBER = "0618038247"  # เบอร์โทรศัพท์ที่จะรับเงิน
# =====================================

# ตัวแปรสำหรับเก็บช่องแจ้งเตือนปัจจุบัน
current_notification_channel_id = NOTIFICATION_CHANNEL_ID

@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')

@bot.command()
@commands.has_permissions(administrator=True)
async def set_channel(ctx, channel_id: int):
    """ตั้งค่าช่องแจ้งเตือน"""
    global current_notification_channel_id
    current_notification_channel_id = channel_id
    
    await ctx.send(f'ตั้งค่าช่องแจ้งเตือนเป็น <#{channel_id}> เรียบร้อยแล้ว')

@bot.event
async def on_message(message):
    # ประมวลผลคำสั่งก่อน
    await bot.process_commands(message)
    
    # ข้ามข้อความจากบอทเอง
    if message.author == bot.user:
        return
    
    # ตรวจสอบว่าข้อความมีลิงก์ TrueMoney Gift หรือไม่
    if "https://gift.truemoney.com" in message.content:
        # ดึงลิงก์ TrueMoney Gift
        pattern = r'(https://gift\.truemoney\.com[^\s]+)'
        match = re.search(pattern, message.content)
        
        if match:
            song = match.group(1)
            print(f"พบลิงก์ TrueMoney Gift: {song}")
            
            # ประมวลผลลิงก์
            result = await process_truemoney_link(song)
            
            # ช่องที่จะตอบกลับ (ช่องเดียวกับที่มีการส่งลิงก์)
            channel = message.channel
            
            if result:
                status = result.get('status', '')
                
                if status == 'SUCCESS':
                    amount = result.get('amount', '0.00')
                    await channel.reply('เช็คแล้ว')
                    
                    # ส่งการแจ้งเตือนไปยังช่องที่กำหนด
                    if current_notification_channel_id != 0:
                        notification_channel = bot.get_channel(current_notification_channel_id)
                        if notification_channel:
                            notification_message = f'<@&{MENTION_ROLE_ID}>\nได้รับเงิน **{amount}** บาท\nจาก {song}'
                            await notification_channel.send(notification_message)
                        else:
                            print(f"ไม่พบช่องแจ้งเตือนที่มีไอดี {current_notification_channel_id}")
                else:
                    # ถ้าสถานะเป็น FAIL ให้ตอบกลับด้วยข้อความตรวจสอบเท่านั้น
                    await channel.reply('เช็คแล้ว')
            else:
                await channel.send('เช็คแล้ว')

async def process_truemoney_link(link):
    api_url = f"https://tw-eh4404.onrender.com/?phone={PHONE_NUMBER}&link={link}"
    
    max_attempts = 5
    attempt = 0
    
    while attempt < max_attempts:
        try:
            response = requests.get(api_url)
            
            # ตรวจสอบว่าการตอบกลับเป็น JSON ที่ถูกต้องหรือไม่
            try:
                result = response.json()
                
                # ตรวจสอบว่าผลลัพธ์มีสถานะหรือไม่
                if 'status' in result:
                    if result['status'] == 'SUCCESS' or result['status'] == 'FAIL':
                        return result
            except json.JSONDecodeError:
                # การตอบกลับไม่ใช่ JSON ลองอีกครั้ง
                pass
            
            # รอสักครู่ก่อนลองอีกครั้ง
            time.sleep(2)
            attempt += 1
            
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการประมวลผลลิงก์ TrueMoney: {e}")
            attempt += 1
            time.sleep(2)
    
    return None

# เริ่มระบบ keep alive
keep_alive()

# เริ่มต้นบอท
bot.run(DISCORD_TOKEN)
