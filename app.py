import telebot
from flask import Flask, request
import os

# التوكن الخاص بك
API_TOKEN = '8731183112:AAEJ5ki0lgqq_i3Ua3hKn-Cspz-ttMwEEgk'
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# الرد على رسالة البداية
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "✅ البوت شغال 100% على سيرفر Render!")

# الرد على أي رسالة أخرى
@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.reply_to(message, "وصلت رسالتك للسيرفر: " + message.text)

@app.route('/' + API_TOKEN, methods=['POST'])
def getMessage():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "!", 200
    else:
        return "Forbidden", 403

@app.route("/")
def webhook():
    return "Bot Server is Live!", 200

if __name__ == "__main__":
    # تشغيل السيرفر على البورت المطلوب
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
