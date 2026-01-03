from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from typing import List, Dict

def get_channel_buttons(channels: List[Dict]) -> InlineKeyboardMarkup:
    """Kanallar uchun obuna tugmalari"""
    buttons = []
    
    for channel in channels:
        if channel['username']:
            url = f"https://t.me/{channel['username'].replace('@', '')}"
        elif channel['invite_link']:
            url = channel['invite_link']
        else:
            continue
        
        button_text = f"📢 {channel['title']}"
        buttons.append([InlineKeyboardButton(text=button_text, url=url)])
    
    # Tekshirish tugmasi
    buttons.append([InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_download_button(file_db_id: int) -> InlineKeyboardMarkup:
    """Yuklab olish tugmasi (kanalda ishlatiladi)"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬇️ Yuklab olish", callback_data=f"download_{file_db_id}")]
    ])

def get_admin_main_menu() -> ReplyKeyboardMarkup:
    """Admin asosiy menyu"""
    keyboard = [
        [KeyboardButton(text="🤖 Botlar"), KeyboardButton(text="📢 Kanallar")],
        [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="ℹ️ Yordam")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_bot_management_menu() -> InlineKeyboardMarkup:
    """Bot boshqaruv menyusi"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yangi bot qo'shish", callback_data="add_bot")],
        [InlineKeyboardButton(text="📋 Botlar ro'yxati", callback_data="list_bots")],
        [InlineKeyboardButton(text="🔙 Ortga", callback_data="main_menu")]
    ])

def get_channel_management_menu(bot_id: int) -> InlineKeyboardMarkup:
    """Kanal boshqaruv menyusi"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data=f"add_channel_{bot_id}")],
        [InlineKeyboardButton(text="📋 Kanallar ro'yxati", callback_data=f"list_channels_{bot_id}")],
        [InlineKeyboardButton(text="🔙 Ortga", callback_data="main_menu")]
    ])

def get_bots_list(bots: List[Dict]) -> InlineKeyboardMarkup:
    """Botlar ro'yxati"""
    buttons = []
    for bot in bots:
        buttons.append([
            InlineKeyboardButton(
                text=f"🤖 {bot['name']}", 
                callback_data=f"bot_{bot['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Ortga", callback_data="bots_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_channels_list(channels: List[Dict], bot_id: int) -> InlineKeyboardMarkup:
    """Kanallar ro'yxati"""
    buttons = []
    for channel in channels:
        type_emoji = "🔒" if channel['type'] == "private" else "📢"
        buttons.append([
            InlineKeyboardButton(
                text=f"{type_emoji} {channel['title']}", 
                callback_data=f"channel_{channel['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Ortga", callback_data=f"bot_{bot_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_channel_actions(channel_id: int, bot_id: int) -> InlineKeyboardMarkup:
    """Kanal amallar menyusi"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"del_channel_{channel_id}")],
        [InlineKeyboardButton(text="🔙 Ortga", callback_data=f"list_channels_{bot_id}")]
    ])

def get_cancel_button() -> InlineKeyboardMarkup:
    """Bekor qilish tugmasi"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")]
    ])