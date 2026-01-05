import os
import requests
from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext
)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# ====== UTILIDADES ======

def usuario_autorizado(telegram_id: int):
    url = f"{SUPABASE_URL}/rest/v1/usuarios?telegram_id=eq.{telegram_id}&activo=eq.true"
    r = requests.get(url, headers=HEADERS)
    return r.status_code == 200 and len(r.json()) > 0

def guardar_acceso_tierra(data: dict):
    url = f"{SUPABASE_URL}/rest/v1/accesos_tierra"
    r = requests.post(url, headers=HEADERS, json=data)
    return r.status_code in (200, 201)

# ====== ESTADOS ======
ESPERANDO_FOTO = 1
ESPERANDO_PLACAS = 2
ESPERANDO_TIPO = 3

# ====== COMANDOS ======

def start(update: Update, context: CallbackContext):
    telegram_id = update.effective_user.id

    if not usuario_autorizado(telegram_id):
        update.message.reply_text("⛔ Acceso no autorizado.")
        return

    keyboard = [
        ["📍 Acceso Tierra (Base 1)"],
        ["🚤 Acceso Marina"],
        ["🚨 Incidencia"],
        ["🔄 Rondín"],
        ["🧑‍✈️ Supervisión"]
    ]

    update.message.reply_text(
        "✅ Acceso autorizado\nSelecciona una opción:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

def acceso_tierra(update: Update, context: CallbackContext):
    context.user_data.clear()
    update.message.reply_text(
        "📸 Envía la FOTO del vehículo",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data["estado"] = ESPERANDO_FOTO

# ====== MANEJO DE MENSAJES ======

def manejar_mensajes(update: Update, context: CallbackContext):
    estado = context.user_data.get("estado")

    if estado == ESPERANDO_FOTO:
        if not update.message.photo:
            update.message.reply_text("❗ Envía una FOTO, por favor.")
            return
        context.user_data["foto_file_id"] = update.message.photo[-1].file_id
        update.message.reply_text("🔤 Ingresa las PLACAS del vehículo:")
        context.user_data["estado"] = ESPERANDO_PLACAS

    elif estado == ESPERANDO_PLACAS:
        context.user_data["placas"] = update.message.text
        keyboard = [
            ["Residente"],
            ["Invitado"],
            ["Proveedor"],
            ["Trabajador"]
        ]
        update.message.reply_text(
            "👤 Selecciona el TIPO DE INGRESO:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        context.user_data["estado"] = ESPERANDO_TIPO

    elif estado == ESPERANDO_TIPO:
        tipo = update.message.text
        telegram_id = update.effective_user.id

        data = {
            "usuario_id": None,
            "zona_id": 1,  # Base 1
            "placas": context.user_data["placas"],
            "tipo_ingreso": tipo
        }

        guardar_acceso_tierra(data)

        update.message.reply_text(
            "✅ Acceso registrado correctamente",
            reply_markup=ReplyKeyboardRemove()
        )
        context.user_data.clear()
        start(update, context)

# ====== MAIN ======

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.regex("^📍 Acceso Tierra"), acceso_tierra))
    dp.add_handler(MessageHandler(Filters.text | Filters.photo, manejar_mensajes))

    print("BOT INICIADO CORRECTAMENTE")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
