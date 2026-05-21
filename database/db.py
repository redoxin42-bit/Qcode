# Путь: database/db.py
import aiosqlite
from config import DB_PATH

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                api_id INTEGER,
                api_hash TEXT,
                phone TEXT,
                status TEXT DEFAULT 'not_configured',
                has_subscription INTEGER DEFAULT 0
            )
        """)
        await db.commit()

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()

async def add_or_update_user(user_id: int, api_id: int = None, api_hash: str = None, phone: str = None, status: str = None, has_sub: int = None):
    async with aiosqlite.connect(DB_PATH) as db:
        user = await get_user(user_id)
        if not user:
            await db.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
            await db.commit()
        
        if api_id is not None:
            await db.execute("UPDATE users SET api_id = ?, api_hash = ? WHERE user_id = ?", (api_id, api_hash, user_id))
        if phone is not None:
            await db.execute("UPDATE users SET phone = ? WHERE user_id = ?", (phone, user_id))
        if status is not None:
            await db.execute("UPDATE users SET status = ? WHERE user_id = ?", (status, user_id))
        if has_sub is not None:
            await db.execute("UPDATE users SET has_subscription = ? WHERE user_id = ?", (has_sub, user_id))
        
        await db.commit()

async def set_sub_to_all(has_sub: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET has_subscription = ?", (has_sub,))
        await db.commit()

async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM users") as cursor:
            return await cursor.fetchall()
