from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

MENU = ReplyKeyboardMarkup(
    [
        ["🏆 Classifica", "📅 Calendario"],
        ["⚽ Prossima Partita", "👥 Rosa"],
        ["🚑 Indisponibili"]
    ],
    resize_keyboard=True
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Benvenuto nel FC Roccaraso Bot!",
        reply_markup=MENU
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🏆 Classifica":
        await update.message.reply_text("Funzione classifica in preparazione.")

    elif text == "📅 Calendario":
        await update.message.reply_text("Funzione calendario in preparazione.")

    elif text == "⚽ Prossima Partita":
        await update.message.reply_text("Funzione prossima partita in preparazione.")

    elif text == "👥 Rosa":
        await update.message.reply_text("Funzione rosa in preparazione.")

    elif text == "🚑 Indisponibili":
        await update.message.reply_text("Funzione indisponibili in preparazione.")

    else:
        await update.message.reply_text("Seleziona una voce dal menu.")

if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, menu)
    )

    app.run_polling()
