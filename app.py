import telebot
from flask import Flask, request
import os

API_TOKEN = '8731183112:AAEJ5ki0lgqq_i3Ua3hKn-Cspz-ttMwEEgk'
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# هذا الجزء هو المسؤول عن الرد على رسالة البداية
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً بك! بوت رصيد ديزاد يعمل الآن بنجاح على Render 🚀")

# هذا الجزء لاستقبال أي رسالة نصية أخرى
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "وصلت رسالتك: " + message.text)

@app.route('/' + API_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    return "Bot is Running!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
