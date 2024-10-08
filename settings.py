from dotenv import load_dotenv



TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_SUPPORT_CHAT_ID = os.getenv("TELEGRAM_SUPPORT_CHAT_ID")
TELEGRAM_PREMIUM_CHAT_ID = os.getenv("TELEGRAM_PREMIUM_CHAT_ID")
PAYMENT_URL = "http://localhost:5000"

if not isinstance(TELEGRAM_SUPPORT_CHAT_ID, int):
    TELEGRAM_SUPPORT_CHAT_ID = int(TELEGRAM_SUPPORT_CHAT_ID)

if not isinstance(TELEGRAM_PREMIUM_CHAT_ID, int):
    TELEGRAM_PREMIUM_CHAT_ID = int(TELEGRAM_PREMIUM_CHAT_ID)