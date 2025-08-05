import telebot
from telebot import types
from flask import Flask, request
import subprocess
import os
import uuid

# بيانات البوت
API_TOKEN = "8467663079:AAHQxMhHOQ8cW7CqSTv7Y4QTKRL4nlohXnA"
bot = telebot.TeleBot(API_TOKEN)

# قنوات الاشتراك الإجباري
CHANNELS = ["@tyaf90", "@Nodi39"]

# إعداد Flask
app = Flask(__name__)

# التحقق من الاشتراك
def is_subscribed(user_id):
    for channel in CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except:
            return False
    return True

# /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not is_subscribed(message.from_user.id):
        markup = types.InlineKeyboardMarkup()
        for ch in CHANNELS:
            markup.add(types.InlineKeyboardButton(f"📢 اشترك في {ch}", url=f"https://t.me/{ch.replace('@', '')}"))
        bot.send_message(message.chat.id,
                         "🔔 يجب الاشتراك في القنوات التالية لاستخدام البوت:",
                         reply_markup=markup)
        return
    bot.send_message(message.chat.id, "✅ أهلاً بك! أرسل رابط فيديو من YouTube أو TikTok:")

# استقبال الرابط
@bot.message_handler(func=lambda message: True)
def download_video(message):
    if not is_subscribed(message.from_user.id):
        bot.send_message(message.chat.id, "⚠️ اشترك أولاً في القنوات ثم أعد المحاولة.")
        return

    url = message.text.strip()
    if not url.startswith("http"):
        bot.send_message(message.chat.id, "❌ أرسل رابط صحيح.")
        return

    bot.send_message(message.chat.id, "⏳ جاري التحميل، يرجى الانتظار...")

    # إنشاء اسم ملف مؤقت
    file_id = str(uuid.uuid4())
    output_path = f"{file_id}.mp4"

    try:
        # تحميل الفيديو باستخدام yt-dlp مع معالجة الأخطاء
        result = subprocess.run([
            "yt-dlp",
            "-f", "best",  # أفضل جودة متاحة
            "-o", output_path,
            url
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode == 0 and os.path.exists(output_path):
            with open(output_path, 'rb') as video:
                bot.send_video(message.chat.id, video)
        else:
            error_message = result.stderr.decode()
            print("🔴 yt-dlp Error:\n", error_message)
            bot.send_message(message.chat.id, "❌ فشل التحميل، تأكد من أن الرابط صحيح ومدعوم.")

    except Exception as e:
        print("🔴 Exception:", str(e))
        bot.send_message(message.chat.id, "❌ حدث خطأ غير متوقع أثناء التحميل.")

    finally:
        # حذف الفيديو بعد الإرسال
        if os.path.exists(output_path):
            os.remove(output_path)

# إعداد Webhook
@app.route(f"/{API_TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "✅ البوت شغال"

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url="https://downloadtiktok-9cxz.onrender.com/" + API_TOKEN)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
