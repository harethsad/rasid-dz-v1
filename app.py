import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request
import os
import sqlite3
from datetime import datetime

# --- الإعدادات الأساسية ---
# توكن البوت الخاص بك
API_TOKEN = '8731183112:AAEJ5ki0lgqq_i3Ua3hKn-Cspz-ttMwEEgk'
# معرف التلجرام الخاص بك (الأدمن)
ADMIN_ID = 6766302745 
bot = telebot.TeleBot(API_TOKEN, threaded=False)
app = Flask(__name__)
DB_NAME = "rasid_dz.db"

# --- نظام قاعدة البيانات المحسن ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # جدول المستخدمين: تخزين الاسم، الرصيد، والديون
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, name TEXT, username TEXT, balance REAL DEFAULT 0, debt REAL DEFAULT 0)''')
    # جدول الطلبات: لتسجيل كل عملية شحن
    c.execute('''CREATE TABLE IF NOT EXISTS orders 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, service TEXT, details TEXT, status TEXT, date TEXT)''')
    conn.commit()
    conn.close()

# تهيئة قاعدة البيانات عند التشغيل
init_db()

# --- لوحات المفاتيح (نفس شكل الصور 100%) ---
def main_keyboard(uid):
    markup = InlineKeyboardMarkup()
    # السطر الأول: الألعاب والبطاقات
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

    # السطر الثاني: الديون والرصيد والأرباح (مع البيانات الحقيقية)
    markup.row(InlineKeyboardButton(f"الارباح : 0 دج", callback_data="none"),
               InlineKeyboardButton(f"رصيد : {bal} دج", callback_data="none"),
               InlineKeyboardButton(f"ديون : {debt} دج", callback_data="none"))
    
    # السطر الثالث: الخدمات الأخرى
    markup.row(InlineKeyboardButton("سجل التحويلات 📅", callback_data="history"),
               InlineKeyboardButton("حسابك 👤", callback_data="profile"),
               InlineKeyboardButton("تحويل الارباح 💰", callback_data="transfer"))
    
    # السطر الرابع: الدليل والاتصال
    markup.row(InlineKeyboardButton("دليل الاستخدام 📖", callback_data="guide"),
               InlineKeyboardButton("اتصل بنا 👍", callback_data="contact"))
    
    # إضافة زر لوحة الإدارة للأدمن فقط
    if uid == ADMIN_ID:
        markup.row(InlineKeyboardButton("⚙️ لوحة الإدارة (الكريدي)", callback_data="admin_panel"))
    return markup

def cards_keyboard():
    markup = InlineKeyboardMarkup()
    # تقسيم الأزرار لتبدو منظمة كما في الصور
    markup.row(InlineKeyboardButton("Idoom", callback_data="buy_Idoom"), 
               InlineKeyboardButton("4G LTE", callback_data="buy_4GLTE"), 
               InlineKeyboardButton("Mobilis", callback_data="buy_Mobilis"))
    markup.row(InlineKeyboardButton("Djezzy", callback_data="buy_Djezzy"), 
               InlineKeyboardButton("Ooredoo", callback_data="buy_Ooredoo"), 
               InlineKeyboardButton("NETFLIX", callback_data="buy_Netflix"))
    markup.row(InlineKeyboardButton("Google", callback_data="buy_Google"), 
               InlineKeyboardButton("Shahid", callback_data="buy_Shahid"), 
               InlineKeyboardButton("Kaspersky", callback_data="buy_Kaspersky"))
    markup.row(InlineKeyboardButton("ChatGPT", callback_data="buy_ChatGPT"), 
               InlineKeyboardButton("TikTok", callback_data="buy_TikTok"), 
               InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="home"))
    return markup

# --- معالجة الأوامر والرسائل ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    uname = message.from_user.first_name
    uusername = message.from_user.username or "N/A"
    
    # تسجيل المستخدم تلقائياً عند دخوله لأول مرة
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, name, username) VALUES (?, ?, ?)", (uid, uname, uusername))
    conn.commit()
    conn.close()
    
    bot.send_message(message.chat.id, "🇩🇿 مرحباً بك في **Rasid_dz**\nأفضل منصة لخدمات الشحن في الجزائر.", reply_markup=main_keyboard(uid), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    uid = call.from_user.id
    chat_id = call.message.chat.id
    mid = call.message.message_id

    # التعامل مع الأزرار
    if call.data == "home":
        bot.edit_message_text("🇩🇿 القائمة الرئيسية لبوت Rasid_dz:", chat_id, mid, reply_markup=main_keyboard(uid))
    elif call.data == "cards":
        bot.edit_message_text("🎁 جميع أنواع البطاقات:", chat_id, mid, reply_markup=cards_keyboard())
    elif call.data.startswith("buy_"):
        service = call.data.split("_")[1]
        msg = bot.send_message(chat_id, f"📥 يرجى إرسال رقم الهاتف أو الـ ID المطلوب شحنه لـ **{service}**:")
        bot.register_next_step_handler(msg, process_order, service)
    elif call.data == "contact":
        # معلومات الاتصال التجارية الصحيحة
        text = (
            f"📌 **مرحباً بك في Rasid_dz**\n\n"
            f"يرجى الاتصال بنا لشحن حسابك أو الاستفسار:\n\n"
            f"📱 الهاتف: `0554693558`\n"
            f"💬 واتساب: [اضغط للمراسلة](https://wa.me/213554693558)\n\n"
            f"💳 طرق الدفع المتاحة:\n"
            f"• بريدي موب (BaridiMob)\n"
            f"• CCP\n\n"
            f"⚠️ يرجى إرسال صورة الوصل بعد الدفع لضمان سرعة المعالجة."
        )
        markup = InlineKeyboardMarkup().row(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="home"))
        bot.edit_message_text(text, chat_id, mid, reply_markup=markup, parse_mode="Markdown")
    
    elif call.data == "admin_panel" and uid == ADMIN_ID:
        # لوحة إدارة بسيطة (قابلة للتوسيع لتشمل إدارة الديون)
        text = "⚙️ لوحة تحكم الإدارة:\n(قريباً: إضافة ديون، تعديل أرصدة، إرسال رسائل جماعية)"
        markup = InlineKeyboardMarkup().row(InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="home"))
        bot.edit_message_text(text, chat_id, mid, reply_markup=markup)

# --- معالجة الطلبات وإرسالها للأدمن (للعمل من الكمبيوتر) ---
def process_order(message, service):
    # التأكد من أن الرسالة تحتوي على نص
    if not message.text or message.text.startswith('/'):
        bot.send_message(message.chat.id, "❌ خطأ في الإدخال. يرجى إعادة المحاولة.")
        return

    user_input = message.text
    user_name = message.from_user.first_name
    user_id = message.from_user.id
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # رسالة تأكيد للزبون
    bot.send_message(message.chat.id, f"✅ تم استلام طلبك لخدمة **{service}**. جاري المعالجة...")
    
    # تسجيل الطلب في قاعدة البيانات
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO orders (user_id, service, details, status, date) VALUES (?, ?, ?, ?, ?)", 
              (user_id, service, user_input, "Pending", current_time))
    conn.commit()
    conn.close()
    
    # رسالة احترافية للأدمن تظهر على التلجرام ديسكتوب (جاهزة للنسخ بضغطة واحدة)
    admin_text = (
        f"🚀 **طلب شحن جديد!**\n\n"
        f"👤 الزبون: {user_name} (ID: `{user_id}`)\n"
        f"🛠 الخدمة: `{service}`\n"
        f"📱 البيانات: `{user_input}`\n"
        f"⏰ الوقت: `{current_time}`\n\n"
        f"📢 انسخ البيانات وقم بالتنفيذ عبر برنامج الـ GSM."
    )
    # إرسال الإشعار لحساب الأدمن
    bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")

# --- Flask لـ Render ---
@app.route('/' + API_TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.get_data().decode('utf-8'))])
    return "!", 200

@app.route("/")
def index(): return "Rasid_dz is Running Professionally", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
    
