import os
import requests
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext
)

# =====================
# VARIABLES DE ENTORNO
# =====================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# =====================
# CONSTANTES DE ESTADO
# =====================
ESPERANDO_FOTO = "esperando_foto"
ESPERANDO_PLACAS = "esperando_placas"
ESPERANDO_TIPO = "esperando_tipo"

# =====================
# FUNCIONES SUPABASE
# =====================
def usuario_autorizado(telegram_id: int) -> bool:
    url = f"{SUPABASE_URL}/rest/v1/usuarios?telegram_id=eq.{telegram_id}&activo=eq.true"
    r = requests.get(url, headers=HEADERS)
    return r.status_code == 200 and len(r.json()) > 0

def guardar_acceso_tierra(data: dict) -> bool:
    url = f"{SUPABASE_URL}/rest/v1/accesos_tierra"
    r = requests.post(url, headers=HEADERS, json=data)
    return r.status_code in (200, 201)

# =====================
# COMANDOS PRINCIPALES
# =====================
def start(update: Update, context: CallbackContext):
    telegram_id = update.effective_user.id
    context.user_data.clear()

    if not usuario_autorizado(telegram_id):
        update.message.reply_text(
            "⛔ Acceso no autorizado.\nContacta al administrador."
        )
        return

    keyboard = [
        ["📍 Acceso Tierra (Base 1)"],
        ["🚤 Acceso Marina"],
        ["🚨 Incidencia"],
        ["🔄 Rondín"],
        ["🧑‍✈️ Supervisión"]
    ]

    update.message.reply_text(
        "✅ Acceso autorizado\n\nSelecciona una opción:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# =====================
# FLUJO ACCESO TIERRA
# =====================
def acceso_tierra(update: Update, context: CallbackContext):
    context.user_data.clear()
    context.user_data["estado"] = ESPERANDO_FOTO

    update.message.reply_text(
        "📸 Envía la FOTO del vehículo",
        reply_markup=ReplyKeyboardRemove()
    )

# =====================
# MANEJO DE MENSAJES
# =====================
def manejar_mensajes(update: Update, context: CallbackContext):
    if "estado" not in context.user_data:
        return

    estado = context.user_data.get("estado")

    # ---- FOTO ----
    if estado == ESPERANDO_FOTO:
        if not update.message.photo:
            update.message.reply_text("❗ Debes enviar una FOTO del vehículo.")
            return

        context.user_data["foto_id"] = update.message.photo[-1].file_id
        context.user_data["estado"] = ESPERANDO_PLACAS

        update.message.reply_text("🔤 Ingresa las PLACAS del vehículo:")
        return

    # ---- PLACAS ----
    if estado == ESPERANDO_PLACAS:
        context.user_data["placas"] = update.message.text
        context.user_data["estado"] = ESPERANDO_TIPO

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
        return

    # ---- TIPO ----
    if estado == ESPERANDO_TIPO:
        telegram_id = update.effective_user.id

        data = {
            "zona_id": 1,  # Base 1
            "placas": context.user_data.get("placas"),
            "tipo_ingreso": update.message.text
        }

        guardar_acceso_tierra(data)

        context.user_data.clear()

        update.message.reply_text(
            "✅ Acceso registrado correctamente",
            reply_markup=ReplyKeyboardRemove()
        )

        start(update, context)

# =====================
# MAIN
# =====================
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    dp.add_handler(
        MessageHandler(
            Filters.text & Filters.regex("^📍 Acceso Tierra \\(Base 1\\)$"),
            acceso_tierra
        )
    )

    dp.add_handler(
        MessageHandler(
            Filters.text | Filters.photo,
            manejar_mensajes
        )
    )

    print("BOT INICIADO CORRECTAMENTE")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

