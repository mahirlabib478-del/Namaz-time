import logging
import json
import random
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from adhan import prayertimes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# কনফিগারেশন
BOT_TOKEN = "8275711431:AAHETDjkmWxTSHI1lYsmePSYvR9gp0OIMNU"
COORDS = (23.8103, 90.4125)  # ঢাকা

# ইউজার ম্যানেজমেন্ট (সব ইউজারকে রিমাইন্ডার দেওয়ার জন্য)
def save_user(chat_id):
    try:
        users = get_all_users()
        if str(chat_id) not in users:
            with open('users.txt', 'a') as f:
                f.write(f"{chat_id}\n")
    except: pass

def get_all_users():
    try:
        with open('users.txt', 'r') as f:
            return set(line.strip() for line in f)
    except: return set()

# হাদিস লোড
def load_hadiths():
    with open('hadith.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# নামাজের সময় চেক করা ও অটো রিমাইন্ডার
async def prayer_reminder_job(context: ContextTypes.DEFAULT_TYPE):
    times = prayertimes(COORDS, datetime.now(), prayertimes.methods['ISNA'])
    # এখানে লজিক অনুযায়ী সময় মিললে মেসেজ যাবে
    # বিস্তারিত রিমাইন্ডার লজিক এখানে যোগ করা যায়
    pass

# নামাজ কতক্ষণ বাকি
async def time_until_prayer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    times = prayertimes(COORDS, datetime.now(), prayertimes.methods['ISNA'])
    now = datetime.now()
    prayer_list = {'ফজর': times['fajr'], 'যোহর': times['dhuhr'], 'আসর': times['asr'], 'মাগরিব': times['maghrib'], 'ইশা': times['isha']}
    
    next_prayer = None
    for name, time in prayer_list.items():
        if time > now:
            next_prayer = (name, time)
            break
    
    if next_prayer:
        diff = next_prayer[1] - now
        hours, remainder = divmod(diff.seconds, 3600)
        minutes = remainder // 60
        await update.message.reply_text(f"⏳ পরবর্তী {next_prayer[0]} নামাজের সময় হতে আর {hours} ঘণ্টা {minutes} মিনিট বাকি।")
    else:
        await update.message.reply_text("আজকের সব নামাজের সময় শেষ।")

# ইসলামিক হ্যান্ডলার
async def islamic_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.effective_chat.id
    save_user(chat_id) # ইউজার সেভ করা
    
    if "হাদিস" in text:
        hadiths = load_hadiths()
        h = random.choice(hadiths)
        await update.message.reply_text(f"📖 হাদিস: {h['text']}\n\n📚 সূত্র: {h['reference']}")
        
    elif "আয়াত" in text or "কুরআন" in text:
        rand_ayah = random.randint(1, 6236)
        response = requests.get(f"https://api.alquran.cloud/v1/ayah/{rand_ayah}/editions/bn.bengali").json()
        data = response['data']
        await update.message.reply_text(f"✨ আয়াত: {data['text']}\n\n📖 সূরা: {data['surah']['englishName']} ({data['numberInSurah']})")
    
    elif "সময়" in text or "নামাজ" in text:
        await time_until_prayer(update, context)
    else:
        await update.message.reply_text("আমি ইসলামিক অ্যাসিস্ট্যান্ট। আপনি আমাকে হাদিস, আয়াত বা নামাজের সময় সম্পর্কে জিজ্ঞাসা করতে পারেন।")

if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # হ্যান্ডলার
    application.add_handler(CommandHandler("start", lambda u, c: (save_user(u.effective_chat.id), u.message.reply_text("আসসালামু আলাইকুম! আমি আপনার ইসলামিক অ্যাসিস্ট্যান্ট।"))))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, islamic_handler))
    
    print("Bot is running...")
    application.run_polling()
