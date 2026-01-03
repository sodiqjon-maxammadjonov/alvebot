import aiosqlite
from typing import List, Dict, Optional
import json

class Database:
    def __init__(self, db_name: str):
        self.db_name = db_name
    
    async def init_db(self):
        """Database jadvallarini yaratish"""
        async with aiosqlite.connect(self.db_name) as db:
            # Botlar jadvali
            await db.execute("""
                CREATE TABLE IF NOT EXISTS bots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Kanallar jadvali
            await db.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bot_id INTEGER NOT NULL,
                    channel_id TEXT NOT NULL,
                    username TEXT,
                    title TEXT,
                    type TEXT NOT NULL,
                    invite_link TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (bot_id) REFERENCES bots (id) ON DELETE CASCADE,
                    UNIQUE(bot_id, channel_id)
                )
            """)
            
            # Foydalanuvchilar jadvali
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Fayllar jadvali
            await db.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bot_id INTEGER NOT NULL,
                    file_id TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (bot_id) REFERENCES bots (id) ON DELETE CASCADE
                )
            """)
            
            # Yuklab olishlar jadvali
            await db.execute("""
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    file_id INTEGER NOT NULL,
                    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (file_id) REFERENCES files (id)
                )
            """)
            
            await db.commit()
    
    # ===== BOT FUNKSIYALARI =====
    async def add_bot(self, token: str, name: str) -> int:
        """Yangi bot qo'shish"""
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute(
                "INSERT INTO bots (token, name) VALUES (?, ?)",
                (token, name)
            )
            await db.commit()
            return cursor.lastrowid
    
    async def get_bot_by_token(self, token: str) -> Optional[Dict]:
        """Token orqali botni olish"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM bots WHERE token = ?", (token,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def get_all_bots(self) -> List[Dict]:
        """Barcha botlarni olish"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM bots ORDER BY created_at DESC")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # ===== KANAL FUNKSIYALARI =====
    async def add_channel(self, bot_id: int, channel_id: str, username: str, 
                         title: str, channel_type: str, invite_link: str = None) -> bool:
        """Kanal qo'shish"""
        try:
            async with aiosqlite.connect(self.db_name) as db:
                await db.execute(
                    """INSERT INTO channels (bot_id, channel_id, username, title, type, invite_link) 
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (bot_id, channel_id, username, title, channel_type, invite_link)
                )
                await db.commit()
                return True
        except aiosqlite.IntegrityError:
            return False
    
    async def remove_channel(self, bot_id: int, channel_id: str) -> bool:
        """Kanalni o'chirish"""
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute(
                "DELETE FROM channels WHERE bot_id = ? AND channel_id = ?",
                (bot_id, channel_id)
            )
            await db.commit()
            return cursor.rowcount > 0
    
    async def get_channels(self, bot_id: int) -> List[Dict]:
        """Bot kanallarini olish"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM channels WHERE bot_id = ? ORDER BY created_at DESC",
                (bot_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_channel(self, bot_id: int, channel_id: str) -> Optional[Dict]:
        """Bitta kanalni olish"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM channels WHERE bot_id = ? AND channel_id = ?",
                (bot_id, channel_id)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    # ===== FOYDALANUVCHI FUNKSIYALARI =====
    async def add_user(self, user_id: int, username: str = None, 
                      first_name: str = None, last_name: str = None):
        """Foydalanuvchi qo'shish yoki yangilash"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                """INSERT INTO users (user_id, username, first_name, last_name) 
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(user_id) DO UPDATE SET
                   username = excluded.username,
                   first_name = excluded.first_name,
                   last_name = excluded.last_name""",
                (user_id, username, first_name, last_name)
            )
            await db.commit()
    
    async def get_user_count(self) -> int:
        """Foydalanuvchilar sonini olish"""
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM users")
            count = await cursor.fetchone()
            return count[0] if count else 0
    
    # ===== FAYL FUNKSIYALARI =====
    async def add_file(self, bot_id: int, file_id: str, 
                      file_type: str, file_name: str = None) -> int:
        """Fayl qo'shish"""
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute(
                """INSERT INTO files (bot_id, file_id, file_type, file_name) 
                   VALUES (?, ?, ?, ?)""",
                (bot_id, file_id, file_type, file_name)
            )
            await db.commit()
            return cursor.lastrowid
    
    async def get_file(self, file_db_id: int) -> Optional[Dict]:
        """Faylni olish"""
        async with aiosqlite.connect(self.db_name) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM files WHERE id = ?", (file_db_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    # ===== YUKLAB OLISH FUNKSIYALARI =====
    async def add_download(self, user_id: int, file_id: int):
        """Yuklab olish qayd qilish"""
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                "INSERT INTO downloads (user_id, file_id) VALUES (?, ?)",
                (user_id, file_id)
            )
            await db.commit()
    
    async def check_downloaded(self, user_id: int, file_id: int) -> bool:
        """Foydalanuvchi faylni yuklab olganmi?"""
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM downloads WHERE user_id = ? AND file_id = ?",
                (user_id, file_id)
            )
            count = await cursor.fetchone()
            return count[0] > 0 if count else False
    
    async def get_download_count(self) -> int:
        """Jami yuklab olishlar soni"""
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM downloads")
            count = await cursor.fetchone()
            return count[0] if count else 0
    
    # ===== STATISTIKA =====
    async def get_stats(self, bot_id: int = None) -> Dict:
        """Statistika olish"""
        async with aiosqlite.connect(self.db_name) as db:
            stats = {}
            
            # Foydalanuvchilar
            cursor = await db.execute("SELECT COUNT(*) FROM users")
            stats['total_users'] = (await cursor.fetchone())[0]
            
            # Yuklab olishlar
            cursor = await db.execute("SELECT COUNT(*) FROM downloads")
            stats['total_downloads'] = (await cursor.fetchone())[0]
            
            if bot_id:
                # Bot uchun maxsus statistika
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM channels WHERE bot_id = ?", (bot_id,)
                )
                stats['channels'] = (await cursor.fetchone())[0]
                
                cursor = await db.execute(
                    "SELECT COUNT(*) FROM files WHERE bot_id = ?", (bot_id,)
                )
                stats['files'] = (await cursor.fetchone())[0]
            
            return stats