from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import os
import json
import gspread
from google.oauth2.service_account import Credentials

BOT_TOKEN = os.getenv("BOT_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

MENU = ReplyKeyboardMarkup(
    [
        ["🏆 Classifica", "📅 Calendario"],
        ["⚽ Prossima Partita", "👥 Rosa"],
        ["🚑 Indisponibili"]
    ],
    resize_keyboard=True
)

# Connessione Google Sheets
credentials_dict = json.loads(GOOGLE_CREDENTIALS)

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    credentials_dict,
    scopes=scopes
)

client = gspread.authorize(creds)

sheet = client.open_by_key(SPREADSHEET_ID)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ Benvenuto nel Bot del Torneo!",
        reply_markup=MENU
    )

async def mostra_rosa(update: Update):
    worksheet = sheet.worksheet("ROSA")

    dati = worksheet.get_all_records()

    testo = "👥 ROSA FC ROCCARASO\n\n"

    for giocatore in dati:
        testo += f"{giocatore['NR']} - {giocatore['NOME']}\n"

    await update.message.reply_text(testo)

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "👥 Rosa":
        await mostra_rosa(update)

    elif text == "🏆 Classifica":
        await update.message.reply_text("Classifica in sviluppo")

    elif text == "📅 Calendario":
        await update.message.reply_text("Calendario in sviluppo")

    elif text == "⚽ Prossima Partita":
        await update.message.reply_text("Prossima partita in sviluppo")

    elif text == "🚑 Indisponibili":
        await update.message.reply_text("Indisponibili in sviluppo")

if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, menu)
    )

    app.run_polling()
