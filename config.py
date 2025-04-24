import os
from typing import Tuple

from dotenv import load_dotenv

load_dotenv()

def ensure_https_url(url):
    if url and not url.startswith('https://'):
        return url.replace('http://', 'https://')
    return url

def check_unifi_config() -> Tuple[bool, str]:

    if not UNIFI_URL:
        return False, "UNIFI_URL no está configurado"
    if not UNIFI_API_TOKEN:
        return False, "UNIFI_API_TOKEN no está configurado"
    if not NOMBRE_PBR:
        return False, "NOMBRE_PBR no está configurado"
    return True, "Configuración de Unifi válida"

def check_cloudflare_config() -> Tuple[bool, str]:

    if not CLOUDFLARE_API_URL:
        return False, "CLOUDFLARE_API_URL no está configurado"
    if not CLOUDFLARE_API_TOKEN:
        return False, "CLOUDFLARE_API_TOKEN no está configurado"
    return True, "Configuración de Cloudflare válida"

UNIFI_URL = ensure_https_url(os.getenv('UNIFI_URL'))
UNIFI_API_TOKEN = os.getenv('UNIFI_API_TOKEN')
NOMBRE_PBR = os.getenv('NOMBRE_PBR')

CLIENTE_NOTIFICACION = os.getenv('CLIENTE_NOTIFICACION')

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK')

CLOUDFLARE_API_URL = os.getenv('CLOUDFLARE_API_URL', 'https://api.cloudflare.com/client/v4')
CLOUDFLARE_API_TOKEN = os.getenv('CLOUDFLARE_API_TOKEN')

INITIAL_DELAY = int(os.getenv('INITIAL_DELAY', '2'))  # Delay in seconds

TZ = os.getenv('TZ', 'Europe/Madrid')
DEBUG = os.getenv('DEBUG', '0') == '1'

IMG_DISCORD_URL = 'https://github.com/unraiders/unifi-pbr-cloudflare/blob/main/imagenes/unifi-pbr-cloudflare.png?raw=true'
