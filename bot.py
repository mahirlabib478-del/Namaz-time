import logging
import json
import random
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from adhan import PrayerTimes
from adhan.methods import ISNA

# কনফিগারেশন
BOT_TOKEN = "8275711431:AAHETDjkmWxTSHI1lYsmePSYvR9gp0OIMNU"
COORDS = (23.8103, 90.4125)  # ঢাকা

# হাদিস লোড করার ফাংশন
def load_hadiths():
    try:
        with open('hadith.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return[{"text": "হাদিস ফাইলটি পাওয়া যাচ্ছে না।", "reference": "N/A"}]

# ফাংশন: হাদিস পাঠানো
async def send_hadith(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hadiths = load_hadiths()
    h = random.choice(hadiths)
    await update.message.reply_text(f"📖 হাদিস: {h['text']}\n\n📚 সূত্র: {h['reference']}")

# ফাংশন: আয়াত পাঠানো
async def send_quran(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rand_ayah = random.randint(1, 6236)
    try:
        response = requests.get(f"https://api.alquran.cloud/v1/ayah/{rand_ayah}/editions/bn.bengali").json()
        data = response['data']
        await update.message.reply_text(f"✨ আয়াত: {data['text']}\n\n📖 সূরা: {data['surah']['englishName']} ({data['numberInSurah']})")
    except:
        await update.message.reply_text("দুঃখিত, বর্তমানে আয়াত লোড করা যাচ্ছে না।")


# নামাজের সময় পাওয়ার ফাংশন (আপডেট করা)
async def time_until_prayer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # কোঅর্ডিনেটস এবং মেথড সেটআপ
    coords = (23.8103, 90.4125)
    params = ISNA
    
    # PrayerTimes ক্লাস ব্যবহার করে সময় বের করা
    times = PrayerTimes(coords, datetime.now(), params)
    now = datetime.now()
    
    # নতুন লাইব্রেরিতে সময়গুলো ডট (.) দিয়ে অ্যাক্সেস করতে হয়
    prayer_list = {
        'ফজর': times.fajr, 
        'যোহর': times.dhuhr, 
        'আসর': times.asr, 
        'মাগরিব': times.maghrib, 
        'ইশা': times.isha
    }
    
    next_prayer = None
    for name, time in prayer_list.items():
        # time এখানে datetime অবজেক্ট, তাই সরাসরি তুলনা করা যাবে
        if time > now:
            next_prayer = (name, time)
            break
    
    if next_prayer:
        diff = next_prayer[1] - now
        # diff.total_seconds() ব্যবহার করা বেশি নিরাপদ
        total_seconds = int(diff.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        
        await update.message.reply_text(f"⏳ পরবর্তী {next_prayer[0]} নামাজের সময় হতে আর {hours} ঘণ্টা {minutes} মিনিট বাকি।")
    else:
        await update.message.reply_text("আজকের সব নামাজের সময় শেষ।")

# মেইন হ্যান্ডলার: যা টেক্সট মেসেজ চেক করবে
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    
    if "হাদিস" in text:
        await send_hadith(update, context)
    elif "আয়াত" in text or "কুরআন" in text:
        await send_quran(update, context)
    elif "সময়" in text or "নামাজ" in text:
        await time_until_prayer(update, context)
    else:
        await update.message.reply_text("আমি ইসলামিক অ্যাসিস্ট্যান্ট! আপনি আমাকে কমান্ড দিতে পারেন বা হাদিস, আয়াত বা নামাজের সময় সম্পর্কে লিখতে পারেন।")

if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # কমান্ড হ্যান্ডলার (Command /)
    application.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("আসসালামু আলাইকুম! আমি আপনার ইসলামিক অ্যাসিস্ট্যান্ট।\nকমান্ড: /hadith, /quran, /time")))
    application.add_handler(CommandHandler("hadith", send_hadith))
    application.add_handler(CommandHandler("quran", send_quran))
    application.add_handler(CommandHandler("time", time_until_prayer))
    
    # মেসেজ হ্যান্ডলার (Text Message)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    print("Bot is running...")
    application.run_polling()
