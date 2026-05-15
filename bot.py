import os
import json
import random
import logging
import requests
from flask import Flask
from threading import Thread
import os

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

BOT_TOKEN = "8275711431:AAEbB_fVHqqXcGkMlzwy4snT5sJWpYRzITc"
ADMIN_ID = 8538304896

TIMEZONE = ZoneInfo("Asia/Dhaka")
# =========================
# FLASK SERVER
# =========================

flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "Salat Reminder Bot Running!"


def run_web():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)
    
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

PRAYER_FILE = "prayer_times.json"


def get_timings():
    try:
        with open(PRAYER_FILE, "r") as f:
            return json.load(f)

    except Exception as e:
        logging.error(e)

        return {
            "Fajr": "04:15",
            "Dhuhr": "12:00",
            "Asr": "15:30",
            "Maghrib": "18:30",
            "Isha": "19:45"
        }


def save_timings(data):
    with open(PRAYER_FILE, "w") as f:
        json.dump(data, f, indent=4)

# =========================
# HADITH LOADER
# =========================

def load_hadiths():
    try:
        with open("hadith.json", "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception as e:
        logging.error(f"Error loading hadiths: {e}")
        return[
            {
                "text": "হাদিস লোড করা যায়নি।",
                "explanation": "ডেটাবেস ফাইলটি খুঁজে পাওয়া যাচ্ছে না অথবা ফাইল ফরম্যাটে সমস্যা আছে।",
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
        # আয়াত নম্বর
        ayah_number = data["numberInSurah"]

        await update.message.reply_text(
            f"📖 {text}\n\n"
            f"🕌 সূরা: {surah}\n"
            f"🔢 আয়াত: {ayah_number}" 
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

    # এখন 'explanation' ফিল্ডটি যোগ করা হয়েছে
    await update.message.reply_text(
        f"📚 **হাদিস**\n\n"
        f"{h['text']}\n\n"
        f"💡 **ব্যাখ্যা:**\n{h.get('explanation', 'কোনো ব্যাখ্যা নেই।')}\n\n"
        f"📖 **সূত্র:** {h['reference']}",
        parse_mode='Markdown'
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

last_sent = {}

async def prayer_reminder_job(context: ContextTypes.DEFAULT_TYPE):

    timings = get_timings()

    if not timings:
        return

    now = datetime.now(TIMEZONE)

    current_time = now.strftime("%H:%M")

    prayers = {
        "Fajr": "ফজর",
        "Dhuhr": "যোহর",
        "Asr": "আসর",
        "Maghrib": "মাগরিব",
        "Isha": "ইশা"
    }

    today = now.strftime("%Y-%m-%d")

    for eng, bn in prayers.items():

        prayer_time = timings.get(eng)

        print("Current Time:", current_time)
        print("Prayer Time:", prayer_time)
    

        # একই দিনে একবারের বেশি send করবে না
        unique_key = f"{today}_{eng}"

        if prayer_time == current_time:

            if last_sent.get(unique_key):
                continue

            last_sent[unique_key] = True

            users = get_all_users()

            for chat_id in users:
                try:
                    await context.bot.send_message(
                        chat_id=int(chat_id),
                        text=(
                            f"🕌 এখন {bn} নামাজের সময় হয়েছে\n\n"
                            f"আল্লাহর দিকে ফিরে আসুন 🤍"
                        )
                    )

                except Exception as e:
                    logging.error(e)

            # 60 মিনিট পরে follow up
            context.job_queue.run_once(
                follow_up_job,
                when=3600,
                data=bn
            )


# =========================
# FOLLOW UP
# =========================

async def follow_up_job(context: ContextTypes.DEFAULT_TYPE):

    prayer_name = context.job.data

    users = get_all_users()

    # বাটন এখানে
    keyboard = [
        [
            InlineKeyboardButton(
                "হ্যাঁ, পড়েছি 🤍",
                callback_data=f"done_{prayer_name}"
            ),
            InlineKeyboardButton(
                "না, পড়া হয় নি 🥺",
                callback_data=f"not_done_{prayer_name}"
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    for chat_id in users:
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    f"🤍 আপনি কি {prayer_name} "
                    f"নামাজ আদায় করেছেন?"
                ),
                reply_markup=reply_markup
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
  # নামাজ পড়ে নি
    
    elif query.data.startswith("not_done_"):

        prayer_name = query.data.replace("not_done_", "")

        await query.edit_message_text(
            f"🤍 সমস্যা নেই।\n\n"
            f"দয়া করে যত দ্রুত সম্ভব {prayer_name} "
            f"নামাজ আদায় করে নিন।"
        )      

# =========================
# SET PRAYER TIME
# =========================

async def set_prayer(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text(
            "আপনি Admin না।"
        )
        return

    if len(context.args) != 1:

        await update.message.reply_text(
            "Usage:\n"
            "/setfajr 04:20"
        )
        return

    prayer_time = context.args[0]

    timings = get_timings()

    command = update.message.text.split()[0]

    prayer_map = {
        "/setfajr": "Fajr",
        "/setdhuhr": "Dhuhr",
        "/setasr": "Asr",
        "/setmaghrib": "Maghrib",
        "/setisha": "Isha"
    }

    prayer_name = prayer_map.get(command)

    if not prayer_name:
        return

    timings[prayer_name] = prayer_time

    save_timings(timings)

    await update.message.reply_text(
        f"✅ {prayer_name} এর সময় সেট হয়েছে {prayer_time}"
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
    
    Thread(target=run_web).start()
    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hadith", send_hadith))
    app.add_handler(CommandHandler("ayah", send_quran))
    app.add_handler(CommandHandler("time", prayer_times))
    app.add_handler(CommandHandler("next", next_prayer))

    app.add_handler(CommandHandler("setfajr", set_prayer))
    app.add_handler(CommandHandler("setdhuhr", set_prayer))
    app.add_handler(CommandHandler("setasr", set_prayer))
    app.add_handler(CommandHandler("setmaghrib", set_prayer))
    app.add_handler(CommandHandler("setisha", set_prayer))

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
        interval=30,
        first=5
    )

    print("Bot running...")

    app.run_polling()
