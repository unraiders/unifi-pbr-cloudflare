import os

from dotenv import load_dotenv

load_dotenv()

def ensure_https_url(url):
    if url and not url.startswith('https://'):
        return url.replace('http://', 'https://')
    return url

UNIFI_URL = ensure_https_url(os.getenv('UNIFI_URL'))
UNIFI_API_TOKEN = os.getenv('UNIFI_API_TOKEN')
NOMBRE_PBR = os.getenv('NOMBRE_PBR')

CLIENTE_NOTIFICACION = os.getenv("CLIENTE_NOTIFICACION")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

WORKERS = os.getenv('WORKERS', '1')

INITIAL_DELAY = int(os.getenv('INITIAL_DELAY', '2'))  # Delay in seconds

TZ = os.getenv("TZ", "Europe/Madrid")
DEBUG = os.getenv("DEBUG", "0") == "1"

IMG_DISCORD_URL = "https://github.com/unraiders/unifi-pbr-cloudflare/blob/main/imagenes/unifi-pbr-cloudflare.png?raw=true"
