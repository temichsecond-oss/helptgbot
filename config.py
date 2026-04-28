import os
from dotenv import load_dotenv

load_dotenv()

# Токен вашого бота (отримати у @BotFather)
BOT_TOKEN = os.getenv("BOT_TOKEN", "8722791410:AAEwkt5Tz_Q-7fQoRr9ETYKxDRZv8ksvbJw")

# ID групи (від'ємне число, напр. -1001234567890)
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", "-1001234567890"))

# ID адміністраторів (через кому: 123456789,987654321)
ADMIN_IDS = [
    int(i.strip())
    for i in os.getenv("ADMIN_IDS", "123456789").split(",")
    if i.strip().isdigit()
]

# Час щоденного опитування (за Києвом)
DAILY_POLL_HOUR = 13
DAILY_POLL_MINUTE = 0
