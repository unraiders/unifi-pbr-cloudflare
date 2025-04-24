import re

import requests

from utils import setup_logger

logger = setup_logger(__name__)

def obtener_ip_publica():

    def try_get_ip(urls):
        for url in urls:
            try:
                response = requests.get(url.strip(), timeout=10.0)
                if response.status_code == 200:
                    ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
                    ip = response.text.strip()
                    if ip_pattern.match(ip):
                        return ip, url.strip()
            except Exception as e:
                logger.debug(f"Error al obtener IP de {url.strip()}: {str(e)}")
                continue
        return None, None

    # Leer las URLs del archivo
    try:
        with open('/app/data/check_ip.txt', 'r') as file:
            urls = file.readlines()

        ip, url_usado = try_get_ip(urls)
        if ip:
            logger.debug(f'Dirección IP pública desde {url_usado} es: {ip}')
            logger.info(f'IP pública obtenida: {ip}')
            return ip
        else:
            logger.error('No se pudo obtener la IP pública de ninguna de las URLs disponibles')
            return None
    except Exception as e:
        logger.error(f'Error al leer el archivo check_ip.txt o procesar URLs: {str(e)}')
        return None
