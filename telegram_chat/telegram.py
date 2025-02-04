import logging
from telegram import Update
from telegram.ext import Application, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from typing import Callable
import asyncio

class TelegramBot:
    application: Application
    action: Callable
    
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        stream=open(f"logs/telegram.log", "w")
    )

    def __init__(self, token: str, api: str = "https://api.telegram.org/bot"):
        self.application = ApplicationBuilder().base_url(api).token(token).build()

        normal_handler = MessageHandler(filters.COMMAND, lambda upd, ctx: self.action(upd, ctx))
        self.application.add_handler(normal_handler)
        self.actions = []
    
    def run(self):
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        _ = self.application.run_polling()