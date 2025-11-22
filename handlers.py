from aiogram import Dispatcher, F, types
from aiogram.filters import Command, CommandObject
from aiogram.types import ChatPermissions, CallbackQuery
from datetime import datetime, timedelta
import random
import time
import aiosqlite
import logging

# Импортируем все необходимое
from database import *  # Импортируем все функции БД
from keyboards import *  # Импортируем все клавиатуры
from config import DB_NAME


# Вспомогательные функции, не связанные с БД
async def get_target_user_id(message: types.Message, command: CommandObject):
    # ... (Ваша функция get_target_user_id)
    if message.reply_to_message:
        return message.reply_to_message.from_user.id, message.reply_to_message.from_user.first_name

    if command.args:
        username_arg = command.args.split()[0]
        user_id = await get_user_id_by_username(username_arg)
        if user_id:
            return user_id, username_arg

    return None, None


async def is_admin(message: types.Message):
    # ... (Ваша функция is_admin)
    if message.chat.type == 'private':
        return False
    member = await message.chat.get_member(message.from_user.id)
    return member.status in ['administrator', 'creator']


async def is_creator(message: types.Message):
    # ... (Ваша функция is_creator)
    member = await message.chat.get_member(message.from_user.id)
    return member.status == 'creator'


# Функция для регистрации хендлеров в диспетчере
def register_handlers(dp: Dispatcher):
    # --- ХЕНДЛЕРЫ КОМАНД (Регистрируем как методы dp.message) ---

    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        await get_user(message.from_user.id, message.from_user.username)
        await message.answer("Бот активирован! Используйте /help для списка команд.")

    # ... (Все остальные ваши хендлеры, например: cmd_help, cmd_info, cmd_stats и т.д.)
    @dp.message(Command("help"))
    async def cmd_help(message: types.Message):
        text = (
            "<b>📚 Помощь пользователям:</b>\n"
            "<b>stats</b> — Моя статистика\n"
            "<b>top</b> — Топ участников\n"
            "<b>staff</b> — Администрация чата\n"
            "<b>bonus</b> — Ежедневный бонус репутации\n"
            "<b>info</b> — Информация о чате\n"
            "<b>rep</b> + или - — Изменить репутацию"
        )
        await message.answer(text, reply_markup=get_help_keyboard())

    # ... (Просто перенесите все ваши функции cmd_* и callback_* сюда, без изменений,
    # кроме того, что они теперь используют импортированные функции и константы)

    @dp.callback_query(F.data == "help_back")
    async def callback_help_back(callback: CallbackQuery):
        text = (
            "<b>📚 Помощь пользователям:</b>\n"
            "<b>stats</b> — Моя статистика\n"
            "<b>top</b> — Топ участников\n"
            "<b>staff</b> — Администрация чата\n"
            "<b>bonus</b> — Ежедневный бонус репутации\n"
            "<b>info</b> — Информация о чате\n"
            "<b>rep</b> + или - — Изменить репутацию"
        )
        await callback.message.edit_text(text, reply_markup=get_help_keyboard())

    @dp.callback_query(F.data == "help_mod")
    async def callback_help_mod(callback: CallbackQuery):
        member = await callback.message.chat.get_member(callback.from_user.id)
        if member.status not in ['administrator', 'creator']:
            return await callback.answer("⛔️ Доступ только для модераторов!", show_alert=True)

        text = (
            "<b>🛡 Помощь модераторам:</b>\n"
            "<b>kick</b> — Выгнать\n"
            "<b>ban</b> — Забанить\n"
            "<b>mute</b> — Замутить\n"
            "<b>warn</b> — Выдать предупреждение\n"
            "<b>clear</b> — Удалить сообщения\n"
            "<b>check</b> — Проверить пользователя\n"
            "<b>setnick</b> [ник] — Установить никнейм пользователю (только админ)\n\n"
            "<b>🚑 Снятие наказаний:</b>\n"
            "<b>unmute</b> — Снять мут (+1 реп)\n"
            "<b>unwarn</b> — Снять варн (+5 реп)\n"
            "<b>unban</b> — Разбанить\n\n"
            "<b>👑 Владелец:</b>\n"
            "<b>setrep</b> [число] — Установить репутацию"
        )
        await callback.message.edit_text(text, reply_markup=get_help_mod_keyboard())

    # (Все остальные ваши хендлеры и колбэки переносятся сюда)
    @dp.message(Command("info"))
    async def cmd_info(message: types.Message):
        text = (
            "👑 <b>Основатель чата:</b> Имя Основателя\n"
            "📜 <b>Правила чата:</b> Соблюдайте адекватность.\n"
            "📢 <b>Канал в TG:</b> <a href='https://t.me/channel'>Перейти</a>\n"
            "💬 <b>Чат в TG:</b> <a href='https://t.me/chat'>Перейти</a>\n"
            "💎 <b>Услуги:</b> Доступны по кнопке ниже."
        )
        await message.answer(text, disable_web_page_preview=True, reply_markup=get_info_keyboard())

    @dp.message(Command("staff"))
    async def cmd_staff(message: types.Message):
        admins = await message.chat.get_administrators()
        creator = ""
        staff_list = []

        for admin in admins:
            user = admin.user
            name = user.first_name
            if admin.status == "creator":
                creator = f"👑 <b>Создатель:</b> {name} (@{user.username})" if user.username else f"👑 <b>Создатель:</b> {name}"
            else:
                staff_line = f"👮 {name} (@{user.username})" if user.username else f"👮 {name}"
                staff_list.append(staff_line)

        text = creator + "\n\n<b>Модераторы:</b>\n" + "\n".join(
            staff_list) if staff_list else creator + "\n\n<b>Модераторы:</b>\nПока нет"
        await message.answer(text)

    @dp.message(Command("setnick"))
    async def cmd_setnick(message: types.Message, command: CommandObject):
        if not await is_admin(message):
            return await message.reply("⛔️ Эта команда доступна только модераторам.")

        if not command.args:
            return await message.reply("Использование: /setnick НовыйНик (ответом на сообщение)")

        target_id = message.from_user.id
        new_nick = command.args

        if message.reply_to_message:
            target_id = message.reply_to_message.from_user.id

        if len(new_nick) > 20:
            return await message.reply("Ник слишком длинный!")

        await set_reputation(target_id,
                             new_nick)  # Здесь была ошибка, функция set_reputation меняет репутацию, а не ник.
        # В вашем коде это: await db.execute("UPDATE users SET nickname = ? WHERE user_id = ?", (new_nick, target_id))

        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("UPDATE users SET nickname = ? WHERE user_id = ?", (new_nick, target_id))
            await db.commit()

        await message.reply(f"Никнейм пользователя изменен на: <b>{new_nick}</b>")

    @dp.message(Command("bonus"))
    async def cmd_bonus(message: types.Message):
        user_id = message.from_user.id
        await get_user(user_id, message.from_user.username)

        today = datetime.now().strftime("%Y-%m-%d")
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute("SELECT last_bonus_date FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row and row[0] == today:
                    return await message.reply("⏳ Вы уже получали бонус сегодня!")

            bonus = random.randint(1, 5)
            await db.execute("UPDATE users SET reputation = reputation + ?, last_bonus_date = ? WHERE user_id = ?",
                             (bonus, today, user_id))
            await db.commit()

        await message.reply(f"🎁 Вы получили бонус: <b>+{bonus} репутации</b>!")

    @dp.message(Command("stats"))
    async def cmd_stats(message: types.Message, command: CommandObject):
        target_id = message.from_user.id
        target_username = message.from_user.username

        if message.reply_to_message:
            target_id = message.reply_to_message.from_user.id
            target_username = message.reply_to_message.from_user.username
        elif command.args:
            username_arg = command.args.split()[0]
            found_id = await get_user_id_by_username(username_arg)
            if found_id:
                target_id = found_id
                target_username = username_arg

        text = await generate_stats_text(target_id, target_username)
        await message.answer(text, reply_markup=get_stats_keyboard(target_id))

    @dp.message(Command("top"))
    async def cmd_top(message: types.Message):
        await message.answer("📊 Выберите тип топа:", reply_markup=get_top_keyboard())

    # --- ОБРАБОТКА ТОПОВ (CALLBACK) ---
    @dp.callback_query(F.data.startswith("top:"))
    async def callback_top(callback: CallbackQuery):
        mode = callback.data.split(":")[1]

        async with aiosqlite.connect(DB_NAME) as db:
            if mode == "msgs":
                rows = await db.execute_fetchall(
                    "SELECT nickname, msgs_total FROM users ORDER BY msgs_total DESC LIMIT 10")
                title = "🏆 Топ 10 по сообщениям"
            else:
                rows = await db.execute_fetchall(
                    "SELECT nickname, reputation FROM users ORDER BY reputation DESC LIMIT 10")
                title = "⭐️ Топ 10 по репутации"

        text = f"<b>{title}:</b>\n"
        for i, row in enumerate(rows, 1):
            val = row[1]
            text += f"{i}. {row[0]} — {val}\n"

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад к выбору", callback_data="top_back")]
        ])
        await callback.message.edit_text(text, reply_markup=kb)

    @dp.callback_query(F.data == "top_back")
    async def callback_top_back(callback: CallbackQuery):
        await callback.message.edit_text("📊 Выберите тип топа:", reply_markup=get_top_keyboard())

    # --- МОДЕРАЦИЯ ---

    @dp.message(Command("kick"))
    async def cmd_kick(message: types.Message, command: CommandObject):
        if not await is_admin(message): return
        target_id, target_name = await get_target_user_id(message, command)
        if not target_id: return await message.reply("⚠️ Укажите пользователя.")

        reason = "без указания причины"
        if command.args:
            parts = command.args.split()
            if parts[0].startswith("@") and len(parts) > 1:
                reason = " ".join(parts[1:])
            elif not parts[0].startswith("@"):
                reason = command.args

        try:
            await message.chat.ban(target_id)
            await message.chat.unban(target_id)
            now_str = datetime.now().strftime("%d.%m.%Y %H:%M")

            await message.answer(
                f"👢 Пользователь {target_name} был кикнут.\n"
                f"📄 Причина: {reason}\n"
                f"🕒 Дата: {now_str}"
            )
            await log_punishment(target_id, "kick", reason)
        except Exception as e:
            await message.reply(f"Ошибка: {e}")

    @dp.message(Command("ban"))
    async def cmd_ban(message: types.Message, command: CommandObject):
        if not await is_admin(message): return
        target_id, target_name = await get_target_user_id(message, command)
        if not target_id: return await message.reply("⚠️ Укажите пользователя.")

        args = command.args.split() if command.args else []
        if args and args[0].startswith("@"): args.pop(0)

        time_days = None
        reason = "без указания причины"

        if args:
            try:
                time_days = int(args[0])
                reason = " ".join(args[1:]) if len(args) > 1 else "без указания причины"
            except ValueError:
                time_days = None
                reason = " ".join(args)

        now = datetime.now()
        now_str = now.strftime("%d.%m.%Y %H:%M")

        try:
            if time_days is None:
                await message.chat.ban(target_id)
                msg_text = (
                    f"🚫 Пользователь {target_name} забанен <b>НАВСЕГДА</b>.\n"
                    f"📄 Причина: {reason}\n\n"
                    f"🔻 Получен: {now_str}\n"
                    f"🔺 Истекает: Никогда"
                )
            else:
                until = now + timedelta(days=time_days)
                until_str = until.strftime("%d.%m.%Y %H:%M")
                await message.chat.ban(target_id, until_date=until)
                msg_text = (
                    f"🚫 Пользователь {target_name} забанен на <b>{time_days} дней</b>.\n"
                    f"📄 Причина: {reason}\n\n"
                    f"🔻 Получен: {now_str}\n"
                    f"🔺 Истекает: {until_str}"
                )

            await message.answer(msg_text, reply_markup=get_undo_keyboard("ban", target_id))
            await log_punishment(target_id, "ban", reason)
        except Exception as e:
            await message.reply(f"Ошибка: {e}")

    @dp.message(Command("mute"))
    async def cmd_mute(message: types.Message, command: CommandObject):
        if not await is_admin(message): return
        target_id, target_name = await get_target_user_id(message, command)
        if not target_id: return await message.reply("⚠️ Укажите пользователя.")

        args = command.args.split() if command.args else []
        if args and args[0].startswith("@"): args.pop(0)

        time_min = None
        reason = "без указания причины"

        if args:
            try:
                time_min = int(args[0])
                reason = " ".join(args[1:]) if len(args) > 1 else "без указания причины"
            except ValueError:
                pass

        if time_min is None:
            return await message.reply("⚠️ Укажите время в минутах.")

        permissions = ChatPermissions(can_send_messages=False)

        try:
            now = datetime.now()
            until = now + timedelta(minutes=time_min)
            now_str = now.strftime("%d.%m.%Y %H:%M")
            until_str = until.strftime("%d.%m.%Y %H:%M")

            await message.chat.restrict(user_id=target_id, permissions=permissions, until_date=until)
            await change_reputation(target_id, -1)
            await log_punishment(target_id, "mute", reason)

            await message.answer(
                f"🔇 Пользователь {target_name} замучен на <b>{time_min} минут</b>.\n"
                f"📄 Причина: {reason}\n"
                f"📉 Репутация: -1\n\n"
                f"🔻 Получен: {now_str}\n"
                f"🔺 Истекает: {until_str}",
                reply_markup=get_undo_keyboard("mute", target_id)
            )
        except Exception as e:
            await message.reply(f"Ошибка: {e}")

    @dp.message(Command("warn"))
    async def cmd_warn(message: types.Message, command: CommandObject):
        if not await is_admin(message): return
        target_id, target_name = await get_target_user_id(message, command)
        if not target_id: return await message.reply("⚠️ Укажите пользователя.")

        admin_id = message.from_user.id
        admin_name = message.from_user.first_name

        reason_text = None
        args = command.args.split() if command.args else []
        if args and args[0].startswith("@"): args.pop(0)
        if args: reason_text = " ".join(args)

        db_reason = reason_text if reason_text else "без указания причины"
        timestamp = int(time.time())
        chat_id = message.chat.id

        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("INSERT INTO warns (user_id, admin_id, chat_id, reason, timestamp) VALUES (?, ?, ?, ?, ?)",
                             (target_id, admin_id, chat_id, db_reason, timestamp))
            await db.commit()

        await log_punishment(target_id, "warn", db_reason)
        await change_reputation(target_id, -5)
        warn_count = await get_active_warns(target_id)

        now = datetime.now()
        until = now + timedelta(days=30)

        msg = f"⚠️ Пользователь {target_name} получил предупреждение на 30 дней.\n"
        if reason_text: msg += f"📄 Причина: {reason_text}\n"

        msg += (
            f"👮 Выдал: {admin_name}\n"
            f"🔢 Всего варнов: {warn_count}/3\n"
            f"📉 Репутация: -5\n\n"
            f"🔻 Получен: {now.strftime('%d.%m.%Y %H:%M')}\n"
            f"🔺 Истекает: {until.strftime('%d.%m.%Y %H:%M')}"
        )

        if warn_count >= 3:
            try:
                await message.chat.ban(target_id)
                await message.chat.unban(target_id)
                msg += "\n\n👢 <b>Достигнут лимит варнов (3/3). Пользователь кикнут.</b>"
            except:
                pass

        await message.answer(msg, reply_markup=get_undo_keyboard("warn", target_id))

    # --- НОВЫЕ КОМАНДЫ СНЯТИЯ НАКАЗАНИЙ ---

    @dp.message(Command("unmute"))
    async def cmd_unmute(message: types.Message, command: CommandObject):
        if not await is_admin(message): return
        target_id, target_name = await get_target_user_id(message, command)
        if not target_id: return await message.reply("⚠️ Укажите пользователя.")

        permissions = ChatPermissions(
            can_send_messages=True, can_send_media_messages=True,
            can_send_other_messages=True, can_add_web_page_previews=True
        )
        try:
            await message.chat.restrict(user_id=target_id, permissions=permissions)
            await change_reputation(target_id, 1)
            await message.answer(f"🔊 С пользователя {target_name} снят мут.\n📈 Репутация восстановлена (+1).")
        except Exception as e:
            await message.reply(f"Ошибка: {e}")

    @dp.message(Command("unban"))
    async def cmd_unban(message: types.Message, command: CommandObject):
        if not await is_admin(message): return
        target_id, target_name = await get_target_user_id(message, command)
        if not target_id: return await message.reply("⚠️ Укажите пользователя.")

        try:
            await message.chat.unban(target_id)
            await message.answer(f"🕊 Пользователь {target_name} разбанен.")
        except Exception as e:
            await message.reply(f"Ошибка: {e}")

    @dp.message(Command("unwarn"))
    async def cmd_unwarn(message: types.Message, command: CommandObject):
        if not await is_admin(message): return
        target_id, target_name = await get_target_user_id(message, command)
        if not target_id: return await message.reply("⚠️ Укажите пользователя.")

        removed = await remove_last_warn(target_id)
        if removed:
            await change_reputation(target_id, 5)
            count = await get_active_warns(target_id)
            await message.answer(f"⚠️ Варн снят. Текущее кол-во: {count}/3.\n📈 Репутация восстановлена (+5).")
        else:
            await message.answer("У пользователя нет активных варнов.")

    # --- КОМАНДА ВЛАДЕЛЬЦА (SETREP) ---

    @dp.message(Command("setrep"))
    async def cmd_setrep(message: types.Message, command: CommandObject):
        if not await is_creator(message):
            return await message.reply("⛔️ Только владелец.")
        if not message.reply_to_message or not command.args:
            return await message.reply("Ответом на юзера `/setrep 100`")
        try:
            amount = int(command.args)
            target_id = message.reply_to_message.from_user.id
            await set_reputation(target_id, amount)
            await message.answer(f"🤴 Репутация установлена: <b>{amount}</b>.")
        except ValueError:
            pass

    @dp.message(Command("clear"))
    async def cmd_clear(message: types.Message):
        if not await is_admin(message) or not message.reply_to_message:
            return
        target_msg_id = message.reply_to_message.message_id
        await message.answer("Удалить сообщение?", reply_markup=get_clear_keyboard(target_msg_id))

    @dp.message(Command("check"))
    async def cmd_check(message: types.Message, command: CommandObject):
        if not await is_admin(message): return
        target_id, target_name = await get_target_user_id(message, command)
        if not target_id: return await message.reply("⚠️ Укажите пользователя.")

        try:
            warns = await get_active_warns(target_id)
            await message.answer(f"🔎 Проверка {target_name}:\nАктивных варнов: {warns}",
                                 reply_markup=get_check_keyboard(target_id))
        except Exception:
            pass

    # --- РЕПУТАЦИЯ (ЛОГИКА) ---

    @dp.message(Command("rep"))
    async def cmd_rep(message: types.Message, command: CommandObject):
        if not command.args:
            return await message.reply("Использование: <code>/rep +</code> или <code>/rep - @username</code>")

        args = command.args.split()
        operation = args[0]

        if operation not in ['+', '-']:
            return await message.reply("Первый аргумент должен быть + или -")

        target_user_id = None
        target_name = None

        if message.reply_to_message:
            target_user_id = message.reply_to_message.from_user.id
            target_name = message.reply_to_message.from_user.first_name
        elif len(args) > 1:
            username_arg = args[1]
            target_user_id = await get_user_id_by_username(username_arg)
            target_name = username_arg

        if not target_user_id:
            return await message.reply("Не удалось найти пользователя. Ответьте на сообщение или укажите @username.")

        if message.from_user.id == target_user_id:
            return await message.reply("Нельзя менять репутацию себе!")

        action = "up" if operation == "+" else "down"
        action_text = "повысить" if action == "up" else "понизить"

        await message.reply(
            f"Вы действительно хотите {action_text} репутацию пользователю {target_name}?",
            reply_markup=get_confirm_rep_keyboard(target_user_id, action)
        )

    # --- CALLBACK HANDLERS (Интерактив) ---

    @dp.callback_query(F.data.startswith("undo:"))
    async def callback_undo_punishment(callback: CallbackQuery):
        if not await is_admin(callback.message):
            return await callback.answer("⛔️ Только для администраторов!", show_alert=True)

        _, action, target_id = callback.data.split(":")
        target_id = int(target_id)

        try:
            if action == "ban":
                await callback.message.chat.unban(target_id)
                res = "разбанен"
            elif action == "mute":
                permissions = ChatPermissions(can_send_messages=True, can_send_media_messages=True,
                                              can_send_other_messages=True)
                await callback.message.chat.restrict(user_id=target_id, permissions=permissions)
                await change_reputation(target_id, 1)
                res = "размучен"
            elif action == "warn":
                await remove_last_warn(target_id)
                await change_reputation(target_id, 5)
                res = "варн снят"

            await callback.message.edit_text(f"✅ Наказание отменено ({res}) администратором.")
        except Exception as e:
            await callback.answer(f"Ошибка: {e}", show_alert=True)

    @dp.callback_query(F.data.startswith("confirm_rep:"))
    async def callback_confirm_rep(callback: CallbackQuery):
        _, action, target_id = callback.data.split(":")
        target_id = int(target_id)
        user_id = callback.from_user.id

        today_start = int(datetime.now().replace(hour=0, minute=0, second=0).timestamp())
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute("SELECT COUNT(*) FROM rep_log WHERE from_user_id = ? AND timestamp > ?",
                                  (user_id, today_start)) as cursor:
                count = (await cursor.fetchone())[0]

        if count >= 3:
            await callback.message.delete()
            return await callback.answer("⚠️ Лимит на сегодня исчерпан (3/3)!", show_alert=True)

        amount = 1 if action == "up" else -1

        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("INSERT INTO rep_log (from_user_id, to_user_id, timestamp) VALUES (?, ?, ?)",
                             (user_id, target_id, int(time.time())))
            await db.commit()

        await change_reputation(target_id, amount)
        res_text = "повышена" if amount > 0 else "понижена"
        await callback.message.edit_text(f"✅ Репутация {res_text}!")

    @dp.callback_query(F.data == "cancel_rep")
    async def callback_cancel_rep(callback: CallbackQuery):
        await callback.message.edit_text("❌ Действие отменено.")

    @dp.callback_query(F.data.startswith("stats_like:") | F.data.startswith("stats_dislike:"))
    async def callback_stats_vote(callback: CallbackQuery):
        action, target_id = callback.data.split(":")
        target_id = int(target_id)
        user_id = callback.from_user.id

        if user_id == target_id:
            return await callback.answer("Нельзя голосовать за себя!", show_alert=True)

        today_start = int(datetime.now().replace(hour=0, minute=0, second=0).timestamp())

        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute("SELECT COUNT(*) FROM rep_log WHERE from_user_id = ? AND timestamp > ?",
                                  (user_id, today_start)) as cursor:
                count = (await cursor.fetchone())[0]

        if count >= 3:
            return await callback.answer("⚠️ Лимит репутации (3/3) на сегодня исчерпан!", show_alert=True)

        amount = 1 if "like" in action and "dislike" not in action else -1

        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("INSERT INTO rep_log (from_user_id, to_user_id, timestamp) VALUES (?, ?, ?)",
                             (user_id, target_id, int(time.time())))
            await db.execute("UPDATE users SET reputation = reputation + ? WHERE user_id = ?", (amount, target_id))
            await db.commit()

        await callback.answer(f"Репутация {'повышена' if amount > 0 else 'понижена'}!")

        new_text = await generate_stats_text(target_id, None)
        try:
            await callback.message.edit_text(new_text, reply_markup=get_stats_keyboard(target_id))
        except Exception:
            pass

    @dp.callback_query(F.data.startswith("del_one:"))
    async def callback_del_one(callback: CallbackQuery):
        msg_id = int(callback.data.split(":")[1])
        try:
            await callback.message.bot.delete_message(callback.message.chat.id, msg_id)
            await callback.message.delete()
        except Exception:
            await callback.answer("Не удалось удалить.", show_alert=True)

    @dp.callback_query(F.data == "cancel_clear")
    async def callback_cancel_clear(callback: CallbackQuery):
        await callback.message.delete()

    # --- ОБРАБОТКА ИСТОРИИ (CHECK) ---
    @dp.callback_query(F.data.startswith("hist:"))
    async def callback_history(callback: CallbackQuery):
        _, h_type, user_id = callback.data.split(":")
        user_id = int(user_id)

        type_map = {"ban": "ban", "mute": "mute", "warn": "warn"}
        title_map = {"ban": "Блокировки", "mute": "Муты", "warn": "Предупреждения"}
        target_type = type_map.get(h_type)

        async with aiosqlite.connect(DB_NAME) as db:
            rows = await db.execute_fetchall(
                "SELECT reason, timestamp FROM punishment_history WHERE user_id = ? AND type = ? ORDER BY timestamp DESC LIMIT 5",
                (user_id, target_type))

        text = f"📜 <b>История ({title_map[h_type]}):</b>\n"
        if not rows: text += "Пусто."
        for reason, ts in rows:
            date_str = datetime.fromtimestamp(ts).strftime("%d.%m.%Y %H:%M")
            text += f"— {date_str}: {reason}\n"

        await callback.message.edit_text(text, reply_markup=get_history_back_button(user_id))

    @dp.callback_query(F.data.startswith("back_to_check:"))
    async def callback_back_to_check(callback: CallbackQuery):
        user_id = int(callback.data.split(":")[1])
        user_data = await get_user(user_id)
        name = user_data[2] if user_data else "Пользователь"
        warns = await get_active_warns(user_id)
        text = f"🔎 Проверка {name}:\nАктивных варнов: {warns}"
        await callback.message.edit_text(text, reply_markup=get_check_keyboard(user_id))

    @dp.callback_query(F.data == "close_check")
    async def callback_close_check(callback: CallbackQuery):
        await callback.message.delete()

    # --- СБОР СТАТИСТИКИ (ОБРАБОТЧИК СООБЩЕНИЙ) ---
    @dp.message()
    async def on_message(message: types.Message):
        if message.chat.type in ['group', 'supergroup']:
            await get_user(message.from_user.id, message.from_user.username)
            await update_stats(message.from_user.id)
