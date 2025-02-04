import logging
from telegram import Update
from telegram.ext import Application, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from typing import Callable
import json

class TelegramBot:
    application: Application
    action: Callable
    
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    def __init__(self, token: str, api: str = "https://api.telegram.org/bot"):
        self.application = ApplicationBuilder().base_url(api).token(token).build()

        normal_handler = MessageHandler(filters.COMMAND, lambda upd, ctx: self.action(upd, ctx))
        self.application.add_handler(normal_handler)
        self.actions = []
    
    def run(self):
        self.application.run_polling()