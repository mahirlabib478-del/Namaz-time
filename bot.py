import os
import json
import random
import logging
import requests

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

# =========================
# CONFIG
# =========================

BOT_TOKEN=8275711431:AAGcsGnUqgEo9AAHTtht_68eky-6313DBOE

TIMEZONE = ZoneInfo("Asia/Dhaka")

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# =========================
# USER STORAGE
# =========================

USERS_FILE = "users.txt"


def get_all_users():
    try:
        with open(USERS_FILE, "r") as f:
            return set(line.strip() for line in f)
    except:
        return set()


def save_user(chat_id):
    users = get_all_users()

    if str(chat_id) not in users:
        with open(USERS_FILE, "a") as f:
            f.write(f"{chat_id}\n")


# =========================
# PRAYER API
# =========================

def get_timings():
    try:
        url = (
            "https://api.aladhan.com/v1/timingsByCity"
            "?city=Dhaka&country=Bangladesh&method=2"
        )

        response = requests.get(url, timeout=10)

        data = response.json()

        return data["data"]["timings"]

    except Exception as e:
        logging.error(f"Prayer API Error: {e}")

        return None


# =========================
# HADITH LOADER
# =========================

def load_hadiths():
    try:
        with open("hadith.json", "r", encoding="utf-8") as f:
            return json.load(f)

    except:
        return [
            {
                "text": "হাদিস লোড করা যায়নি।",
                "reference": "N/A"
            }
        ]


# =========================
# QURAN AYAH
# =========================

async def send_quran(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        ayah_no = random.randint(1, 6236)

        url = (
            f"https://api.alquran.cloud/v1/ayah/"
            f"{ayah_no}/editions/bn.bengali"
        )

        response = requests.get(url, timeout=10)

        data = response.json()["data"][0]

        text = data["text"]
        surah = data["surah"]["englishName"]

        await update.message.reply_text(
            f"📖 {text}\n\n"
            f"🕌 সূরা: {surah}"
        )

    except Exception as e:
        logging.error(e)

        await update.message.reply_text(
            "আয়াত লোড করা যাচ্ছে না।"
        )


# =========================
# HADITH
# =========================

async def send_hadith(update: Update, context: ContextTypes.DEFAULT_TYPE):
    hadiths = load_hadiths()

    h = random.choice(hadiths)

    await update.message.reply_text(
        f"📚 হাদিস\n\n"
        f"{h['text']}\n\n"
        f"📖 সূত্র: {h['reference']}"
    )


# =========================
# PRAYER TIMES
# =========================

async def prayer_times(update: Update, context: ContextTypes.DEFAULT_TYPE):
    timings = get_timings()

    if not timings:
        await update.message.reply_text(
            "নামাজের সময় লোড করা যাচ্ছে না।"
        )
        return

    msg = (
        "🕌 আজকের নামাজের সময়সূচী\n\n"
        f"🌅 ফজর: {timings['Fajr']}\n"
        f"☀️ যোহর: {timings['Dhuhr']}\n"
        f"🌇 আসর: {timings['Asr']}\n"
        f"🌙 মাগরিব: {timings['Maghrib']}\n"
        f"🌌 ইশা: {timings['Isha']}"
    )

    await update.message.reply_text(msg)


# =========================
# NEXT PRAYER
# =========================

async def next_prayer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    timings = get_timings()

    if not timings:
        await update.message.reply_text(
            "নামাজের সময় পাওয়া যাচ্ছে না।"
        )
        return

    now = datetime.now(TIMEZONE)

    prayers = {
        "Fajr": "ফজর",
        "Dhuhr": "যোহর",
        "Asr": "আসর",
        "Maghrib": "মাগরিব",
        "Isha": "ইশা"
    }

    prayer_list = []

    for eng, bn in prayers.items():

        prayer_time = datetime.strptime(
            timings[eng],
            "%H:%M"
        ).replace(
            year=now.year,
            month=now.month,
            day=now.day,
            tzinfo=TIMEZONE
        )

        prayer_list.append((prayer_time, bn, timings[eng]))

    next_prayer_data = None

    for prayer_time, bn, time_str in prayer_list:
        if prayer_time > now:
            next_prayer_data = (
                prayer_time,
                bn,
                time_str
            )
            break

    # If all prayers passed
    if not next_prayer_data:

        fajr_time = prayer_list[0][0] + timedelta(days=1)

        next_prayer_data = (
            fajr_time,
            prayer_list[0][1],
            prayer_list[0][2]
        )

    diff = next_prayer_data[0] - now

    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60

    await update.message.reply_text(
        f"🕌 পরবর্তী নামাজ: "
        f"{next_prayer_data[1]}\n"
        f"⏰ সময়: {next_prayer_data[2]}\n\n"
        f"⌛ বাকি আছে:\n"
        f"{hours} ঘণ্টা {minutes} মিনিট"
    )


# =========================
# REMINDER JOB
# =========================

async def prayer_reminder_job(context: ContextTypes.DEFAULT_TYPE):

    timings = get_timings()

    if not timings:
        return

    now = datetime.now(TIMEZONE).strftime("%H:%M")

    prayers = {
        "Fajr": "ফজর",
        "Dhuhr": "যোহর",
        "Asr": "আসর",
        "Maghrib": "মাগরিব",
        "Isha": "ইশা"
    }

    for eng, bn in prayers.items():

        if timings[eng] == now:

            users = get_all_users()

            keyboard = [
                [
                    InlineKeyboardButton(
                        "হ্যাঁ, পড়েছি 🤍",
                        callback_data=f"done_{bn}"
                    )
                ]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            for chat_id in users:
                try:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=(
                            f"🕌 এখন {bn} নামাজের সময় হয়েছে।\n"
                            f"আল্লাহর দিকে ফিরে আসুন 🤍"
                        ),
                        reply_markup=reply_markup
                    )

                except Exception as e:
                    logging.error(e)

            # follow-up after 20 mins
            context.job_queue.run_once(
                follow_up_job,
                when=1200,
                data=bn
            )


# =========================
# FOLLOW UP
# =========================

async def follow_up_job(context: ContextTypes.DEFAULT_TYPE):

    prayer_name = context.job.data

    users = get_all_users()

    for chat_id in users:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    f"🤍 আপনি কি {prayer_name} "
                    f"নামাজ আদায় করেছেন?"
                )
            )

        except Exception as e:
            logging.error(e)


# =========================
# BUTTON HANDLER
# =========================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    if query.data.startswith("done_"):

        await query.edit_message_text(
            "মাশাআল্লাহ 🤍\n"
            "আল্লাহ আপনার নামাজ কবুল করুন।"
        )


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    save_user(update.effective_chat.id)

    msg = (
        "🕌 আসসালামু আলাইকুম\n\n"
        "আমি আপনার ইসলামিক অ্যাসিস্ট্যান্ট বট।\n\n"
        "📌 কমান্ডসমূহ:\n"
        "/hadith - হাদিস\n"
        "/ayah - কুরআনের আয়াত\n"
        "/time - নামাজের সময়\n"
        "/next - পরবর্তী নামাজ"
    )

    await update.message.reply_text(msg)


# =========================
# TEXT HANDLER
# =========================

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    save_user(update.effective_chat.id)

    text = update.message.text.lower()

    if "হাদিস" in text:
        await send_hadith(update, context)

    elif "আয়াত" in text or "কুরআন" in text:
        await send_quran(update, context)

    elif "সময়" in text:
        await prayer_times(update, context)

    elif "বাকি" in text or "পরের নামাজ" in text:
        await next_prayer(update, context)

    else:
        await update.message.reply_text(
            "আমি আপনাকে নামাজের সময়, "
            "হাদিস ও কুরআনের আয়াত দিতে পারি।"
        )


# =========================
# MAIN
# =========================

if __name__ == "__main__":

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hadith", send_hadith))
    app.add_handler(CommandHandler("ayah", send_quran))
    app.add_handler(CommandHandler("time", prayer_times))
    app.add_handler(CommandHandler("next", next_prayer))

    # Buttons
    app.add_handler(CallbackQueryHandler(button_handler))

    # Text
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_handler
        )
    )

    # Prayer checker every minute
    app.job_queue.run_repeating(
        prayer_reminder_job,
        interval=60,
        first=10
    )

    print("Bot running...")

    app.run_polling()
