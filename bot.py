import json
import random
import requests
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

BOT_TOKEN = "8275711431:AAHETDjkmWxTSHI1lYsmePSYvR9gp0OIMNU"

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# গ্লোবাল অ্যাপ ভেরিয়েবল
app = None

# ইউজার ম্যানেজমেন্ট
def save_user(chat_id):
    try:
        users = get_all_users()
        if str(chat_id) not in users:
            with open("users.txt", "a") as f:
                f.write(f"{chat_id}\n")
    except: pass

def get_all_users():
    try:
        with open("users.txt", "r") as f:
            return set(line.strip() for line in f)
    except: return set()

def get_timings():
    url = "https://api.aladhan.com/v1/timingsByCity?city=Dhaka&country=Bangladesh&method=2"
    return requests.get(url).json()["data"]["timings"]

def load_hadiths():
    try:
        with open("hadith.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except: return[{"text": "হাদিস লোড করা সম্ভব হয়নি।", "reference": "N/A"}]

# অটোমেটিক রিমাইন্ডার ফাংশন
async def prayer_reminder_job():
    try:
        timings = get_timings()
        now = datetime.now().strftime("%H:%M")
        prayer_names = {'Fajr': 'ফজর', 'Dhuhr': 'যোহর', 'Asr': 'আসর', 'Maghrib': 'মাগরিব', 'Isha': 'ইশা'}
        
        for p_en, p_bn in prayer_names.items():
            if timings[p_en] == now:
                users = get_all_users()
                for chat_id in users:
                    try:
                        await app.bot.send_message(chat_id=chat_id, text=f"আসসালামু আলাইকুম! এখন {p_bn}-এর নামাজের সময়। 🕋")
                    except: pass
    except: pass

# কমান্ড ও মেসেজ হ্যান্ডলার
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_chat.id)
    await update.message.reply_text("আসসালামু আলাইকুম! আমি আপনার ইসলামিক অ্যাসিস্ট্যান্ট। আমি আপনাকে নিয়মিত নামাজের রিমাইন্ডার দেব।")

async def send_hadith(update: Update, context: ContextTypes.DEFAULT_TYPE):
    h = random.choice(load_hadiths())
    await update.message.reply_text(f"📖 হাদিস: {h['text']}\n\n📚 সূত্র: {h['reference']}")

async def send_quran(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        res = requests.get(f"https://api.alquran.cloud/v1/ayah/{random.randint(1, 6236)}/editions/bn.bengali").json()
        data = res["data"]
        await update.message.reply_text(f"✨ আয়াত: {data['text']}\n\n📖 সূরা: {data['surah']['englishName']} ({data['numberInSurah']})")
    except: await update.message.reply_text("আয়াত লোড করা যাচ্ছে না।")

async def prayer_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = get_timings()
    await update.message.reply_text(f"🕌 আজকের সময়সূচী:\nফজর: {t['Fajr']}\nযোহর: {t['Dhuhr']}\nআসর: {t['Asr']}\nমাগরিব: {t['Maghrib']}\nইশা: {t['Isha']}")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_chat.id)
    text = update.message.text.lower()
    if "হাদিস" in text: await send_hadith(update, context)
    elif "আয়াত" in text or "কুরআন" in text: await send_quran(update, context)
    elif "নামাজ" in text or "সময়" in text: await prayer_time(update, context)
    else: await update.message.reply_text("আমি ইসলামিক অ্যাসিস্ট্যান্ট! হাদিস, আয়াত বা নামাজের সময় জানতে লিখুন।")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # শিডিউলার যোগ করা
    scheduler = AsyncIOScheduler()
    scheduler.add_job(prayer_reminder_job, 'interval', minutes=1)
    scheduler.start()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hadith", send_hadith))
    app.add_handler(CommandHandler("quran", send_quran))
    app.add_handler(CommandHandler("time", prayer_time))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("Bot is running...")
    app.run_polling()
