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
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

SQUADRA = "FC Roccaraso"

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
    "https://www.googleapis.com/auth/drive",
]

creds = Credentials.from_service_account_info(
    credentials_dict,
    scopes=scopes
)

client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID)

# --------------------
# START
# --------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ Benvenuto nel Bot del Torneo",
        reply_markup=MENU
    )

# --------------------
# ROSA
# --------------------

async def mostra_rosa(update):

    ws = sheet.worksheet("ROSA")

    dati = ws.get_all_records()

    testo = "👥 ROSA ZIO BARRETT-GWINE\n\n"

    for r in dati:
        testo += f"{r['NR']} - {r['NOME']}\n"

    await update.message.reply_text(testo)

# --------------------
# INDISPONIBILI
# --------------------

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

# --------------------
# CALENDARIO
# --------------------

async def mostra_calendario(update):

    ws = sheet.worksheet("CALENDARIO")

    dati = ws.get_all_records()

    testo = "📅 CALENDARIO ZIO BARRETT-GWINE\n\n"

    trovate = 0

    for partita in dati:

        casa = partita["CASA"]
        trasferta = partita["TRASFERTA"]

        if SQUADRA in (casa, trasferta):

            trovate += 1

            testo += (
                f"📅 {partita['DATA']} {partita['ORA']}\n"
                f"{casa} vs {trasferta}\n"
                f"🏟 {partita['CAMPO']}\n\n"
            )

    if trovate == 0:
        testo = "Nessuna partita trovata."

    await update.message.reply_text(testo)

# --------------------
# PROSSIMA PARTITA
# --------------------

async def mostra_prossima(update):

    ws = sheet.worksheet("CALENDARIO")

    dati = ws.get_all_records()

    prossima = None

    oggi = datetime.now()

    for partita in dati:

        casa = partita["CASA"]
        trasferta = partita["TRASFERTA"]

        if SQUADRA not in (casa, trasferta):
            continue

        try:

            data_partita = datetime.strptime(
                partita["DATA"],
                "%d/%m/%Y"
            )

            if data_partita >= oggi:

                if prossima is None:
                    prossima = partita

                elif data_partita < datetime.strptime(
                    prossima["DATA"],
                    "%d/%m/%Y"
                ):
                    prossima = partita

        except:
            pass

    if prossima:

        testo = (
            "⚽ PROSSIMA PARTITA\n\n"
            f"{prossima['CASA']} vs {prossima['TRASFERTA']}\n\n"
            f"📅 {prossima['DATA']}\n"
            f"🕒 {prossima['ORA']}\n"
            f"🏟 {prossima['CAMPO']}"
        )

    else:
        testo = "Nessuna partita futura trovata."

    await update.message.reply_text(testo)

# --------------------
# CLASSIFICA
# --------------------

async def mostra_classifica(update):

    squadre_ws = sheet.worksheet("SQUADRE")
    risultati_ws = sheet.worksheet("RISULTATI")
    calendario_ws = sheet.worksheet("CALENDARIO")

    squadre = squadre_ws.get_all_records()
    risultati = risultati_ws.get_all_records()
    calendario = calendario_ws.get_all_records()

    classifica = {}

    for s in squadre:

        nome = s["Nome Squadra"]

        classifica[nome] = {
            "PT": 0,
            "GF": 0,
            "GS": 0,
            "V": 0,
            "N": 0,
            "P": 0,
            "PG": 0,
        }

    calendario_map = {}

    for p in calendario:

        calendario_map[str(p["ID PARTITA"])] = p

    for r in risultati:

        idp = str(r["ID PARTITA"])

        if idp not in calendario_map:
            continue

        partita = calendario_map[idp]

        casa = partita["CASA"]
        trasferta = partita["TRASFERTA"]

        gc = int(r["GOL CASA"])
        gt = int(r["GOL TRASFERTA"])

        classifica[casa]["PG"] += 1
        classifica[trasferta]["PG"] += 1

        classifica[casa]["GF"] += gc
        classifica[casa]["GS"] += gt

        classifica[trasferta]["GF"] += gt
        classifica[trasferta]["GS"] += gc

        if gc > gt:

            classifica[casa]["PT"] += 3
            classifica[casa]["V"] += 1

            classifica[trasferta]["P"] += 1

        elif gc < gt:

            classifica[trasferta]["PT"] += 3
            classifica[trasferta]["V"] += 1

            classifica[casa]["P"] += 1

        else:

            classifica[casa]["PT"] += 1
            classifica[trasferta]["PT"] += 1

            classifica[casa]["N"] += 1
            classifica[trasferta]["N"] += 1

    ordinate = sorted(
        classifica.items(),
        key=lambda x: (
            x[1]["PT"],
            x[1]["GF"] - x[1]["GS"],
            x[1]["GF"]
        ),
        reverse=True
    )

    testo = "🏆 CLASSIFICA\n\n"

    pos = 1

    for nome, stat in ordinate:

        dr = stat["GF"] - stat["GS"]

        testo += (
            f"{pos}. {nome}\n"
            f"PT:{stat['PT']} "
            f"PG:{stat['PG']} "
            f"DR:{dr}\n\n"
        )

        pos += 1

    await update.message.reply_text(testo)

# --------------------
# MENU
# --------------------

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

# --------------------
# AVVIO
# --------------------

if __name__ == "__main__":

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, menu)
    )

    app.run_polling()
