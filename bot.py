import re
import io
import requests
import telebot
from telebot import types

# ==== CONFIG ====
BOT_TOKEN = "8262615033:AAHka9Tau6ngQqeBZOmv5squaq5KsW2Plgg"  # <-- এখানে তোমার Telegram Bot Token বসাও

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ==== USER STATES ====
expecting_url = {}
had_first_download = {}

# ==== KEYBOARDS ====
def main_menu_kb():
    kb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    kb.add("Download YT Thumbnail")
    return kb

def after_first_kb():
    kb = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    kb.add("Download another thumbnail")
    return kb

def hide_keyboard():
    return types.ReplyKeyboardRemove()

# ==== HELPERS ====
YOUTUBE_REGEX = re.compile(
    r"""(?:https?://)?(?:www\.)?(?:m\.)?
        (?:
            (?:youtube\.com/(?:watch\?v=|embed/|v/|shorts/|.*[?&]v=))
            |(?:youtu\.be/)
        )
        (?P<id>[-_0-9A-Za-z]{11})
    """,
    re.VERBOSE,
)

def extract_video_id(url: str):
    match = YOUTUBE_REGEX.search(url)
    if match:
        return match.group("id")
    if re.fullmatch(r"[-_0-9A-Za-z]{11}", url.strip()):
        return url.strip()
    return None

def fetch_hd_thumbnail(video_id: str):
    url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200 and r.headers.get("Content-Type", "").startswith("image"):
            return r.content, f"{video_id}_maxres.jpg"
    except:
        pass
    return None, None

def ask_for_url(chat_id: int):
    expecting_url[chat_id] = True

# ==== HANDLERS ====
@bot.message_handler(commands=["start", "help"])
def cmd_start(message):
    chat_id = message.chat.id
    expecting_url.pop(chat_id, None)
    had_first_download.pop(chat_id, None)
    text = (
        "👋 Welcome!\n\n"
        "I am a YouTube Thumbnail Downloader Bot.\n\n"
        "📌 How to use:\n"
        "1️⃣ Click <b>Download YT Thumbnail</b>\n"
        "2️⃣ Send a YouTube video URL\n"
        "3️⃣ I will send you the HD thumbnail."
    )
    bot.send_message(chat_id, text, reply_markup=main_menu_kb())

@bot.message_handler(func=lambda m: m.text == "Download YT Thumbnail")
def handle_main_menu(message):
    chat_id = message.chat.id
    ask_for_url(chat_id)
    bot.send_message(chat_id, "Enter your YouTube video url please..", reply_markup=hide_keyboard())

@bot.message_handler(func=lambda m: m.text == "Download another thumbnail")
def handle_download_another(message):
    chat_id = message.chat.id
    ask_for_url(chat_id)
    bot.send_message(chat_id, "Enter your YouTube video url please..", reply_markup=hide_keyboard())

@bot.message_handler(func=lambda m: True, content_types=["text"])
def catch_all_text(message):
    chat_id = message.chat.id
    text = (message.text or "").strip()

    if expecting_url.get(chat_id):
        expecting_url[chat_id] = False
        video_id = extract_video_id(text)

        if not video_id:
            bot.send_message(chat_id, "❗ Invalid URL. Please try again.", 
                             reply_markup=(after_first_kb() if had_first_download.get(chat_id) else main_menu_kb()))
            return

        search_msg = bot.send_message(chat_id, "🔎 Searching thumbnail...")

        data, filename = fetch_hd_thumbnail(video_id)

        # Delete search message
        try:
            bot.delete_message(chat_id, search_msg.message_id)
        except:
            pass

        if data:
            bio = io.BytesIO(data)
            bio.name = filename
            bio.seek(0)
            caption = "<b>Image High quality</b>\nThumbnail found!"
            bot.send_photo(chat_id, photo=bio, caption=caption)

            had_first_download[chat_id] = True
            bot.send_message(chat_id, "✅ Thumbnail sent.", reply_markup=after_first_kb())
        else:
            bot.send_message(chat_id, "⚠️ HD Thumbnail not found. Try another video.",
                             reply_markup=(after_first_kb() if had_first_download.get(chat_id) else main_menu_kb()))
        return

    bot.send_message(chat_id, "Please use the menu to start.", 
                     reply_markup=(after_first_kb() if had_first_download.get(chat_id) else main_menu_kb()))

@bot.message_handler(content_types=["photo", "sticker", "video", "document", "audio", "voice", "location"])
def handle_others(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Please send a YouTube video URL when requested.",
                     reply_markup=(after_first_kb() if had_first_download.get(chat_id) else main_menu_kb()))

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()