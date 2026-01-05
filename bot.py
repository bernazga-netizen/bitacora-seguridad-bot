import os
import requests
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackContext

BOT_TOKEN = os.environ.get("BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def usuario_autorizado(telegram_id: int):
    url = f"{SUPABASE_URL}/rest/v1/usuarios?telegram_id=eq.{telegram_id}&activo=eq.true"
    r = requests.get(url, headers=HEADERS)
    return r.status_code == 200 and len(r.json()) > 0

def start(update: Update, context: CallbackContext):
    telegram_id = update.effective_user.id

    if not usuario_autorizado(telegram_id):
        update.message.reply_text(
            "⛔ Acceso no autorizado.\n"
            "Contacta al administrador."
        )
        return

    keyboard = [
        ["📍 Acceso Tierra (Base 1)"],
        ["🚤 Acceso Marina"],
        ["🚨 Incidencia"],
        ["🔄 Rondín"],
        ["🧑‍✈️ Supervisión"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    update.message.reply_text(
        "✅ Acceso autorizado\n\n"
        "Bitácora de Seguridad\nSelecciona una opción:",
        reply_markup=reply_markup
    )

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    print("BOT INICIADO CORRECTAMENTE")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

