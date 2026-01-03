import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ChatMemberStatus

from config import USER_BOT_TOKEN, MESSAGES
from database import Database
from keyboards import get_channel_buttons

# Logging sozlash
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
print("Bot started")

# Bot va dispatcher
bot = Bot(token=USER_BOT_TOKEN)
dp = Dispatcher()
db = Database("bot_database.db")

async def check_subscription(user_id: int, bot_id: int) -> tuple[bool, list]:
    """
    Foydalanuvchi obunalarini tekshirish
    Returns: (barcha_obuna_bo'ldimi, obuna_bo'lmagan_kanallar)
    """
    channels = await db.get_channels(bot_id)
    not_subscribed = []
    
    for channel in channels:
        try:
            member = await bot.get_chat_member(
                chat_id=channel['channel_id'], 
                user_id=user_id
            )
            
            if channel['type'] == 'private':
                # Private kanal: member yoki creator bo'lsa, yoki request yuborgan bo'lsa OK
                if member.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
                    # Agar restricted yoki left bo'lsa - request yuborgan bo'lishi mumkin
                    # Biz restricted ni qabul qilamiz (bu request yuborgan degani)
                    if member.status == ChatMemberStatus.RESTRICTED:
                        # Request yuborgan, OK
                        continue
                    else:
                        not_subscribed.append(channel)
            else:
                # Public kanal: faqat member yoki admin bo'lsa OK
                if member.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
                    not_subscribed.append(channel)
        
        except Exception as e:
            logger.error(f"Kanal tekshirishda xato {channel['channel_id']}: {e}")
            not_subscribed.append(channel)
    
    return len(not_subscribed) == 0, not_subscribed

@dp.message(CommandStart())
async def start_handler(message: Message):
    """Start komandasi"""
    # Foydalanuvchini DB ga qo'shish
    await db.add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    await message.answer(MESSAGES['start'])

@dp.callback_query(F.data.startswith("download_"))
async def download_handler(callback: CallbackQuery):
    """Yuklab olish tugmasi bosilganda"""
    try:
        # File ID ni olish
        file_db_id = int(callback.data.split("_")[1])
        
        # Faylni topish
        file_data = await db.get_file(file_db_id)
        if not file_data:
            await callback.answer("❌ Fayl topilmadi!", show_alert=True)
            return
        
        bot_id = file_data['bot_id']
        
        # Obunani tekshirish
        is_subscribed, not_subscribed_channels = await check_subscription(
            callback.from_user.id, 
            bot_id
        )
        
        if not is_subscribed:
            # Obuna bo'lmagan
            text = MESSAGES['not_subscribed']
            for channel in not_subscribed_channels:
                type_text = "🔒 Private" if channel['type'] == 'private' else "📢 Public"
                text += f"\n{type_text}: {channel['title']}"
            
            text += "\n\n⚠️ Barcha kanallarga obuna bo'ling yoki so'rov yuboring!"
            
            await callback.message.edit_text(
                text=text,
                reply_markup=get_channel_buttons(not_subscribed_channels)
            )
            await callback.answer()
            return
        
        # Allaqachon yuklab olganmi?
        already_downloaded = await db.check_downloaded(callback.from_user.id, file_db_id)
        
        # Faylni yuborish
        try:
            if file_data['file_type'] == 'video':
                await callback.message.answer_video(
                    video=file_data['file_id'],
                    caption=MESSAGES['file_sent']
                )
            elif file_data['file_type'] == 'document':
                await callback.message.answer_document(
                    document=file_data['file_id'],
                    caption=MESSAGES['file_sent']
                )
            elif file_data['file_type'] == 'photo':
                await callback.message.answer_photo(
                    photo=file_data['file_id'],
                    caption=MESSAGES['file_sent']
                )
            elif file_data['file_type'] == 'audio':
                await callback.message.answer_audio(
                    audio=file_data['file_id'],
                    caption=MESSAGES['file_sent']
                )
            
            # Yuklab olishni qayd qilish (faqat birinchi marta)
            if not already_downloaded:
                await db.add_download(callback.from_user.id, file_db_id)
            
            await callback.answer("✅ Fayl yuborildi!", show_alert=True)
            
        except Exception as e:
            logger.error(f"Fayl yuborishda xato: {e}")
            await callback.answer("❌ Faylni yuborishda xatolik!", show_alert=True)
    
    except Exception as e:
        logger.error(f"Download handler xato: {e}")
        await callback.answer(MESSAGES['error'], show_alert=True)

@dp.callback_query(F.data == "check_sub")
async def check_subscription_handler(callback: CallbackQuery):
    """Obunani tekshirish tugmasi"""
    try:
        # Bu yerda file_db_id ni callback message dan olish kerak
        # Chunki foydalanuvchi qaysi faylni yuklamoqchi ekanligini bilishimiz kerak
        # Hozircha oddiy xabar yuboramiz
        await callback.answer("♻️ Obunalar tekshirilmoqda...", show_alert=False)
        await callback.message.answer(
            "ℹ️ Yuklab olish tugmasini qaytadan bosing va obunalar avtomatik tekshiriladi."
        )
    except Exception as e:
        logger.error(f"Check subscription xato: {e}")
        await callback.answer(MESSAGES['error'], show_alert=True)

async def main():
    """Botni ishga tushirish"""
    # Database initsializatsiya
    await db.init_db()
    
    # Bot haqida ma'lumot
    bot_info = await bot.get_me()
    logger.info(f"User bot ishga tushdi: @{bot_info.username}")
    
    # Polling boshlash
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())