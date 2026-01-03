import os
from dotenv import load_dotenv

load_dotenv()

# Bot tokenlar
USER_BOT_TOKEN = os.getenv("USER_BOT_TOKEN")
ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN")

# Admin ID
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# Database
DATABASE_NAME = os.getenv("DATABASE_NAME", "bot_database.db")

# Xabar shablonlari
MESSAGES = {
    "start": "👋 Assalomu alaykum!\n\nFayllarni yuklab olish uchun kanallarimizga obuna bo'ling.",
    "not_subscribed": "❌ Siz quyidagi kanallarga obuna bo'lmagansiz yoki so'rov yubormagansiz:\n\n",
    "check_subscription": "✅ Obunani tekshirish",
    "subscribed": "✅ Rahmat! Endi faylingizni yuklab olishingiz mumkin.",
    "subscribe_button": "📢 Obuna bo'lish",
    "already_downloaded": "⚠️ Siz bu faylni allaqachon yuklab olgansiz.",
    "file_sent": "✅ Fayl yuborildi!",
    "error": "❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.",
}