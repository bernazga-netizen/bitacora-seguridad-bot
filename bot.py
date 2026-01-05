import os
import requests
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# =====================
# VARIABLES
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
# ESTADOS
# =====================
ESPERANDO_FOTO = "foto"
ESPERANDO_PLACAS = "placas"
ESPERANDO_TIPO = "tipo"

# =====================
# SUPABASE
# =====================
def usuario_autorizado(telegram_id):
    url = f"{SUPABASE_URL}/rest/v1/usuarios?telegram_id=eq.{telegram_id}&activo=eq.true"
    r = requests.get(url, headers=HEADERS)
    return r.status_code == 200 and len(r.json()) > 0

def guardar_acceso_tierra(data):
    url = f"{SUPABASE_URL}/rest/v1/accesos_tierra"
    requests.post(url, headers=HEADERS, json=data)

# =====================
# START
# =====================
def start(update: Update, context: CallbackContext):
    if not usuario_autorizado(update.effective_user.id):
        update.message.reply_text("⛔ Acceso no autorizado")
        return

    context.user_data.clear()

    teclado = [
        ["📍 Acceso Tierra (Base 1)"],
        ["🚤 Acceso Marina"],
        ["🚨 Incidencia"],
        ["🔄 Rondín"],
        ["🧑‍✈️ Supervisión"]
    ]

    update.message.reply_text(
        "Selecciona una opción:",
        reply_markup=ReplyKeyboardMarkup(teclado, resize_keyboard=True)
    )

# =====================
# MENSAJES (CONTROL TOTAL)
# =====================
def manejar(update: Update, context: CallbackContext):
    texto = update.message.text if update.message.text else ""

    # --- BOTÓN ACCESO TIERRA ---
    if texto == "📍 Acceso Tierra (Base 1)":
        context.user_data.clear()
        context.user_data["estado"] = ESPERANDO_FOTO
        update.message.reply_text(
            "📸 Envía la FOTO del vehículo",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # --- FLUJO FOTO ---
    if context.user_data.get("estado") == ESPERANDO_FOTO:
        if not update.message.photo:
            update.message.reply_text("❗ Debes enviar una FOTO")
            return
        context.user_data["foto"] = update.message.photo[-1].file_id
        context.user_data["estado"] = ESPERANDO_PLACAS
        update.message.reply_text("🔤 Ingresa las PL
