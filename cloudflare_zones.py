import json
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

from config import CLOUDFLARE_API_TOKEN, CLOUDFLARE_API_URL
from ip_info import obtener_ip_publica
from utils import setup_logger

logger = setup_logger(__name__)

def cargar_zonas() -> List[Dict[str, Any]]:

    try:
        with open('/app/data/zonas.json', 'r') as f:
            zonas = json.load(f)
            return zonas
    except Exception as e:
        logger.error(f"Error al cargar el archivo zonas.json: {e}")
        return []

def guardar_zonas(zonas: List[Dict[str, Any]]) -> bool:

    try:
        with open('/app/data/zonas.json', 'w') as f:
            json.dump(zonas, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Error al guardar en el archivo zonas.json: {e}")
        return False

def connect_cloudflare() -> Tuple[bool, Optional[Dict[str, str]]]:

    if not CLOUDFLARE_API_TOKEN:
        logger.error("CLOUDFLARE_API_TOKEN no está configurado.")
        return False, None

    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        logger.debug(f"Intentando verificar conexión con Cloudflare API TOKEN: {CLOUDFLARE_API_TOKEN}")
        response = requests.get(f"{CLOUDFLARE_API_URL}/user/tokens/verify", headers=headers)

        if response.status_code == 200:
            logger.info("Cliente Cloudflare inicializado correctamente.")
            return True, headers
        else:
            logger.error(f"Error al verificar token de Cloudflare: {response.text}")
            return False, None

    except Exception as e:
        logger.error(f"Error al conectar con Cloudflare: {str(e)}")
        return False, None

def verificar_zona(headers: Dict[str, str], zone_id: str) -> bool:

    try:
        response = requests.get(f"{CLOUDFLARE_API_URL}/zones/{zone_id}", headers=headers)

        if response.status_code == 200:
            zona = response.json()['result']
            zone_name = zona.get('name', 'desconocido')
            logger.info(f"Zona {zone_id} ({zone_name}) verificada correctamente.")
            return True
        else:
            logger.error(f"Error al verificar la zona {zone_id}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error inesperado al verificar la zona {zone_id}: {e}")
        return False

def buscar_registro_a(headers: Dict[str, str], zone_id: str, nombre: str) -> Optional[Dict[str, Any]]:

    try:
        params = {
            'type': 'A',
            'name': nombre
        }

        response = requests.get(
            f"{CLOUDFLARE_API_URL}/zones/{zone_id}/dns_records",
            headers=headers,
            params=params
        )

        if response.status_code == 200:
            registros = response.json()['result']
            if registros:
                registro = registros[0]
                logger.info(f"Registro encontrado: {nombre} - ID: {registro.get('id')} - IP actual: {registro.get('content')} - Proxied: {registro.get('proxied')}")
                return registro
            else:
                logger.warning(f"No se encontró registro tipo A con nombre {nombre} en la zona {zone_id}")
                return None
        else:
            logger.error(f"Error al buscar registro DNS {nombre}: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error inesperado al buscar registro DNS {nombre}: {e}")
        return None

def buscar_registro_cname(headers: Dict[str, str], zone_id: str, nombre: str) -> Optional[Dict[str, Any]]:

    try:
        params = {
            'type': 'CNAME',
            'name': nombre
        }

        logger.debug(f"Buscando registro CNAME {nombre} en zona {zone_id}")
        logger.debug(f"Parámetros de búsqueda: {params}")
        logger.debug(f"URL: {CLOUDFLARE_API_URL}/zones/{zone_id}/dns_records")

        response = requests.get(
            f"{CLOUDFLARE_API_URL}/zones/{zone_id}/dns_records",
            headers=headers,
            params=params,
            timeout=30.0
        )

        logger.debug(f"Respuesta de Cloudflare: Status={response.status_code}")
        if response.status_code == 200:
            registros = response.json()['result']
            if registros:
                registro = registros[0]
                logger.info(f"Registro CNAME encontrado: {nombre} - ID: {registro.get('id')} - Target actual: {registro.get('content')} - Proxied: {registro.get('proxied')}")
                return registro
            else:
                logger.warning(f"No se encontró registro tipo CNAME con nombre {nombre} en la zona {zone_id}")
                return None
        else:
            error_text = response.text
            logger.error(f"Error al buscar registro CNAME {nombre}: Status={response.status_code}, Response={error_text}")
            return None
    except requests.Timeout as e:
        logger.error(f"Timeout al buscar registro CNAME {nombre}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado al buscar registro CNAME {nombre}: {str(e)}")
        logger.error(f"Detalles del error: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

def actualizar_registro_cname(headers: Dict[str, str], zone_id: str, registro_id: str,
                          nuevo_target: str, registro_actual: Dict[str, Any]) -> bool:

    try:
        nombre_registro = registro_actual['name']
        target_actual = registro_actual['content']

        if target_actual == nuevo_target:
            logger.info(f"El registro CNAME {nombre_registro} ya tiene el target {nuevo_target}. No se requiere actualización.")
            return True

        logger.info(f"Preparando actualización del registro CNAME {nombre_registro}...")
        logger.info(f"Target actual: {target_actual}")
        logger.info(f"Nuevo target: {nuevo_target}")

        estado_proxied_actual = registro_actual.get('proxied', False)

        datos_actualizacion = {
            'name': registro_actual['name'],
            'type': 'CNAME',
            'content': nuevo_target,
            'proxied': estado_proxied_actual,
            'ttl': registro_actual.get('ttl', 1)
        }

        response = requests.put(
            f"{CLOUDFLARE_API_URL}/zones/{zone_id}/dns_records/{registro_id}",
            headers=headers,
            json=datos_actualizacion
        )

        if response.status_code == 200:
            resultado = response.json()
            if resultado.get('success', False):
                logger.info(f"Registro CNAME {nombre_registro} actualizado: Target anterior={target_actual}, Target nuevo={nuevo_target}")
                return True
            else:
                logger.error(f"Error en la respuesta de Cloudflare: {resultado.get('errors', [])}")
                return False
        else:
            logger.error(f"Error al actualizar registro CNAME: {response.text}")
            return False

    except Exception as e:
        logger.error(f"Error inesperado al actualizar el target CNAME: {e}")
        return False

def actualizar_registro_proxied(headers: Dict[str, str], zone_id: str, registro_id: str, proxied: bool) -> bool:

    max_retries = 3
    base_timeout = 60.0  # 60 segundos de timeout base

    for intento in range(max_retries):
        try:
            # Obtener registro actual
            response = requests.get(
                f"{CLOUDFLARE_API_URL}/zones/{zone_id}/dns_records/{registro_id}",
                headers=headers,
                timeout=base_timeout * (intento + 1)
            )

            if response.status_code != 200:
                error_text = response.text
                logger.error(f"Error al obtener registro actual: Status={response.status_code}, Response={error_text}")
                if intento < max_retries - 1:
                    logger.info("Reintentando en 5 segundos...")
                    time.sleep(5)
                    continue
                return False

            registro_actual = response.json()['result']
            estado_actual = registro_actual.get('proxied', False)
            nombre_registro = registro_actual.get('name', 'desconocido')
            tipo_registro = registro_actual.get('type', 'desconocido')

            logger.debug(f"Estado actual de proxied para {nombre_registro} ({tipo_registro}): {estado_actual}")

            if estado_actual == proxied:
                logger.info(f"El registro {nombre_registro} ya tiene el estado proxied={proxied}. No se requiere actualización.")
                return True

            datos_actualizacion = {
                'name': registro_actual['name'],
                'type': registro_actual['type'],
                'content': registro_actual['content'],
                'proxied': proxied,
                'ttl': registro_actual.get('ttl', 1)
            }

            logger.debug(f"Enviando datos de actualización a Cloudflare: {datos_actualizacion}")

            response = requests.put(
                f"{CLOUDFLARE_API_URL}/zones/{zone_id}/dns_records/{registro_id}",
                headers=headers,
                json=datos_actualizacion,
                timeout=base_timeout * (intento + 1)
            )

            logger.debug(f"Respuesta de Cloudflare: Status={response.status_code}")
            response_json = response.json()
            logger.debug(f"Respuesta detallada: {json.dumps(response_json, indent=2)}")

            if response.status_code == 200:
                if response_json.get('success', False):
                    logger.debug(f"Registro {nombre_registro} actualizado: proxied={proxied}")
                    # Verificar que el cambio se aplicó correctamente
                    verify_response = requests.get(
                        f"{CLOUDFLARE_API_URL}/zones/{zone_id}/dns_records/{registro_id}",
                        headers=headers
                    )
                    if verify_response.status_code == 200:
                        registro_actualizado = verify_response.json()['result']
                        estado_final = registro_actualizado.get('proxied', False)
                        if estado_final == proxied:
                            logger.debug(f"Verificación exitosa: el estado proxied se actualizó correctamente a {proxied}")
                            return True
                        else:
                            logger.error(f"El estado proxied no se actualizó correctamente. Estado actual: {estado_final}")
                            if intento < max_retries - 1:
                                logger.info("Reintentando en 5 segundos...")
                                time.sleep(5)
                                continue
                            return False
                else:
                    errors = response_json.get('errors', [])
                    messages = response_json.get('messages', [])
                    logger.error(f"Error en la respuesta de Cloudflare: Errors={errors}, Messages={messages}")
                    if intento < max_retries - 1:
                        logger.info("Reintentando en 5 segundos...")
                        time.sleep(5)
                        continue
                    return False
            else:
                logger.error(f"Error al actualizar registro: Status={response.status_code}, Response={response.text}")
                if intento < max_retries - 1:
                    logger.info("Reintentando en 5 segundos...")
                    time.sleep(5)
                    continue
                return False

        except requests.Timeout as e:
            logger.error(f"Timeout al actualizar el registro (intento {intento + 1}): {str(e)}")
            if intento < max_retries - 1:
                logger.info("Reintentando en 5 segundos...")
                time.sleep(5)
                continue
            return False
        except Exception as e:
            logger.error(f"Error inesperado al actualizar el registro proxied: {str(e)}")
            logger.error(f"Detalles del error: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback completo:\n{traceback.format_exc()}")
            if intento < max_retries - 1:
                logger.info("Reintentando en 5 segundos...")
                time.sleep(5)
                continue
            return False

    return False

def actualizar_registro_contenido(headers: Dict[str, str], zone_id: str, registro_id: str,
                              nuevo_contenido: str, registro_actual: Dict[str, Any]) -> bool:

    try:
        nombre_registro = registro_actual['name']
        contenido_actual = registro_actual['content']

        if contenido_actual == nuevo_contenido:
            logger.info(f"El registro {nombre_registro} ya tiene el contenido {nuevo_contenido}. No se requiere actualización.")
            return True

        logger.info(f"Preparando actualización del registro {nombre_registro}...")
        logger.info(f"Contenido actual: {contenido_actual}")
        logger.info(f"Nuevo contenido: {nuevo_contenido}")

        # Obtener el estado actual del registro antes de actualizarlo
        response = requests.get(
            f"{CLOUDFLARE_API_URL}/zones/{zone_id}/dns_records/{registro_id}",
            headers=headers
        )

        if response.status_code != 200:
            logger.error(f"Error al obtener estado actual del registro: {response.text}")
            return False

        registro_actual_cloudflare = response.json()['result']
        estado_proxied_actual = registro_actual_cloudflare.get('proxied', False)

        datos_actualizacion = {
            'name': registro_actual['name'],
            'type': registro_actual['type'],
            'content': nuevo_contenido,
            'proxied': estado_proxied_actual,  # Mantenemos el estado proxied actual
            'ttl': registro_actual.get('ttl', 1)
        }

        logger.debug(f"Enviando actualización a Cloudflare: {datos_actualizacion}")
        response = requests.put(
            f"{CLOUDFLARE_API_URL}/zones/{zone_id}/dns_records/{registro_id}",
            headers=headers,
            json=datos_actualizacion
        )

        if response.status_code == 200:
            resultado = response.json()
            if resultado.get('success', False):
                logger.info(f"Registro {nombre_registro} actualizado: IP anterior={contenido_actual}, IP nueva={nuevo_contenido}, proxied={estado_proxied_actual}")
                return True
            else:
                logger.error(f"Error en la respuesta de Cloudflare: {resultado.get('errors', [])}")
                return False
        else:
            logger.error(f"Error al actualizar registro: {response.text}")
            return False

    except Exception as e:
        logger.error(f"Error inesperado al actualizar el contenido: {e}")
        return False

def procesar_zonas(estado_webhook: str, ip_publica: str = None):

    logger.debug(f"=== INICIANDO PROCESAMIENTO DE ZONAS PARA ESTADO: {estado_webhook} ===")

    # Conectamos a Cloudflare
    logger.debug("Conectando a Cloudflare API...")
    exito, headers = connect_cloudflare()
    if not exito or not headers:
        logger.error("No se pudo conectar con Cloudflare. Abortando operación.")
        return

    # Cargamos las zonas
    logger.info("Cargando configuración de zonas desde zonas.json...")
    zonas = cargar_zonas()
    if not zonas:
        logger.error("No hay zonas configuradas o no se pudo cargar el archivo zonas.json.")
        return

    logger.info(f"Se encontraron {len(zonas)} zonas configuradas.")

    # Para modificaciones en contenido, necesitamos la IP pública solo al activar
    if estado_webhook == 'activado' and any(zona.get('cambiar_ip', False) for zona in zonas):
        if ip_publica:
            logger.info(f"Usando IP pública proporcionada: {ip_publica}")
        else:
            logger.info("Obteniendo IP pública para actualizar registros...")
            ip_publica = obtener_ip_publica()
            if not ip_publica:
                logger.error("No se pudo obtener la IP pública. Necesaria para actualizar registros.")
                return
        logger.info(f"IP pública obtenida/proporcionida: {ip_publica}")

    # Procesamos cada zona
    zonas_modificadas = False
    for i, zona in enumerate(zonas):
        zone_id = zona.get('id_zona')
        nombre = zona.get('name') or zona.get('nombre')

        logger.info(f"--- Procesando zona {i+1}/{len(zonas)}: {nombre} (ID: {zone_id}) ---")

        if not zone_id or not nombre:
            logger.warning(f"Zona #{i+1} no tiene id_zona o nombre/name. Saltando.")
            continue

        # Verificamos que la zona sea válida
        logger.debug(f"Verificando acceso a la zona {zone_id}...")
        if not verificar_zona(headers, zone_id):
            logger.warning(f"Zona {zone_id} no es válida en Cloudflare. Saltando.")
            continue

        # Determinar el tipo de registro basado en la configuración
        es_cname = bool(zona.get('target_cname'))

        if es_cname:
            # Procesamiento para registros CNAME
            logger.info(f"Procesando configuración CNAME para {nombre}...")
            registro_cname = buscar_registro_cname(headers, zone_id, nombre)
            if registro_cname:
                if estado_webhook == 'activado':
                    target_actual = registro_cname['content']
                    logger.info(f"Guardando target actual del CNAME ({target_actual}) antes de cambiarlo")

                    zonas[i]['target_cname_anterior'] = target_actual
                    zonas_modificadas = True

                    if actualizar_registro_cname(headers, zone_id, registro_cname['id'], zona['target_cname'], registro_cname):
                        logger.info(f"Target CNAME de {nombre} actualizado a {zona['target_cname']}")
                    else:
                        logger.error(f"Error al actualizar target CNAME de {nombre}")

                elif estado_webhook == 'desactivado' and zona.get('target_cname_anterior'):
                    target_anterior = zona['target_cname_anterior']
                    logger.info(f"Restaurando target CNAME anterior: {target_anterior}")

                    if actualizar_registro_cname(headers, zone_id, registro_cname['id'], target_anterior, registro_cname):
                        logger.info(f"Target CNAME de {nombre} restaurado a {target_anterior}")
                        zonas[i]['target_cname_anterior'] = ""
                        zonas_modificadas = True
                        logger.info(f"Valor de target_cname_anterior limpiado para {nombre}")
                    else:
                        logger.error(f"Error al restaurar target CNAME de {nombre}")

                # Procesamiento de cambio de proxied para registro CNAME si está configurado
                if zona.get('cambiar_proxied', False):
                    nuevo_estado_proxied = False if estado_webhook == 'activado' else True
                    logger.info(f"Acción: Cambiar estado proxied del CNAME a {nuevo_estado_proxied}")

                    if actualizar_registro_proxied(headers, zone_id, registro_cname['id'], nuevo_estado_proxied):
                        logger.info(f"Proxied del CNAME {nombre} actualizado correctamente a {nuevo_estado_proxied}")
                    else:
                        logger.error(f"Error al actualizar proxied del CNAME {nombre}")
            else:
                logger.warning(f"No se encontró registro CNAME para {nombre}")

        else:
            # Procesamiento para registros tipo A
            registro_a = buscar_registro_a(headers, zone_id, nombre)
            if registro_a:
                # Procesamiento de cambio de IP
                if zona.get('cambiar_ip', False):
                    if estado_webhook == 'activado':
                        contenido_actual = registro_a['content']
                        logger.info(f"Acción: Guardar IP actual ({contenido_actual}) y actualizar a IP pública ({ip_publica})")

                        zonas[i]['contenido_anterior'] = contenido_actual
                        zonas_modificadas = True

                        if actualizar_registro_contenido(headers, zone_id, registro_a['id'], ip_publica, registro_a):
                            logger.info(f"IP de {nombre} actualizada correctamente a {ip_publica}")
                            registro_a = buscar_registro_a(headers, zone_id, nombre)
                        else:
                            logger.error(f"Error al actualizar IP de {nombre}")

                    elif estado_webhook == 'desactivado' and zona.get('contenido_anterior'):
                        contenido_anterior = zona.get('contenido_anterior')
                        logger.info(f"Acción: Restaurar IP a valor anterior ({contenido_anterior})")

                        if actualizar_registro_contenido(headers, zone_id, registro_a['id'], contenido_anterior, registro_a):
                            logger.info(f"IP de {nombre} restaurada correctamente a {contenido_anterior}")
                            registro_a = buscar_registro_a(headers, zone_id, nombre)
                        else:
                            logger.error(f"Error al restaurar IP de {nombre}")
                else:
                    logger.info(f"El registro A {nombre} no tiene configurado el cambio de IP. Saltando esta acción.")

                # Procesamiento de cambio de proxied para registro A
                if zona.get('cambiar_proxied', False):
                    nuevo_estado_proxied = False if estado_webhook == 'activado' else True
                    logger.info(f"Acción: Cambiar estado proxied del registro A a {nuevo_estado_proxied}")

                    if actualizar_registro_proxied(headers, zone_id, registro_a['id'], nuevo_estado_proxied):
                        logger.info(f"Proxied del registro A {nombre} actualizado correctamente a {nuevo_estado_proxied}")
                    else:
                        logger.error(f"Error al actualizar proxied del registro A {nombre}")
                else:
                    logger.info(f"El registro A {nombre} no tiene configurado el cambio de proxied. Saltando esta acción.")
            else:
                logger.error(f"No se encontró registro tipo A para {nombre}")

    # Guardamos las zonas si hubo modificaciones
    if zonas_modificadas:
        logger.debug("Guardando cambios en zonas.json...")
        if guardar_zonas(zonas):
            logger.debug("Archivo zonas.json actualizado correctamente")
        else:
            logger.error("Error al guardar cambios en zonas.json")

    logger.debug(f"=== PROCESAMIENTO DE ZONAS FINALIZADO PARA ESTADO: {estado_webhook} ===")

if __name__ == "__main__":
    # Para pruebas manuales
    logger.info("Iniciando prueba de conexión a Cloudflare...")
    success, headers = connect_cloudflare()
    if success:
        logger.info("Conexión a Cloudflare establecida correctamente.")
    else:
        logger.error("No se pudo conectar a Cloudflare.")
