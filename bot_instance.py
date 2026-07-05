# load telebot libs
from telebot import TeleBot
from telebot import ExceptionHandler as BaseExceptionHandler

# load config
from config import BOT_TOKEN, ADMIN


class ExceptionHandler(BaseExceptionHandler):
    def handle(self, exception):
        bot.send_message(ADMIN, f"ERROR!!!\n\n{exception}")
        return True
handler = ExceptionHandler()

bot = TeleBot(BOT_TOKEN, exception_handler=handler)