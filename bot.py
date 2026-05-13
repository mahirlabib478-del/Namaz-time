import logging
import json
import random
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from adhan import prayertimes

# কনফিগারেশন
BOT_TOKEN = "8275711431:AAHETDjkmWxTSHI1lYsmePSYvR9gp0OIMNU"
COORDS = (23.8103, 90.4125)  # ঢাকা

# হাদিস লোড করার ফাংশন
def load_hadiths():
    with open('hadith.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# ১. নামাজ কতক্ষণ বাকি তা বের করা
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

# ২. র‍্যান্ডম হাদিস বা আয়াত প্রদান
async def islamic_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if "হাদিস" in text:
        hadiths = load_hadiths()
        h = random.choice(hadiths)
        await update.message.reply_text(f"📖 হাদিস: {h['text']}\n\n📚 সূত্র: {h['reference']}")
        
    elif "আয়াত" in text or "কুরআন" in text:
        # র‍্যান্ডম আয়াত API থেকে
        rand_ayah = random.randint(1, 6236)
        response = requests.get(f"https://api.alquran.cloud/v1/ayah/{rand_ayah}/editions/bn.bengali").json()
        data = response['data']
        await update.message.reply_text(f"✨ আয়াত: {data['text']}\n\n📖 সূরা: {data['surah']['englishName']} ({data['numberInSurah']})")
    
    elif "সময়" in text or "নামাজ" in text:
        await time_until_prayer(update, context)

if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # কমান্ড হ্যান্ডলার
    application.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("আসসালামু আলাইকুম! আমি আপনার ইসলামিক অ্যাসিস্ট্যান্ট। আমাকে হাদিস, আয়াত বা নামাজের সময় সম্পর্কে জিজ্ঞাসা করুন।")))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, islamic_handler))
    
    print("Bot is running...")
    application.run_polling()
