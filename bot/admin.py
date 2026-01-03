import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import ADMIN_BOT_TOKEN, ADMIN_ID, USER_BOT_TOKEN
from database import Database
from keyboards import (
    get_admin_main_menu, get_bot_management_menu,
    get_channel_management_menu, get_bots_list,
    get_channels_list, get_channel_actions, get_cancel_button
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot va dispatcher
bot = Bot(token=ADMIN_BOT_TOKEN)
user_bot = Bot(token=USER_BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
db = Database("bot_database.db")

# FSM States
class BotStates(StatesGroup):
    waiting_bot_token = State()
    waiting_bot_name = State()

class ChannelStates(StatesGroup):
    waiting_channel_id = State()
    selected_bot_id = State()

def is_admin(user_id: int) -> bool:
    """Admin tekshiruvi"""
    return user_id == ADMIN_ID

@dp.message(CommandStart())
async def start_handler(message: Message):
    """Start komandasi"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqlari yo'q!")
        return
    
    await message.answer(
        "👋 Admin paneliga xush kelibsiz!\n\n"
        "Bu yerda botlaringizni va kanallaringizni boshqarishingiz mumkin.",
        reply_markup=get_admin_main_menu()
    )

@dp.message(F.text == "🤖 Botlar")
async def bots_menu_handler(message: Message):
    """Botlar menyusi"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "🤖 <b>Bot boshqaruvi</b>\n\n"
        "Bu bo'limda botlaringizni qo'shishingiz va boshqarishingiz mumkin.",
        reply_markup=get_bot_management_menu(),
        parse_mode="HTML"
    )

@dp.message(F.text == "📢 Kanallar")
async def channels_menu_handler(message: Message):
    """Kanallar menyusi"""
    if not is_admin(message.from_user.id):
        return
    
    bots = await db.get_all_bots()
    if not bots:
        await message.answer(
            "❌ Avval bot qo'shishingiz kerak!\n\n"
            "🤖 Botlar → ➕ Yangi bot qo'shish"
        )
        return
    
    await message.answer(
        "📢 <b>Kanallar boshqaruvi</b>\n\n"
        "Qaysi botga kanal qo'shmoqchisiz?",
        reply_markup=get_bots_list(bots),
        parse_mode="HTML"
    )

@dp.message(F.text == "📊 Statistika")
async def stats_handler(message: Message):
    """Statistika"""
    if not is_admin(message.from_user.id):
        return
    
    stats = await db.get_stats()
    bots = await db.get_all_bots()
    
    text = "📊 <b>Umumiy statistika</b>\n\n"
    text += f"👥 Foydalanuvchilar: {stats['total_users']}\n"
    text += f"⬇️ Yuklab olishlar: {stats['total_downloads']}\n"
    text += f"🤖 Botlar soni: {len(bots)}\n\n"
    
    for bot_data in bots:
        bot_stats = await db.get_stats(bot_data['id'])
        text += f"<b>{bot_data['name']}</b>\n"
        text += f"  📢 Kanallar: {bot_stats.get('channels', 0)}\n"
        text += f"  📁 Fayllar: {bot_stats.get('files', 0)}\n\n"
    
    await message.answer(text, parse_mode="HTML")

@dp.message(F.text == "ℹ️ Yordam")
async def help_handler(message: Message):
    """Yordam"""
    if not is_admin(message.from_user.id):
        return
    
    text = """
ℹ️ <b>Admin Panel Yo'riqnomasi</b>

<b>1. Bot qo'shish:</b>
🤖 Botlar → ➕ Yangi bot qo'shish
- @BotFather dan yangi bot yarating
- Bot tokenni kiriting
- Bot nomini kiriting

<b>2. Kanal qo'shish:</b>
📢 Kanallar → Botni tanlang → ➕ Kanal qo'shish
- Kanal ID yoki @username kiriting
- Bot kanalda admin bo'lishi SHART!

<b>3. Fayl yuklash:</b>
User botingizga fayl yuboring
Fayl avtomatik bazaga saqlanadi

<b>4. Kanalingizda post:</b>
Post qiling va fayl ostida inline button qo'ying:
⬇️ Yuklab olish → Callback data: download_FILE_ID

<b>Qo'llab-quvvatlash:</b>
@yoursupport
"""
    
    await message.answer(text, parse_mode="HTML")

# ===== BOT QO'SHISH =====
@dp.callback_query(F.data == "add_bot")
async def add_bot_start(callback: CallbackQuery, state: FSMContext):
    """Bot qo'shish boshlash"""
    if not is_admin(callback.from_user.id):
        return
    
    await callback.message.answer(
        "🤖 <b>Yangi bot qo'shish</b>\n\n"
        "Bot tokenni kiriting (@BotFather dan olingan):\n\n"
        "Masalan: <code>1234567890:ABCdefGHIjklMNOpqrsTUVwxyz</code>",
        reply_markup=get_cancel_button(),
        parse_mode="HTML"
    )
    await state.set_state(BotStates.waiting_bot_token)
    await callback.answer()

@dp.message(BotStates.waiting_bot_token)
async def add_bot_token(message: Message, state: FSMContext):
    """Bot token qabul qilish"""
    token = message.text.strip()
    
    # Token formatini tekshirish
    if ":" not in token or len(token) < 40:
        await message.answer(
            "❌ Noto'g'ri token formati!\n\n"
            "Token shunday ko'rinishda bo'lishi kerak:\n"
            "<code>1234567890:ABCdefGHIjklMNOpqrsTUVwxyz</code>",
            parse_mode="HTML"
        )
        return
    
    # Tokenni tekshirish
    try:
        test_bot = Bot(token=token)
        bot_info = await test_bot.get_me()
        await test_bot.session.close()
        
        await state.update_data(token=token, bot_username=bot_info.username)
        await message.answer(
            f"✅ Bot topildi: @{bot_info.username}\n\n"
            "Endi bot uchun nom kiriting (masalan: 'Kanal Bot'):"
        )
        await state.set_state(BotStates.waiting_bot_name)
        
    except Exception as e:
        await message.answer(f"❌ Token noto'g'ri yoki bot topilmadi!\n\nXato: {str(e)}")

@dp.message(BotStates.waiting_bot_name)
async def add_bot_name(message: Message, state: FSMContext):
    """Bot nomi qabul qilish"""
    name = message.text.strip()
    
    if len(name) < 2:
        await message.answer("❌ Nom juda qisqa! Kamida 2 ta belgi kiriting.")
        return
    
    data = await state.get_data()
    token = data['token']
    bot_username = data['bot_username']
    
    # Bazaga qo'shish
    try:
        bot_id = await db.add_bot(token, name)
        await message.answer(
            f"✅ <b>Bot muvaffaqiyatli qo'shildi!</b>\n\n"
            f"📝 Nom: {name}\n"
            f"🤖 Username: @{bot_username}\n"
            f"🆔 ID: {bot_id}\n\n"
            f"Endi bu botga kanallar qo'shishingiz mumkin!",
            reply_markup=get_admin_main_menu(),
            parse_mode="HTML"
        )
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ Xatolik: {str(e)}")
        await state.clear()

@dp.callback_query(F.data == "list_bots")
async def list_bots_handler(callback: CallbackQuery):
    """Botlar ro'yxati"""
    if not is_admin(callback.from_user.id):
        return
    
    bots = await db.get_all_bots()
    if not bots:
        await callback.answer("❌ Hali botlar qo'shilmagan!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🤖 <b>Botlar ro'yxati:</b>\n\n"
        "Batafsil ma'lumot olish uchun botni tanlang:",
        reply_markup=get_bots_list(bots),
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("bot_"))
async def bot_detail_handler(callback: CallbackQuery):
    """Bot tafsilotlari"""
    if not is_admin(callback.from_user.id):
        return
    
    bot_id = int(callback.data.split("_")[1])
    bots = await db.get_all_bots()
    bot_data = next((b for b in bots if b['id'] == bot_id), None)
    
    if not bot_data:
        await callback.answer("❌ Bot topilmadi!", show_alert=True)
        return
    
    stats = await db.get_stats(bot_id)
    channels = await db.get_channels(bot_id)
    
    text = f"🤖 <b>{bot_data['name']}</b>\n\n"
    text += f"🆔 ID: {bot_id}\n"
    text += f"📢 Kanallar: {len(channels)}\n"
    text += f"📁 Fayllar: {stats.get('files', 0)}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_channel_management_menu(bot_id),
        parse_mode="HTML"
    )
    await callback.answer()

# ===== KANAL QO'SHISH =====
@dp.callback_query(F.data.startswith("add_channel_"))
async def add_channel_start(callback: CallbackQuery, state: FSMContext):
    """Kanal qo'shish boshlash"""
    if not is_admin(callback.from_user.id):
        return
    
    bot_id = int(callback.data.split("_")[2])
    
    await state.update_data(bot_id=bot_id)
    await state.set_state(ChannelStates.waiting_channel_id)
    
    await callback.message.answer(
        "📢 <b>Kanal qo'shish</b>\n\n"
        "Kanal ID yoki @username kiriting:\n\n"
        "<b>Public kanal:</b> @kanalim\n"
        "<b>Private kanal:</b> -1001234567890\n\n"
        "⚠️ Bot kanalda admin bo'lishi SHART!",
        reply_markup=get_cancel_button(),
        parse_mode="HTML"
    )
    await callback.answer()

@dp.message(ChannelStates.waiting_channel_id)
async def add_channel_id(message: Message, state: FSMContext):
    """Kanal ID qabul qilish"""
    channel_input = message.text.strip()
    data = await state.get_data()
    bot_id = data['bot_id']
    
    try:
        # Kanalga kirish va ma'lumot olish
        chat = await user_bot.get_chat(channel_input)
        
        # Bot admin ekanligini tekshirish
        bot_member = await user_bot.get_chat_member(chat.id, user_bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            await message.answer(
                "❌ Bot bu kanalda admin emas!\n\n"
                "Iltimos botni kanalga admin qilib qo'shing va qaytadan urinib ko'ring."
            )
            return
        
        # Kanal turini aniqlash
        channel_type = "private" if chat.type == "channel" and chat.username is None else "public"
        
        # Invite link olish (agar private bo'lsa)
        invite_link = None
        if channel_type == "private":
            try:
                link = await user_bot.export_chat_invite_link(chat.id)
                invite_link = link
            except:
                pass
        
        # Bazaga qo'shish
        success = await db.add_channel(
            bot_id=bot_id,
            channel_id=str(chat.id),
            username=chat.username,
            title=chat.title,
            channel_type=channel_type,
            invite_link=invite_link
        )
        
        if success:
            type_emoji = "🔒" if channel_type == "private" else "📢"
            await message.answer(
                f"✅ <b>Kanal muvaffaqiyatli qo'shildi!</b>\n\n"
                f"{type_emoji} {chat.title}\n"
                f"🆔 ID: {chat.id}\n"
                f"🔗 Username: @{chat.username or 'Private'}\n"
                f"📝 Turi: {channel_type.title()}",
                reply_markup=get_admin_main_menu(),
                parse_mode="HTML"
            )
        else:
            await message.answer("❌ Bu kanal allaqachon qo'shilgan!")
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Kanal qo'shishda xato: {e}")
        await message.answer(
            f"❌ Xatolik yuz berdi!\n\n"
            f"Sabab: {str(e)}\n\n"
            f"Tekshiring:\n"
            f"• Kanal ID to'g'ri kiritilganmi?\n"
            f"• Bot kanalda adminmi?\n"
            f"• Bot kanalga kirish huquqiga egami?"
        )

@dp.callback_query(F.data.startswith("list_channels_"))
async def list_channels_handler(callback: CallbackQuery):
    """Kanallar ro'yxati"""
    if not is_admin(callback.from_user.id):
        return
    
    bot_id = int(callback.data.split("_")[2])
    channels = await db.get_channels(bot_id)
    
    if not channels:
        await callback.answer("❌ Bu botga hali kanallar qo'shilmagan!", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"📢 <b>Kanallar ro'yxati</b>\n\n"
        f"Jami: {len(channels)} ta kanal",
        reply_markup=get_channels_list(channels, bot_id),
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("channel_"))
async def channel_detail_handler(callback: CallbackQuery):
    """Kanal tafsilotlari"""
    if not is_admin(callback.from_user.id):
        return
    
    channel_db_id = int(callback.data.split("_")[1])
    
    # Kanalni topish (barcha botlardan)
    all_bots = await db.get_all_bots()
    channel = None
    bot_id = None
    
    for bot_data in all_bots:
        channels = await db.get_channels(bot_data['id'])
        for ch in channels:
            if ch['id'] == channel_db_id:
                channel = ch
                bot_id = bot_data['id']
                break
        if channel:
            break
    
    if not channel:
        await callback.answer("❌ Kanal topilmadi!", show_alert=True)
        return
    
    type_emoji = "🔒" if channel['type'] == "private" else "📢"
    text = f"{type_emoji} <b>{channel['title']}</b>\n\n"
    text += f"🆔 ID: {channel['channel_id']}\n"
    text += f"🔗 Username: @{channel['username'] or 'Private'}\n"
    text += f"📝 Turi: {channel['type'].title()}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_channel_actions(channel_db_id, bot_id),
        parse_mode="HTML"
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("del_channel_"))
async def delete_channel_handler(callback: CallbackQuery):
    """Kanalni o'chirish"""
    if not is_admin(callback.from_user.id):
        return
    
    channel_db_id = int(callback.data.split("_")[2])
    
    # Kanalni topish
    all_bots = await db.get_all_bots()
    channel = None
    bot_id = None
    
    for bot_data in all_bots:
        channels = await db.get_channels(bot_data['id'])
        for ch in channels:
            if ch['id'] == channel_db_id:
                channel = ch
                bot_id = bot_data['id']
                break
        if channel:
            break
    
    if not channel:
        await callback.answer("❌ Kanal topilmadi!", show_alert=True)
        return
    
    # O'chirish
    success = await db.remove_channel(bot_id, channel['channel_id'])
    
    if success:
        await callback.answer("✅ Kanal o'chirildi!", show_alert=True)
        # Kanallar ro'yxatiga qaytish
        channels = await db.get_channels(bot_id)
        if channels:
            await callback.message.edit_text(
                f"📢 <b>Kanallar ro'yxati</b>\n\nJami: {len(channels)} ta kanal",
                reply_markup=get_channels_list(channels, bot_id),
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                "📢 Bu botda kanallar yo'q.",
                reply_markup=get_channel_management_menu(bot_id)
            )
    else:
        await callback.answer("❌ Xatolik!", show_alert=True)

# ===== UMUMIY =====
@dp.callback_query(F.data == "cancel")
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    """Bekor qilish"""
    await state.clear()
    await callback.message.answer(
        "❌ Amal bekor qilindi.",
        reply_markup=get_admin_main_menu()
    )
    await callback.answer()

@dp.callback_query(F.data == "main_menu")
async def main_menu_handler(callback: CallbackQuery):
    """Asosiy menyu"""
    await callback.message.edit_text(
        "👋 Admin paneliga xush kelibsiz!\n\n"
        "Bu yerda botlaringizni va kanallaringizni boshqarishingiz mumkin."
    )
    await callback.answer()

@dp.callback_query(F.data == "bots_menu")
async def bots_menu_callback(callback: CallbackQuery):
    """Botlar menyusiga qaytish"""
    await callback.message.edit_text(
        "🤖 <b>Bot boshqaruvi</b>\n\n"
        "Bu bo'limda botlaringizni qo'shishingiz va boshqarishingiz mumkin.",
        reply_markup=get_bot_management_menu(),
        parse_mode="HTML"
    )
    await callback.answer()

async def main():
    """Admin botni ishga tushirish"""
    await db.init_db()
    
    bot_info = await bot.get_me()
    logger.info(f"Admin bot ishga tushdi: @{bot_info.username}")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())