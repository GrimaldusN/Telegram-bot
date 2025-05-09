import time
from collections import defaultdict
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

# user_id -> {function_name: last_used_time}
user_command_timestamps = defaultdict(dict)

def rate_limited(seconds: int = 5):
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id
            func_name = func.__name__
            now = time.time()

            last_used = user_command_timestamps[user_id].get(func_name, 0)
            if now - last_used < seconds:
                wait = int(seconds - (now - last_used))
                msg = f"⏳ Подождите {wait} сек перед повторным использованием команды."
                if update.message:
                    await update.message.reply_text(msg)
                elif update.callback_query:
                    await update.callback_query.answer(msg, show_alert=True)
                return

            user_command_timestamps[user_id][func_name] = now
            return await func(update, context, *args, **kwargs)

        return wrapper
    return decorator
