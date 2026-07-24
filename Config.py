import os

# ---------- ТОКЕН БОТА ----------
# Получите токен у @BotFather в Telegram:
#   1. Напишите /newbot
#   2. Задайте имя и username бота
#   3. Скопируйте выданный токен
#
# Рекомендуется хранить токен в переменной окружения, а не прямо в коде,
# особенно если репозиторий публичный на GitHub.
#
# Способ 1 (безопасный, через переменную окружения):
BOT_TOKEN ="8920386800:AAEMG39dLXKi9W2qjLo0uiljRqYO2v5tNbg"

# Способ 2 (просто, но небезопасно для публичного репозитория):
# BOT_TOKEN = "вставьте_сюда_токен_от_botfather"


# ---------- ТОКЕН ПЛАТЕЖНОГО ПРОВАЙДЕРА ----------
# Нужен для приёма платежей через Telegram Payments (aiogram.types.PreCheckoutQuery).
# Получить можно через @BotFather -> /mybots -> выбрать бота -> Payments -> выбрать провайдера.
PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN", "")


# ---------- АДМИНИСТРАТОРЫ ----------
# Telegram user_id администраторов бота (узнать свой id можно у @userinfobot)
ADMIN_IDS = [
    123456789,  # замените на реальный Telegram ID
]


# ---------- ПУТЬ К ФАЙЛАМ (фото товаров и т.п.) ----------
FILES_DIR = os.path.join(os.path.dirname(__file__), "files")
os.makedirs(FILES_DIR, exist_ok=True)


# ---------- БАЗА ДАННЫХ (если используется) ----------
DB_NAME = os.getenv("DB_NAME", "database.db")

