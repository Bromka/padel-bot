import os

# ── YCLIENTS ──────────────────────────────────────────────
YCLIENTS_TOKEN = os.environ.get("YCLIENTS_TOKEN", "")

# Список клубов. outdoor=True → показываем предупреждение при дожде.
CLUBS = [
    {
        "name": "Падел Клуб",
        "company_id": 1427988,
        "outdoor": False,
        "booking_url": "https://b1427988.yclients.com/",
    },
    # Добавьте сюда другие клубы:
    # {
    #     "name": "Открытый Корт",
    #     "company_id": 9999999,
    #     "outdoor": True,
    #     "booking_url": "https://b9999999.yclients.com/",
    # },
]

# Сколько часов после дождя считать корт потенциально непригодным
HOURS_AFTER_RAIN = 2

# ── ПОГОДА ────────────────────────────────────────────────
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
WEATHER_CITY = "Kazan,RU"
WEATHER_TIMEZONE = "Europe/Moscow"

# ── TELEGRAM ──────────────────────────────────────────────
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID", "")

# ID топика «Свободные корты» в форум-группе (None = общий чат)
TG_THREAD_ID = int(os.environ.get("TG_THREAD_ID", "4"))

# ── РАСПИСАНИЕ ────────────────────────────────────────────
# Показывать слоты с этого часа и до этого (включительно)
SCHEDULE_START_HOUR = 8
SCHEDULE_END_HOUR = 22
