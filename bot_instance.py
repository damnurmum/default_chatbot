# tg engine room
from telebot import TeleBot
from telebot import ExceptionHandler as BaseExceptionHandler
from telebot import apihelper

# bring in the essentials
from config import BOT_TOKEN, ADMIN

# if something explodes, the admin hears about it first
class ExceptionHandler(BaseExceptionHandler):
    # forward the crash to the admin and keep polling alive
    def handle(self, exception):
        bot.send_message(ADMIN, f"ERROR!!!\n\n{exception}")
        return True

# one handler instance for the whole bot lifetime
handler = ExceptionHandler()

# wake the bot up
bot = TeleBot(BOT_TOKEN, exception_handler=handler)
