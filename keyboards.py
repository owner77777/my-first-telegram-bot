from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_stats_keyboard(target_user_id):
    # ... (Ваша функция get_stats_keyboard)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👍", callback_data=f"stats_like:{target_user_id}"),
            InlineKeyboardButton(text="👎", callback_data=f"stats_dislike:{target_user_id}")
        ]
    ])
    return kb


def get_undo_keyboard(action, target_user_id):
    # ... (Ваша функция get_undo_keyboard)
    action_map = {
        "mute": "🔊 Снять мут",
        "warn": "🛡 Снять варн",
        "ban": "🕊 Разбанить"
    }
    text = action_map.get(action, "Отменить")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data=f"undo:{action}:{target_user_id}")]
    ])
    return kb


# ... (Остальные функции get_confirm_rep_keyboard, get_clear_keyboard и т.д. переносим сюда)
def get_confirm_rep_keyboard(target_user_id, action):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_rep:{action}:{target_user_id}"),
            InlineKeyboardButton(text="❌ Нет", callback_data=f"cancel_rep")
        ]
    ])
    return kb


def get_clear_keyboard(msg_id):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 Удалить это сообщение", callback_data=f"del_one:{msg_id}")],
        [InlineKeyboardButton(text="🔙 Отмена", callback_data="cancel_clear")]
    ])
    return kb


def get_check_keyboard(user_id):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📜 История блокировок", callback_data=f"hist:ban:{user_id}")],
        [InlineKeyboardButton(text="🔇 История мутов", callback_data=f"hist:mute:{user_id}")],
        [InlineKeyboardButton(text="⚠️ История варнов", callback_data=f"hist:warn:{user_id}")],
        [InlineKeyboardButton(text="🔙 Закрыть", callback_data="close_check")]
    ])
    return kb


def get_info_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Сообщество в ВК", url="https://vk.com/bu_chilli"),
            InlineKeyboardButton(text="Чат в ВК", url="https://vk.me/join/p7URv1PMqAiLIo0rBx6JdY9/oxOTQcYuiqA="),
        ],
        [
            InlineKeyboardButton(text="💎 Услуги", url="t.me/bu_chilli_shop")
        ]
    ])
    return kb


def get_help_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👮 Помощь модераторам", callback_data="help_mod")]
    ])
    return kb


def get_help_mod_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="help_back")]
    ])
    return kb


def get_top_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Топ по сообщениям", callback_data="top:msgs")],
        [InlineKeyboardButton(text="🌟 Топ по репутации", callback_data="top:rep")]
    ])
    return kb


def get_history_back_button(user_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_check:{user_id}")]])

