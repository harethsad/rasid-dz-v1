import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request
import os
import sqlite3
from datetime import datetime

# --- الإعدادات النهائية ---
API_TOKEN = '8731183112:AAEJ5ki0lgqq_i3Ua3hKn-Cspz-ttMwEEgk'
ADMIN_ID = 6766302745 
bot = telebot.TeleBot(API_TOKEN, threaded=False)
app = Flask(__name__)
DB_NAME = "rasid_dz.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, name TEXT, username TEXT, balance REAL DEFAULT 0, debt REAL DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, service TEXT, details TEXT, status TEXT, date TEXT)''')
    conn.commit()
    conn.close()

init_db()

def main_menu(uid):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("شحن الالعاب 🎮", callback_data="games"), 
               InlineKeyboardButton("بطاقات 🎁", callback_data="cards"))
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT balance, debt FROM users WHERE user_id=?", (uid,))
    data = c.fetchone()
    conn.close()
    bal, debt = data if data else (0, 0)

    markup.row(InlineKeyboardButton(f"الارباح : 0 دج", callback_data="none"),
               InlineKeyboardButton(f"رصيد : {bal} دج", callback_data="none"),
               InlineKeyboardButton(f"ديون : {debt} دج", callback_data="none"))
    
    markup.row(InlineKeyboardButton("سجل التحويلات 📅", callback_data="history"),
               InlineKeyboardButton("حسابك 👤", callback_data="profile"),
               InlineKeyboardButton("تحويل الارباح 💰", callback_data="transfer"))
    
    markup.row(InlineKeyboardButton("دليل الاستخدام 📖", callback_data="guide"),
               InlineKeyboardButton("اتصل بنا 👍", callback_data="contact"))
    
    if uid == ADMIN_ID:
        markup.row(InlineKeyboardButton("⚙️ لوحة الإدارة (إضافة كريدي)", callback_data="admin_panel"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    uname = message.from_user.first_name
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, name) VALUES (?, ?)", (uid, uname))
    conn.commit()
    conn.close()
    
    # رسالة ترحيب ذكية تظهر الـ ID للزبون ليسهل عليه إرساله لك
    welcome_msg = (
        f"🇩🇿 مرحبا بك في **Rasid_dz**\n\n"
        f"أفضل منصة لخدمات الشحن في الجزائر.\n"
        f"--------------------------\n"
        f"🆔 الخاص بك: `{uid}` (اضغط للنسخ)"
    )
    bot.send_message(message.chat.id, welcome_msg, reply_markup=main_menu(uid), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    uid = call.from_user.id
    chat_id = call.message.chat.id
    mid = call.message.message_id

    if call.data == "home":
        bot.edit_message_text("🇩🇿 القائمة الرئيسية:", chat_id, mid, reply_markup=main_menu(uid))
    
    elif call.data == "cards":
        markup = InlineKeyboardMarkup(row_width=3)
        btns = ["Idoom", "4G LTE", "Mobilis", "Djezzy", "Ooredoo", "Netflix", "Google", "Shahid", "TikTok"]
        markup.add(*[InlineKeyboardButton(b, callback_data=f"buy_{b}") for b in btns])
        markup.add(InlineKeyboardButton("⬅️ عودة", callback_data="home"))
        bot.edit_message_text("🎁 اختر نوع البطاقة:", chat_id, mid, reply_markup=markup)

    elif call.data == "games":
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("Free Fire 🔥", callback_data="buy_FF"), 
                   InlineKeyboardButton("PUBG Mobile 🔫", callback_data="buy_PUBG"))
        markup.add(InlineKeyboardButton("⬅️ عودة", callback_data="home"))
        bot.edit_message_text("🎮 اختر اللعبة:", chat_id, mid, reply_markup=markup)

    elif call.data.startswith("buy_"):
        service = call.data.split("_")[1]
        msg = bot.send_message(chat_id, f"📥 أرسل الرقم أو الـ ID لـ **{service}**:")
        bot.register_next_step_handler(msg, process_order, service)

    elif call.data == "contact":
        text = (f"📌 **Rasid_dz**\n\n📱 الهاتف: `0554693558`\n💬 واتساب: [اضغط للمراسلة](https://wa.me/213554693558)\n"
                f"💳 بريدي موب: أطلب الرقم عبر الواتساب\n\n⚠️ أرسل صورة الوصل هنا.")
        bot.edit_message_text(text, chat_id, mid, reply_markup=InlineKeyboardMarkup().row(InlineKeyboardButton("⬅️ عودة", callback_data="home")), parse_mode="Markdown")

    elif call.data == "admin_panel" and uid == ADMIN_ID:
        msg = bot.send_message(chat_id, "👤 أرسل (ID الزبون) ثم (المبلغ) لإضافة دين:\nمثال: `12345678 500`")
        bot.register_next_step_handler(msg, process_admin_debt)

def process_admin_debt(message):
    try:
        parts = message.text.split()
        target_id = int(parts[0])
        amount = float(parts[1])
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE users SET debt = debt + ? WHERE user_id = ?", (amount, target_id))
        conn.commit()
        conn.close()
        
        bot.send_message(ADMIN_ID, f"✅ تم إضافة {amount} دج دين للحساب `{target_id}`")
        bot.send_message(target_id, f"🔔 تنبيه: تم إضافة مبلغ {amount} دج إلى ديونك في Rasid_dz.")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ خطأ: تأكد من كتابة ID الزبون ثم المبلغ بشكل صحيح.")

def process_order(message, service):
    if not message.text or message.text.startswith('/'): return
    current_time = datetime.now().strftime("%H:%M:%S | %d/%m")
    bot.send_message(message.chat.id, "✅ تم تسجيل طلبك! سيتصل بك المسؤول فور التنفيذ.")
    admin_text = (f"🚀 **طلب جديد!**\n\n👤 الزبون: {message.from_user.first_name}\n🛠 الخدمة: `{service}`\n"
                  f"📱 البيانات: `{message.text}`\n⏰ الوقت: `{current_time}`")
    bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")

@app.route('/' + API_TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return "!", 200

@app.route("/")
def index(): return "Rasid_dz Professional is Online", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
    
