import telebot
import requests
import time

# ================= CONFIGURATION =================
# 1. Get a new token from @BotFather on Telegram
# 2. Paste it below inside the quotes
BOT_TOKEN = "8216359066:AAEt2GFGgTBp3hh_znnJagH3h1nN5A_XQf0" 

ADMIN_ID = 7210704553
SERVER_URL = "https://ggggggggggggggggggg.onrender.com"  # Your Render URL
ADMIN_SECRET = "super_secret_admin_key_123"            # Must match app.py
# =================================================

bot = telebot.TeleBot(BOT_TOKEN)

try:
    bot.remove_webhook()
    time.sleep(1) 
    print("Cleaned up webhooks...")
except:
    pass

print("Bot is starting... (Press Ctrl+C to stop)")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    print(f"DEBUG: Msg from {message.from_user.id}")
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, f"❌ Unauthorized ID: {message.from_user.id}")
        return
    bot.reply_to(message, "🔋 **Admin Bot Online**\nUse: /gen 30 1")

@bot.message_handler(commands=['gen'])
def generate(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        parts = message.text.split()
        days = int(parts[1]) if len(parts)>1 else 30
        count = int(parts[2]) if len(parts)>2 else 1
        
        bot.reply_to(message, "⚙️ Requesting server...")
        resp = requests.post(
            f"{SERVER_URL}/admin/generate",
            json={"days": days, "count": count},
            headers={"X-Admin-Secret": ADMIN_SECRET}
        )
        if resp.status_code == 200:
            keys = resp.json().get("keys", [])
            bot.reply_to(message, f"✅ Keys:\n`{'`\n`'.join(keys)}`", parse_mode="Markdown")
        else:
            bot.reply_to(message, f"❌ Server Error: {resp.text}")
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

bot.infinity_polling()
