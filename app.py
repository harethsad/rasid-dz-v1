import telebot
from flask import Flask, request
import os

API_TOKEN = '8731183112:AAEJ5ki0lgqq_i3Ua3hKn-Cspz-ttMwEEgk'
bot = telebot.TeleBot(API_TOKEN, threaded=False)
app = Flask(__name__)

@app.route('/' + API_TOKEN, methods=['POST'])
def getMessage():
    try:
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "!", 200
    except Exception as e:
        print(f"Error: {e}")
        return str(e), 500

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    try:
        bot.reply_to(message, "✅ السيرفر استلم رسالتك ويرد عليك الآن!")
        print("Reply sent successfully!")
    except Exception as e:
        print(f"Failed to send reply: {e}")

@app.route("/")
def webhook():
    return "Bot is active", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
