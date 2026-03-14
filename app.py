import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request
import os
import sqlite3

# --- الإعدادات الأساسية ---
API_TOKEN = '8731183112:AAEJ5ki0lgqq_i3Ua3hKn-Cspz-ttMwEEgk'
ADMIN_ID = 6766302745 
bot = telebot.TeleBot(API_TOKEN, threaded=False)
app = Flask(__name__)
DB_NAME = "rasid_dz.db"

# --- نظام قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, name TEXT, balance REAL DEFAULT 0, debt REAL DEFAULT 0)''')
    conn.commit()
    conn.close()

init_db()

# --- لوحات المفاتيح (نفس شكل الصور 100%) ---
def main_keyboard(uid):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("شحن الالعاب 🎮", callback_data="games"), 
               InlineKeyboardButton("بطاقات 🎁", callback_data="cards"))
    
    # جلب البيانات الحقيقية من قاعدة البيانات
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT debt, balance FROM users WHERE user_id=?", (uid,))
    user = c.fetchone()
    debt = user[0] if user else 0
    bal = user[1] if user else 0
    conn.close()

    markup.row(InlineKeyboardButton(f"ديون : {debt} دج", callback_data="none"),
               InlineKeyboardButton(f"رصيد : {bal} دج", callback_data="none"),
               InlineKeyboardButton("الارباح : 0 دج", callback_data="none"))
    
    markup.row(InlineKeyboardButton("تحويل الارباح 💰", callback_data="transfer"),
               InlineKeyboardButton("حسابك 👤", callback_data="profile"),
               InlineKeyboardButton("سجل التحويلات 📅", callback_data="history"))
    
    markup.row(InlineKeyboardButton("اتصل بنا 👍", callback_data="contact"),
               InlineKeyboardButton("دليل الاستخدام 📖", callback_data="guide"))
    
    if uid == ADMIN_ID:
        markup.row(InlineKeyboardButton("⚙️ لوحة الإدارة (الكريدي)", callback_data="admin_panel"))
    return markup

def cards_keyboard():
    markup = InlineKeyboardMarkup()
    # تقسيم الأزرار كما في الصورة 1000031535.jpg
    markup.row(InlineKeyboardButton("Idoom", callback_data="buy_Idoom"), 
               InlineKeyboardButton("4G LTE", callback_data="buy_4GLTE"), 
               InlineKeyboardButton("Mobilis", callback_data="buy_Mobilis"))
    markup.row(InlineKeyboardButton("Djezzy", callback_data="buy_Djezzy"), 
               InlineKeyboardButton("Ooredoo", callback_data="buy_Ooredoo"), 
               InlineKeyboardButton("NETFLIX", callback_data="buy_Netflix"))
    markup.row(InlineKeyboardButton("googal", callback_data="buy_Google"), 
               InlineKeyboardButton("shahid", callback_data="buy_Shahid"), 
               InlineKeyboardButton("kaspersky", callback_data="buy_Kaspersky"))
    markup.row(InlineKeyboardButton("chatgpt 4 plus", callback_data="buy_ChatGPT"), 
               InlineKeyboardButton("tiktok coins", callback_data="buy_TikTok"), 
               InlineKeyboardButton("Retour", callback_data="home"))
    return markup

# --- معالجة الأوامر ---
@bot.message_handler(commands=['start'])
def start(message):
    # تسجيل المستخدم تلقائياً عند دخوله لأول مرة
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, name) VALUES (?, ?)", (message.from_user.id, message.from_user.first_name))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "مرحباً بك في Rasid_dz 🇩🇿", reply_markup=main_keyboard(message.from_user.id))

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    uid = call.from_user.id
    if call.data == "home":
        bot.edit_message_text("الرئيسية:", call.message.chat.id, call.message.message_id, reply_markup=main_keyboard(uid))
    elif call.data == "cards":
        bot.edit_message_text("جميع انواع البطاقات:", call.message.chat.id, call.message.message_id, reply_markup=cards_keyboard())
    elif call.data.startswith("buy_"):
        service = call.data.split("_")[1]
        msg = bot.send_message(call.message.chat.id, f"📥 يرجى إرسال رقم الهاتف أو الـ ID لخدمة {service}:")
        bot.register_next_step_handler(msg, process_order, service)
    elif call.data == "contact":
        text = "📌 **Bienvenue chez boukhatem telecom**\n\nيرجى الاتصال بنا عن طريق:\nالهاتف: 0770XXXXXX\nCCP: 0017XXXXXX\n\nيرجى إرسال الوصل عبر واتساب."
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, 
                             reply_markup=InlineKeyboardMarkup().row(InlineKeyboardButton("العودة", callback_data="home")), parse_mode="Markdown")

# --- معالجة الطلبات وإرسالها لكمبيوترك ---
def process_order(message, service):
    # إشعار للزبون
    bot.send_message(message.chat.id, "✅ تم استلام طلبك بنجاح. جاري المعالجة...")
    # إشعار لك (الأدمن) لتنفيذه من الكمبيوتر
    admin_info = f"🚀 **طلب جديد**\n\n👤 المستخدم: {message.from_user.first_name}\n🛠 الخدمة: {service}\n📱 البيانات: `{message.text}`"
    bot.send_message(ADMIN_ID, admin_info, parse_mode="Markdown")

# --- تشغيل Flask لـ Render ---
@app.route('/' + API_TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return "!", 200

@app.route("/")
def index(): return "Bot is Online", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
    
