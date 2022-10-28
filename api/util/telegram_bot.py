from telegram.ext import Updater


def send_telegram_message(token: str, chat_id: any, message: str):
    """Sends a message to a telegram chat."""
    if token and chat_id and message:
        updater = Updater(token=token, use_context=True)
        updater.bot.send_message(chat_id=chat_id, text=message)
    else:
        raise ValueError("Token, chat_id and message must be set.")
        # print("Invalid token, chat or message")
