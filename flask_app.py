import telebot
from flask import Flask, request
import os

# ضع توكن بوتك هنا
API_TOKEN = '8731183112:AAEJ5ki0lgqq_i3Ua3hKn-Cspz-ttMwEEgk'

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# رسالة الترحيب عند كتابة /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً بك في Rasid_dz على منصة Render! 🚀\nالبوت يعمل الآن بنجاح وبدون قيود.")

# الرد على أي رسالة أخرى (تجربة)
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "تم استلام رسالتك في نظام Rasid_dz: " + message.text)

# إعدادات استقبال البيانات من تلجرام (Webhook)
@app.route('/' + API_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

# صفحة رئيسية للتأكد أن السيرفر يعمل
@app.route("/")
def webhook():
    return "Bot is Running Successfully!", 200

if __name__ == "__main__":
    # هذا السطر ضروري لـ Render ليحدد المنفذ (Port) تلقائياً
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
  
