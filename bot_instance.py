# load telebot libs
from telebot import TeleBot
from telebot import ExceptionHandler as BaseExceptionHandler
from telebot import apihelper

# set up warp connect proxy
apihelper.proxy = {
    'https': 'socks5h://127.0.0.1:40000'
}

# load config
from config import BOT_TOKEN, ADMIN

# handler for exceptions
class ExceptionHandler(BaseExceptionHandler):
    def handle(self, exception):
        bot.send_message(ADMIN, f"ERROR!!!\n\n{exception}")
        return True
handler = ExceptionHandler()

# init bot var
bot = TeleBot(BOT_TOKEN, exception_handler=handler)