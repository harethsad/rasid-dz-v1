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

# --- قاعدة بيانات احترافية ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, name TEXT, balance REAL DEFAULT 0, debt REAL DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, details TEXT, status TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- القوائم الرئيسية (شكل الصور 100%) ---
def main_menu(uid):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("شحن الالعاب 🎮", callback_data="games_menu"), 
               InlineKeyboardButton("بطاقات 🎁", callback_data="cards_menu"))
    
    # جلب الديون والرصيد الحقيقي من القاعدة
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT debt, balance FROM users WHERE user_id=?", (uid,))
    user = c.fetchone()
    debt, bal = (user[0], user[1]) if user else (0, 0)
    conn.close()

    markup.row(InlineKeyboardButton(f"الارباح : 0 دج", callback_data="none"),
               InlineKeyboardButton(f"رصيد : {bal} دج", callback_data="none"),
               InlineKeyboardButton(f"ديون : {debt} دج", callback_data="none"))
    
    markup.row(InlineKeyboardButton("سجل التحويلات 📅", callback_data="history"),
               InlineKeyboardButton("حسابك 👤", callback_data="profile"),
               InlineKeyboardButton("تحويل الارباح 💰", callback_data="transfer"))
    
    markup.row(InlineKeyboardButton("دليل الاستخدام 📖", callback_data="guide"),
               InlineKeyboardButton("اتصل بنا 👍", callback_data="contact"))
    
    if uid == ADMIN_ID:
        markup.row(InlineKeyboardButton("⚙️ لوحة الإدارة (الكريدي)", callback_data="admin_panel"))
    return markup

# --- معالجة الضغط على الأزرار ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    uid = call.from_user.id
    chat_id = call.message.chat.id
    mid = call.message.message_id

    if call.data == "home":
        bot.edit_message_text("🇩🇿 القائمة الرئيسية لبوت Rasid_dz:", chat_id, mid, reply_markup=main_menu(uid))

    elif call.data == "contact":
        # معلومات الاتصال التجارية الصحيحة باسمك ورقمك
        text = (
            f"📌 **Bienvenue chez {os.environ.get('BOT_NAME', 'Rasid_dz')}**\n\n"
            f"يرجى الاتصال بنا لشحن حسابك أو الاستفسار:\n\n"
            f"📱 الهاتف: `0554693558`\n"
            f"💬 واتساب: [اضغط للمراسلة](https://wa.me/213554693558)\n\n"
            f"💳 طرق الدفع المتاحة:\n"
            f"• بريدي موب (BaridiMob)\n"
            f"• CCP\n\n"
            f"⚠️ يرجى إرسال صورة الوصل بعد الدفع لضمان سرعة المعالجة."
        )
        markup = InlineKeyboardMarkup().row(InlineKeyboardButton("⬅️ العودة", callback_data="home"))
        bot.edit_message_text(text, chat_id, mid, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "games_menu":
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("Free Fire 🔥", callback_data="buy_FF"), 
                   InlineKeyboardButton("PUBG Mobile 🔫", callback_data="buy_PUBG"))
        markup.add(InlineKeyboardButton("⬅️ العودة", callback_data="home"))
        bot.edit_message_text("اختر اللعبة المطلوبة للشحن:", chat_id, mid, reply_markup=markup)

    elif call.data == "cards_menu":
        markup = InlineKeyboardMarkup(row_width=3)
        btns = ["Idoom", "4G LTE", "Mobilis", "Djezzy", "Ooredoo", "Netflix", "Google", "Shahid", "TikTok"]
        btn_list = [InlineKeyboardButton(b, callback_data=f"buy_{b}") for b in btns]
        markup.add(*btn_list)
        markup.add(InlineKeyboardButton("⬅️ العودة", callback_data="home"))
        bot.edit_message_text("اختر نوع البطاقة أو التعبئة:", chat_id, mid, reply_markup=markup)

    elif call.data.startswith("buy_"):
        service = call.data.split("_")[1]
        msg = bot.send_message(chat_id, f"📥 يرجى إرسال رقم الهاتف أو الـ ID المطلوب شحنه لـ **{service}**:")
        bot.register_next_step_handler(msg, process_order, service)

    elif call.data == "admin_panel" and uid == ADMIN_ID:
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("👤 إدارة الديون والزبائن", callback_data="admin_debts"))
        markup.row(InlineKeyboardButton("📈 إحصائيات المبيعات", callback_data="admin_stats"))
        markup.add(InlineKeyboardButton("⬅️ العودة", callback_data="home"))
        bot.edit_message_text("⚙️ لوحة تحكم الإدارة (Rasid_dz):", chat_id, mid, reply_markup=markup)

# --- معالجة الطلبات وإرسالها للأدمن (للعمل من الكمبيوتر) ---
def process_order(message, service):
    user_input = message.text
    user_name = message.from_user.first_name
    
    # رسالة للزبون
    bot.send_message(message.chat.id, "✅ تم تسجيل طلبك! سيتصل بك المسؤول فور التنفيذ.")
    
    # رسالة احترافية للأدمن (تظهر على الكمبيوتر)
    admin_text = (
        f"🚀 **طلب شحن جديد!**\n\n"
        f"👤 الزبون: {user_name}\n"
        f"🛠 الخدمة: `{service}`\n"
        f"📱 البيانات: `{user_input}`\n"
        f"⏰ الوقت: {message.date}\n\n"
        f"📢 انسخ البيانات وقم بالتنفيذ عبر GSM."
    )
    bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")

# --- الأوامر الأساسية ---
@bot.message_handler(commands=['start'])
def start(message):
    # تسجيل المستخدم في قاعدة البيانات
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, name) VALUES (?, ?)", (message.from_user.id, message.from_user.first_name))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, "🇩🇿 مرحباً بك في **Rasid_dz**\nأفضل منصة لخدمات الفليكسي والبطاقات في الجزائر.", 
                     reply_markup=main_menu(message.from_user.id), parse_mode="Markdown")

# --- Flask لـ Render ---
@app.route('/' + API_TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return "!", 200

@app.route("/")
def index(): return "Rasid_dz is Running Professionally", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
    
