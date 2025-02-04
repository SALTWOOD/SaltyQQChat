import logging
from telegram import Update
from telegram.ext import Application, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from typing import Callable
import json

class TelegramBot:
    application: Application
    actions: list[Callable]
    
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    async def match(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        for i in self.actions:
            i(update, context)

    def __init__(self, token: str, api: str = "https://api.telegram.org/bot"):
        self.application = ApplicationBuilder().base_url(api).token(token).build()

        normal_handler = MessageHandler(filters.COMMAND, self.match)
        self.application.add_handler(normal_handler)
        self.actions = []
    
    def run(self):
        self.application.run_polling()