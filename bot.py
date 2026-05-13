import json
import random
import requests
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

# =========================
# CONFIG
# =========================

BOT_TOKEN = "8275711431:AAHETDjkmWxTSHI1lYsmePSYvR9gp0OIMNU"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# =========================
# LOAD HADITH
# =========================

def load_hadiths():
    try:
        with open("hadith.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return [
            {
                "text": "হাদিস ফাইল পাওয়া যায়নি।",
                "reference": "N/A"
            }
        ]

# =========================
# START COMMAND
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = (
        "🌸 আসসালামু আলাইকুম 🌸\n\n"
        "আমি আপনার ইসলামিক অ্যাসিস্ট্যান্ট 🤖\n\n"
        "📌 কমান্ডসমূহ:\n"
        "/hadith - হাদিস\n"
        "/quran - কুরআনের আয়াত\n"
        "/time - নামাজের সময়"
    )

    await update.message.reply_text(text)

# =========================
# HADITH
# =========================

async def send_hadith(update: Update, context: ContextTypes.DEFAULT_TYPE):

    hadiths = load_hadiths()

    h = random.choice(hadiths)

    msg = (
        f"📖 হাদিস:\n\n"
        f"{h['text']}\n\n"
        f"📚 সূত্র: {h['reference']}"
    )

    await update.message.reply_text(msg)

# =========================
# QURAN AYAH
# =========================

async def send_quran(update: Update, context: ContextTypes.DEFAULT_TYPE):

    rand_ayah = random.randint(1, 6236)

    try:

        response = requests.get(
            f"https://api.alquran.cloud/v1/ayah/{rand_ayah}/bn.bengali"
        ).json()

        data = response["data"]

        text = data["text"]
        surah = data["surah"]["englishName"]
        number = data["numberInSurah"]

        msg = (
            f"✨ কুরআনের আয়াত:\n\n"
            f"{text}\n\n"
            f"📖 সূরা: {surah}\n"
            f"🔢 আয়াত নম্বর: {number}"
        )

        await update.message.reply_text(msg)

    except Exception as e:

        print(e)

        await update.message.reply_text(
            "দুঃখিত, আয়াত লোড করা যাচ্ছে না।"
        )

# =========================
# PRAYER TIME
# =========================

async def prayer_time(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        url = (
            "https://api.aladhan.com/v1/timingsByCity"
            "?city=Dhaka"
            "&country=Bangladesh"
            "&method=2"
        )

        response = requests.get(url).json()

        timings = response["data"]["timings"]

        msg = (
            "🕌 আজকের নামাজের সময়\n\n"
            f"🌅 ফজর: {timings['Fajr']}\n"
            f"☀️ যোহর: {timings['Dhuhr']}\n"
            f"🌇 আসর: {timings['Asr']}\n"
            f"🌆 মাগরিব: {timings['Maghrib']}\n"
            f"🌙 ইশা: {timings['Isha']}"
        )

        await update.message.reply_text(msg)

    except Exception as e:

        print(e)

        await update.message.reply_text(
            "নামাজের সময় আনা যাচ্ছে না।"
        )

# =========================
# TEXT MESSAGE HANDLER
# =========================

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.lower()

    if "হাদিস" in text:
        await send_hadith(update, context)

    elif "আয়াত" in text or "কুরআন" in text:
        await send_quran(update, context)

    elif "নামাজ" in text or "সময়" in text:
        await prayer_time(update, context)

    else:

        await update.message.reply_text(
            "আমি ইসলামিক অ্যাসিস্ট্যান্ট 🤖\n\n"
            "আপনি লিখতে পারেন:\n"
            "• হাদিস\n"
            "• আয়াত\n"
            "• নামাজের সময়"
        )

# =========================
# MAIN
# =========================

if __name__ == "__main__":

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # COMMANDS
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hadith", send_hadith))
    app.add_handler(CommandHandler("quran", send_quran))
    app.add_handler(CommandHandler("time", prayer_time))

    # TEXT MESSAGE
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_handler
        )
    )

    print("Bot is running...")

    app.run_polling()
