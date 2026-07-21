from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

import os
import json
import gspread

from google.oauth2.service_account import Credentials

BOT_TOKEN = os.getenv("BOT_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

SQUADRA = "Zio Barrett - Gwine"

MENU = ReplyKeyboardMarkup(
    [
        ["🏆 Classifica", "📅 Calendario"],
        ["⚽ Prossima Partita", "👥 Rosa"],
        ["🚑 Indisponibili"]
    ],
    resize_keyboard=True
)

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
        "⚽ Benvenuto nel Bot del Torneo",
        reply_markup=MENU
    )


# ==================================
# ROSA
# ==================================

async def mostra_rosa(update):

    ws = sheet.worksheet("ROSA")
    dati = ws.get_all_records()

    testo = "👥 ROSA ZIO BARRETT - GWINE\n\n"

    for r in dati:
        testo += f"{r['NR']} - {r['NOME']}\n"

    await update.message.reply_text(testo)


# ==================================
# INDISPONIBILI
# ==================================

async def mostra_indisponibili(update):

    ws = sheet.worksheet("STATO ROSA")

    dati = ws.get_all_records()

    testo = "🚑 INDISPONIBILI\n\n"

    trovati = False

    for r in dati:

        stato = str(r["STATO"]).strip().lower()

        if stato != "disponibile":

            trovati = True

            testo += (
                f"👤 {r['NOME']}\n"
                f"📌 {r['STATO']}\n"
                f"📝 {r['NOTE']}\n\n"
            )

    if not trovati:
        testo = "✅ Nessun indisponibile"

    await update.message.reply_text(testo)


# ==================================
# CALENDARIO DELLA SQUADRA
# ==================================

async def mostra_calendario(update):

    ws = sheet.worksheet("CALENDARIO")

    dati = ws.get_all_records()

    testo = "📅 CALENDARIO ZIO BARRETT - GWINE\n\n"

    count = 0

    for partita in dati:

        casa = str(partita["CASA"]).strip()
        trasferta = str(partita["TRASFERTA"]).strip()

        if casa == SQUADRA or trasferta == SQUADRA:

            count += 1

            testo += (
                f"📅 {partita['DATA']}\n"
                f"🕒 {partita['ORA']}:00\n"
                f"⚽ {casa} vs {trasferta}\n"
                f"🏟 {partita['CAMPO']}\n\n"
            )

    if count == 0:
        testo = "Nessuna partita trovata."

    await update.message.reply_text(testo)


# ==================================
# PROSSIMA GIORNATA
# ==================================

from datetime import datetime

async def mostra_prossima(update):

    ws = sheet.worksheet("CALENDARIO")

    dati = ws.get_all_records()

    oggi = "21/07/2026"

    testo = f"⚽ PARTITE DI OGGI ({oggi})\n\n"

    trovate = 0

    for partita in dati:

        data_partita = str(partita["DATA"]).strip()

        if data_partita == oggi:

            trovate += 1

            testo += (
                f"🕒 {partita['ORA']}:00\n"
                f"⚽ {partita['CASA']} vs {partita['TRASFERTA']}\n"
                f"🏟 {partita['CAMPO']}\n\n"
            )

    if trovate == 0:

        testo = (
            f"❌ Nessuna partita trovata per il {oggi}"
        )

    await update.message.reply_text(testo)

# ==================================
# CLASSIFICA
# ==================================

async def mostra_classifica(update):

    ws_squadre = sheet.worksheet("SQUADRE")
    ws_calendario = sheet.worksheet("CALENDARIO")
    ws_risultati = sheet.worksheet("RISULTATI")

    squadre = ws_squadre.get_all_records()
    calendario = ws_calendario.get_all_records()
    risultati = ws_risultati.get_all_records()

    classifica = {}

    for squadra in squadre:

        nome = str(
            squadra["Nome Squadra"]
        ).strip()

        classifica[nome] = {
            "PT": 0,
            "PG": 0,
            "GF": 0,
            "GS": 0
        }

    calendario_map = {}

    for partita in calendario:

        calendario_map[
            str(partita["ID PARTITA"])
        ] = partita

    for risultato in risultati:

        try:

            id_partita = str(
                risultato["ID PARTITA"]
            )

            if id_partita not in calendario_map:
                continue

            partita = calendario_map[id_partita]

            casa = str(
                partita["CASA"]
            ).strip()

            trasferta = str(
                partita["TRASFERTA"]
            ).strip()

            gc = int(risultato["GOL CASA"])
            gt = int(risultato["GOL TRASFERTA"])

            if casa not in classifica:
                continue

            if trasferta not in classifica:
                continue

            classifica[casa]["PG"] += 1
            classifica[trasferta]["PG"] += 1

            classifica[casa]["GF"] += gc
            classifica[casa]["GS"] += gt

            classifica[trasferta]["GF"] += gt
            classifica[trasferta]["GS"] += gc

            if gc > gt:

                classifica[casa]["PT"] += 3

            elif gt > gc:

                classifica[trasferta]["PT"] += 3

            else:

                classifica[casa]["PT"] += 1
                classifica[trasferta]["PT"] += 1

        except Exception as e:

            print("Errore Classifica:", e)

    classifica_ordinata = sorted(
        classifica.items(),
        key=lambda x: (
            x[1]["PT"],
            (x[1]["GF"] - x[1]["GS"]),
            x[1]["GF"]
        ),
        reverse=True
    )

    testo = "🏆 CLASSIFICA TORNEO\n\n"

    posizione = 1

    for nome, stats in classifica_ordinata:

        dr = stats["GF"] - stats["GS"]

        playoff = "✅ " if posizione <= 8 else ""

        testo += (
            f"{playoff}{posizione}. {nome}\n"
            f"🏅 {stats['PT']} pt | "
            f"🎮 {stats['PG']} pg | "
            f"⚽ {stats['GF']} gf | "
            f"🥅 {stats['GS']} gs | "
            f"📊 {dr}\n\n"
        )

        posizione += 1

    await update.message.reply_text(testo)


# ==================================
# MENU
# ==================================

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "👥 Rosa":

        await mostra_rosa(update)

    elif text == "🚑 Indisponibili":

        await mostra_indisponibili(update)

    elif text == "📅 Calendario":

        await mostra_calendario(update)

    elif text == "⚽ Prossima Partita":

        await mostra_prossima(update)

    elif text == "🏆 Classifica":

        await mostra_classifica(update)


# ==================================
# AVVIO
# ==================================

if __name__ == "__main__":

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            menu
        )
    )

    print("Bot avviato...")

    app.run_polling()
