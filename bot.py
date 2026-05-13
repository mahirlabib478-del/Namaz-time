import json
import random
import requests
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, 
    MessageHandler, filters, CallbackQueryHandler
)

BOT_TOKEN = "8275711431:AAHETDjkmWxTSHI1lYsmePSYvR9gp0OIMNU"

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# --- ইউজার ম্যানেজমেন্ট ---
def save_user(chat_id):
    users = get_all_users()
    if str(chat_id) not in users:
        with open("users.txt", "a") as f:
            f.write(f"{chat_id}\n")

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

# --- নামাজের নোটিফিকেশন ও ফলো-আপ ---
async def prayer_reminder_job(context: ContextTypes.DEFAULT_TYPE):
    timings = get_timings()
    now = datetime.now().strftime("%H:%M")
    prayer_names = {'Fajr': 'ফজর', 'Dhuhr': 'যোহর', 'Asr': 'আসর', 'Maghrib': 'মাগরিব', 'Isha': 'ইশা'}
    
    for p_en, p_bn in prayer_names.items():
        if timings[p_en] == now:
            users = get_all_users()
            keyboard = [[InlineKeyboardButton("হ্যাঁ, পড়েছি", callback_data=f"prayed_{p_bn}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            for chat_id in users:
                await context.bot.send_message(chat_id=chat_id, text=f"আসসালামু আলাইকুম! এখন {p_bn}-এর নামাজের সময়। 🕋", reply_markup=reply_markup)
            
            # ২০ মিনিট পর ফলো-আপ রিমাইন্ডার
            context.job_queue.run_once(follow_up_job, 1200, data=p_bn)

async def follow_up_job(context: ContextTypes.DEFAULT_TYPE):
    p_bn = context.job.data
    users = get_all_users()
    for chat_id in users:
        await context.bot.send_message(chat_id=chat_id, text=f"আপনি কি {p_bn}-এর নামাজ পড়েছেন? আলহামদুলিল্লাহ বলুন যদি পড়ে থাকেন।")

# --- বাটন হ্যান্ডলার ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("prayed_"):
        await query.edit_message_text(f"মাশাআল্লাহ! আল্লাহ আপনার নামাজ কবুল করুন।")

# --- অন্যান্য ফিচার ---
async def next_prayer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = get_timings()
    now = datetime.now()
    prayer_names = {'Fajr': 'ফজর', 'Dhuhr': 'যোহর', 'Asr': 'আসর', 'Maghrib': 'মাগরিব', 'Isha': 'ইশা'}
    
    sorted_prayers = sorted([(datetime.strptime(t[p_en], "%H:%M"), p_bn, t[p_en]) for p_en, p_bn in prayer_names.items()])
    
    next_p = next((p for p in sorted_prayers if p[0].time() > now.time()), sorted_prayers[0])
    diff = next_p[0] - now
    
    if diff.total_seconds() < 0: diff += timedelta(days=1)
    hours, remainder = divmod(int(diff.total_seconds()), 3600)
    minutes, _ = divmod(remainder, 60)
    
    await update.message.reply_text(f"🕌 পরবর্তী নামাজ: {next_p[1]} ({next_p[2]})\n⏳ বাকি আছে: {hours} ঘণ্টা {minutes} মিনিট।")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_chat.id)
    await update.message.reply_text("আসসালামু আলাইকুম! আমি আপনার ইসলামিক অ্যাসিস্ট্যান্ট।")

async def send_hadith(update: Update, context: ContextTypes.DEFAULT_TYPE):
    h = random.choice(load_hadiths())
    await update.message.reply_text(f"📖 হাদিস: {h['text']}\n\n📚 সূত্র: {h['reference']}")

async def send_quran(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        res = requests.get(f"https://api.alquran.cloud/v1/ayah/{random.randint(1, 6236)}/editions/bn.bengali").json()
        data = res["data"]
        await update.message.reply_text(f"✨ আয়াত: {data['text']}\n\n📖 সূরা: {data['surah']['englishName']}")
    except: await update.message.reply_text("আয়াত লোড করা যাচ্ছে না।")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_chat.id)
    text = update.message.text.lower()
    if "হাদিস" in text: await send_hadith(update, context)
    elif "আয়াত" in text: await send_quran(update, context)
    elif "সময়" in text or "বাকি" in text: await next_prayer(update, context)
    else: await update.message.reply_text("আমি আপনাকে নামাজের সময়, হাদিস বা কুরআন সম্পর্কে তথ্য দিতে পারি।")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.job_queue.run_repeating(prayer_reminder_job, interval=60, first=10)
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    print("Bot is running...")
    app.run_polling()
