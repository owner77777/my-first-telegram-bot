import aiosqlite
import time
from datetime import datetime
from config import DB_NAME


# --- БАЗА ДАННЫХ ---
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # (Все ваши SQL команды CREATE TABLE...)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                nickname TEXT,
                reputation INTEGER DEFAULT 0,
                msgs_total INTEGER DEFAULT 0,
                msgs_today INTEGER DEFAULT 0,
                last_msg_date TEXT,
                last_bonus_date TEXT
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS warns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                admin_id INTEGER,
                chat_id INTEGER,
                reason TEXT,
                timestamp INTEGER
            )
        """)

        try:
            await db.execute("SELECT chat_id FROM warns LIMIT 1")
        except Exception:
            await db.execute("ALTER TABLE warns ADD COLUMN chat_id INTEGER")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS rep_log (
                from_user_id INTEGER,
                to_user_id INTEGER,
                timestamp INTEGER
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS punishment_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT, 
                reason TEXT,
                timestamp INTEGER
            )
        """)
        await db.commit()


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (Перенесены из вашего кода) ---

async def get_user(user_id, username=None):
    # ... (Ваша функция get_user)
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()

            clean_username = username.lstrip("@").lower() if username else None

            if not row:
                nick = username if username else f"User{user_id}"
                await db.execute("INSERT INTO users (user_id, username, nickname) VALUES (?, ?, ?)",
                                 (user_id, clean_username, nick))
                await db.commit()
                # Перезапускаем функцию, чтобы получить свежую запись
                return await get_user(user_id, username)

            current_db_username = row[1]
            if clean_username and current_db_username != clean_username:
                await db.execute("UPDATE users SET username = ? WHERE user_id = ?", (clean_username, user_id))
                await db.commit()
            return row


async def get_user_id_by_username(username_input):
    # ... (Ваша функция get_user_id_by_username)
    clean_username = username_input.lstrip("@").lower()
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id FROM users WHERE username = ?", (clean_username,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def update_stats(user_id):
    # ... (Ваша функция update_stats)
    today = datetime.now().strftime("%Y-%m-%d")
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT last_msg_date, msgs_today FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                last_date, msgs_today = row
                new_msgs_today = msgs_today + 1 if last_date == today else 1
                await db.execute("""
                    UPDATE users SET msgs_total = msgs_total + 1, msgs_today = ?, last_msg_date = ? 
                    WHERE user_id = ?""", (new_msgs_today, today, user_id))
                await db.commit()


async def get_active_warns(user_id):
    # ... (Ваша функция get_active_warns)
    now = int(time.time())
    cutoff = now - 2592000
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM warns WHERE user_id = ? AND timestamp > ?",
                              (user_id, cutoff)) as cursor:
            return (await cursor.fetchone())[0]


async def remove_last_warn(user_id):
    # ... (Ваша функция remove_last_warn)
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT id FROM warns WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                warn_id = row[0]
                await db.execute("DELETE FROM warns WHERE id = ?", (warn_id,))
                await db.commit()
                return True
            return False


async def log_punishment(user_id, p_type, reason):
    # ... (Ваша функция log_punishment)
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO punishment_history (user_id, type, reason, timestamp) VALUES (?, ?, ?, ?)",
                         (user_id, p_type, reason, int(time.time())))
        await db.commit()


async def change_reputation(user_id, amount):
    # ... (Ваша функция change_reputation)
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET reputation = reputation + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()


async def set_reputation(user_id, amount):
    # ... (Ваша функция set_reputation)
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET reputation = ? WHERE user_id = ?", (amount, user_id))
        await db.commit()


# ... (Оставьте остальные вспомогательные функции, связанные с БД, здесь)
# ... (async def generate_stats_text(user_id, username):)
# ... (async def warn_scheduler(bot):) - **ВНИМАНИЕ: warn_scheduler должен принимать bot**

async def generate_stats_text(user_id, username):
    """Генерация текста статистики для повторного использования."""
    user_data = await get_user(user_id, username)
    warns = await get_active_warns(user_id)

    text = (
        f"📊 <b>Статистика {user_data[2]}:</b>\n"
        f"✉️ Сообщений всего: {user_data[4]}\n"
        f"📅 Сообщений сегодня: {user_data[5]}\n"
        f"🌟 Репутация: {user_data[3]}\n"
        f"⚠️ Варны: {warns}/3"
    )
    return text


# Переносим warn_scheduler, чтобы он мог использовать объект bot
async def warn_scheduler(bot):
    # ... (Ваша функция warn_scheduler)
    import logging
    import time
    from datetime import datetime
    import aiosqlite
    now = int(time.time())
    cutoff = now - 2592000  # 30 дней назад

    while True:
        try:
            now = int(time.time())
            cutoff = now - 2592000

            async with aiosqlite.connect(DB_NAME) as db:
                async with db.execute("SELECT id, user_id, chat_id FROM warns WHERE timestamp < ?",
                                      (cutoff,)) as cursor:
                    expired_warns = await cursor.fetchall()

                for warn_id, user_id, chat_id in expired_warns:
                    await db.execute("DELETE FROM warns WHERE id = ?", (warn_id,))
                    await db.commit()

                    if chat_id:
                        try:
                            user_info = await db.execute("SELECT nickname FROM users WHERE user_id = ?", (user_id,))
                            row = await user_info.fetchone()
                            name = row[0] if row else "Пользователь"

                            # Используем переданный объект bot
                            await bot.send_message(chat_id,
                                                   f"✅ У пользователя <b>{name}</b> истек срок предупреждения (30 дней). Варн снят.")
                        except Exception as e:
                            logging.error(f"Не удалось отправить сообщение о снятии варна (chat_id={chat_id}): {e}")

        except Exception as e:
            logging.error(f"Ошибка в планировщике варнов: {e}")

        await asyncio.sleep(60)
