import json
import time

import requests
import telebot
import urllib3
from flask import Flask, jsonify, request

from cloudflare_zones import procesar_zonas
from config import (
    CLIENTE_NOTIFICACION,
    DISCORD_WEBHOOK,
    IMG_DISCORD_URL,
    INITIAL_DELAY,
    NOMBRE_PBR,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    UNIFI_API_TOKEN,
    UNIFI_URL,
    check_cloudflare_config,
    check_unifi_config,
)
from ip_info import obtener_ip_publica
from utils import generate_trace_id, setup_logger

logger = setup_logger(__name__)

# Desactivar advertencias SSL ya que usamos verify=False
urllib3.disable_warnings()
verify_ssl = False

def get_traffic_routes():
    # Obtiene todas las reglas PBR configuradas en Unifi.

    url = f"{UNIFI_URL}/proxy/network/v2/api/site/default/trafficroutes"
    headers = {
        "X-API-KEY": UNIFI_API_TOKEN,
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, verify=verify_ssl)
        if response.status_code == 200:
            formatted_json = json.dumps(response.json(), indent=4, ensure_ascii=False)
            logger.debug(f"Obteniendo las PBR en Unifi: {UNIFI_URL} - status: {response.status_code}\n\n{formatted_json}\n.")
            return response.json()
        else:
            logger.error(f"Error al obtener las PBR en Unifi: {UNIFI_URL} {response.status_code} - {response.text}.")
            return []
    except requests.RequestException:
        return []

def update_traffic_route_status(route_data, enabled=False):

    url = f"{UNIFI_URL}/proxy/network/v2/api/site/default/trafficroutes/{route_data['_id']}"
    headers = {
        "X-API-KEY": UNIFI_API_TOKEN,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = route_data.copy()
    payload['enabled'] = enabled

    try:
        request_data = json.dumps(payload, indent=4)
        logger.debug(f"Enviando petición PUT a {url} con datos:\n{request_data}.")

        update_response = requests.put(
            url,
            headers=headers,
            json=payload,
            verify=verify_ssl,
            allow_redirects=True
        )

        logger.debug(f"Respuesta del servidor ({update_response.status_code}):\n{update_response.text}.")

        if update_response.status_code == 200:
            logger.debug(f"Aplicado cambio en la PBR {route_data['description']} en Unifi {UNIFI_URL}.")
            return True, update_response.json()
        else:
            error_msg = f"Error al aplicar cambio en la PBR {route_data['description']} en Unifi {UNIFI_URL}. Status: {update_response.status_code}. Respuesta: {update_response.text}."
            logger.error(error_msg)
            return False, {"error": error_msg}
    except requests.RequestException as e:
        error_msg = f"Excepción al actualizar PBR {route_data['description']}: {str(e)}."
        logger.error(error_msg)
        return False, {"error": error_msg}

def send_notification(message, title, parse_mode=None, retries=4, delay=2.0, initial_delay=INITIAL_DELAY):
    if CLIENTE_NOTIFICACION:
        if CLIENTE_NOTIFICACION == "telegram":
            if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:

                if initial_delay > 0:
                    time.sleep(initial_delay)

                for attempt in range(retries):
                    try:
                        bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
                        bot.send_message(TELEGRAM_CHAT_ID, message, parse_mode=parse_mode)
                        logger.info("Notificación enviada a Telegram correctamente.")
                        return True
                    except Exception as e:
                        logger.debug(f"Notificación enviada a Telegram: {message}.")
                        logger.debug(f"Intento {attempt+1}/{retries}: Error al enviar notificación a Telegram: {str(e)}.")
                        if attempt < retries - 1:
                            time.sleep(delay)
                        else:
                            logger.error(f"Error al enviar notificación a Telegram después de {retries} intentos: {str(e)}.")
                            return False
            return False
        elif CLIENTE_NOTIFICACION == "discord":
            try:
                    message = message.replace("<b>", "**").replace("</b>", "**")

                    # Payload con embeds para incluir imagen
                    payload = {
                        "avatar_url": IMG_DISCORD_URL,
                        "embeds": [
                            {
                                "title": title,
                                "description": message,
                                "color": 6018047,
                                "thumbnail": {"url": IMG_DISCORD_URL}
                            }
                        ]
                    }

                    response = requests.post(DISCORD_WEBHOOK, json=payload)

                    if response.status_code == 204:  # Discord devuelve 204 cuando es exitoso
                        logger.info("Notificación enviada a Discord correctamente.")
                    else:
                        logger.error(f"Error al enviar mensaje a Discord. Status code: {response.status_code}")

            except Exception as e:
                logger.error(f"Error al enviar mensaje a Discord: {str(e)}")
        else:
            logger.error(f"Cliente de notificación no soportado: {CLIENTE_NOTIFICACION}")

def process_webhook_data(data):

    # Verificar si es una prueba de conexión
    if data.get('heartbeat') is None and data.get('monitor') is None and 'msg' in data:
        return True, True, False, "Prueba de conexión recibida correctamente."

    # Verificar que los datos contengan la estructura esperada
    if 'heartbeat' not in data:
        return False, False, False, "El campo 'heartbeat' es requerido."
    if 'status' not in data['heartbeat']:
        return False, False, False, "El campo 'status' en heartbeat es requerido."

    # El status 0 significa DOWN (activar regla), status 1 significa UP (desactivar regla)
    enabled = data['heartbeat']['status'] == 0
    estado_webhook = 'activado' if enabled else 'desactivado'

    message = f"Estado recibido: {'DOWN' if enabled else 'UP'} - La regla debe ser {estado_webhook}"
    return True, False, enabled, message

app = Flask(__name__)

@app.route('/api/route', methods=['POST'])
def process_webhook():

    generate_trace_id()

    try:
        data = request.get_json()
    except Exception:
        return jsonify({"error": "El contenido debe ser JSON."}), 400

    formatted_json = json.dumps(data, indent=4, ensure_ascii=False)
    logger.debug(f"Payload recibido:\n\n{formatted_json}\n.")

    # Procesar los datos del webhook
    is_valid, is_test, enabled, message = process_webhook_data(data)

    if not is_valid:
        return jsonify({"error": message}), 400

    if is_test:
        logger.info("Prueba desde Uptime Kuma satisfactoria.")
        return jsonify({"message": message})

    response_data = {
        "unifi": {"processed": False, "message": "No procesado"},
        "cloudflare": {"processed": False, "message": "No procesado"}
    }

    # Primero, obtener la IP pública si es necesario
    ip_publica = None
    cloudflare_config_valid, cloudflare_message = check_cloudflare_config()
    if cloudflare_config_valid and enabled:
        try:
            ip_publica = obtener_ip_publica()
            if ip_publica:
                logger.info(f"IP pública obtenida: {ip_publica}")
            else:
                logger.warning("No se pudo obtener la IP pública")
        except Exception as e:
            logger.error(f"Error al obtener IP pública: {str(e)}")

    # Procesar Cloudflare si está configurado
    if cloudflare_config_valid:
        try:
            estado_webhook = 'activado' if enabled else 'desactivado'
            logger.info(f"Procesando configuraciones de Cloudflare para estado: {estado_webhook}")
            procesar_zonas(estado_webhook, ip_publica)
            mensaje = f"Configuraciones de Cloudflare procesadas correctamente para estado: {estado_webhook}"
            logger.info(mensaje)
            response_data["cloudflare"] = {"processed": True, "message": mensaje}
            send_notification(f"🌍 *Cloudflare*: Configuraciones procesadas para estado: *{estado_webhook}*",
                           "Estado CLOUDFLARE", parse_mode="Markdown")
        except Exception as e:
            error_msg = f"Error al procesar configuraciones de Cloudflare: {str(e)}"
            logger.error(error_msg)
            response_data["cloudflare"] = {"processed": False, "message": error_msg}
    else:
        logger.info(f"Cloudflare no configurado: {cloudflare_message}")
        response_data["cloudflare"] = {"processed": False, "message": cloudflare_message}

    # Procesar Unifi si está configurado
    unifi_config_valid, unifi_message = check_unifi_config()
    if unifi_config_valid:
        try:
            routes = get_traffic_routes()
            for route in routes:
                if route['description'] == NOMBRE_PBR:
                    success, route_response = update_traffic_route_status(route, enabled)
                    action_msg = 'activada' if enabled else 'desactivada'
                    if success:
                        mensaje = f"Regla '{NOMBRE_PBR}' {action_msg} correctamente"
                        logger.info(mensaje)
                        response_data["unifi"] = {"processed": True, "message": mensaje}
                        send_notification(
                            f"⚽ Regla *{NOMBRE_PBR}* {action_msg} correctamente en Unifi {UNIFI_URL}",
                            "Estado UNIFI",
                            parse_mode="Markdown"
                        )
                    else:
                        error_msg = f"Error al {action_msg} la regla '{NOMBRE_PBR}'"
                        logger.error(error_msg)
                        response_data["unifi"] = {"processed": False, "message": error_msg}
                    break
            else:
                error_msg = f"No se encontró la regla: {NOMBRE_PBR}"
                logger.error(error_msg)
                response_data["unifi"] = {"processed": False, "message": error_msg}
        except Exception as e:
            error_msg = f"Error procesando Unifi: {str(e)}"
            logger.error(error_msg)
            response_data["unifi"] = {"processed": False, "message": error_msg}
    else:
        logger.info(f"Unifi no configurado: {unifi_message}")
        response_data["unifi"] = {"processed": False, "message": unifi_message}

    # Si ninguno está configurado, devolver error
    if not cloudflare_config_valid and not unifi_config_valid:
        return jsonify({
            "error": "No hay configuración válida para Cloudflare ni Unifi",
            "details": response_data
        }), 500

    return jsonify(response_data)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=1666)
