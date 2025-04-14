import requests
import urllib3
import json
from flask import Flask, request, jsonify

from utils import setup_logger, generate_trace_id
from config import UNIFI_URL, UNIFI_API_TOKEN, NOMBRE_PBR

logger = setup_logger(__name__)

# Desactivar advertencias SSL ya que usamos verify=False
urllib3.disable_warnings()
verify_ssl = False

def get_traffic_routes():
    # Obtiene todas las reglas PBR configuradas en Unifi.
    trace_id = generate_trace_id()
    url = f"{UNIFI_URL}/proxy/network/v2/api/site/default/trafficroutes"
    headers = {
        "X-API-KEY": UNIFI_API_TOKEN,
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, verify=verify_ssl)
        if response.status_code == 200:
            formatted_json = json.dumps(response.json(), indent=4, ensure_ascii=False)
            logger.debug(f"Obteniendo las PBR en Unifi: {UNIFI_URL} - status: {response.status_code}\n\n{formatted_json}\n")
            return response.json()
        else:
            logger.error(f"Error al obtener las PBR en Unifi: {UNIFI_URL} {response.status_code} - {response.text}")
            return []
    except requests.RequestException:
        return []

def update_traffic_route_status(route_data, enabled=False):
    """
    Actualiza el estado de una regla PBR específica en Unifi.
    
    Args:
        route_data (dict): Datos completos de la regla PBR
        enabled (bool): True para activar la regla, False para desactivarla
    """
    trace_id = generate_trace_id()
    url = f"{UNIFI_URL}/proxy/network/v2/api/site/default/trafficroutes/{route_data['_id']}"
    headers = {
        "X-API-KEY": UNIFI_API_TOKEN,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # Mantenemos todos los datos de la regla y solo modificamos enabled
    payload = route_data.copy()
    payload['enabled'] = enabled
    
    try:
        request_data = json.dumps(payload, indent=4)
        logger.debug(f"Enviando petición PUT a {url} con datos:\n{request_data}")
        
        update_response = requests.put(
            url, 
            headers=headers, 
            json=payload,
            verify=verify_ssl,
            allow_redirects=True
        )
        
        logger.debug(f"Respuesta del servidor ({update_response.status_code}):\n{update_response.text}")
        
        if update_response.status_code == 200:
            logger.debug(f"Aplicado cambio en la PBR {route_data['description']} en Unifi {UNIFI_URL}")
            return True, update_response.json()
        else:
            error_msg = f"Error al aplicar cambio en la PBR {route_data['description']} en Unifi {UNIFI_URL}. Status: {update_response.status_code}. Respuesta: {update_response.text}"
            logger.error(error_msg)
            return False, {"error": error_msg}
    except requests.RequestException as e:
        error_msg = f"Excepción al actualizar PBR {route_data['description']}: {str(e)}"
        logger.error(error_msg)
        return False, {"error": error_msg}

def create_app():
    """Crea y configura la aplicación Flask."""
    app = Flask(__name__)

    @app.route('/api/route', methods=['POST'])
    def update_route():
        """
        Endpoint que recibe webhooks de Uptime Kuma y actualiza el estado de la regla PBR.
        También maneja las pruebas de conexión del webhook.
        El estado se determina por el campo status en el heartbeat:
        - status = 0 (DOWN) -> activar regla
        - status = 1 (UP) -> desactivar regla
        """
        trace_id = generate_trace_id()
        
        if not request.is_json:
            return jsonify({"error": "El contenido debe ser JSON"}), 400
        
        data = request.get_json()
        formatted_json = json.dumps(data, indent=4, ensure_ascii=False)
        logger.debug(f"Payload recibido de Uptime Kuma:\n\n{formatted_json}\n")

        # Manejar el caso de prueba de conexión
        if data.get('heartbeat') is None and data.get('monitor') is None and 'msg' in data:
            logger.info("Prueba desde Uptime Kuma satisfactoria")
            return jsonify({"message": "Prueba de conexión recibida correctamente"}), 200

        # Validación del payload normal
        if 'heartbeat' not in data:
            return jsonify({"error": "El campo 'heartbeat' es requerido"}), 400
        if 'status' not in data['heartbeat']:
            return jsonify({"error": "El campo 'status' en heartbeat es requerido"}), 400
        
        # El status 0 significa DOWN (activar regla), status 1 significa UP (desactivar regla)
        enabled = data['heartbeat']['status'] == 0
        logger.debug(f"Estado del monitor: {'DOWN' if data['heartbeat']['status'] == 0 else 'UP'} - La regla se {'activará' if enabled else 'desactivará'}")
        
        # Buscar y actualizar la regla
        routes = get_traffic_routes()
        for route in routes:
            if route['description'] == NOMBRE_PBR:
                success, response = update_traffic_route_status(route, enabled)
                if success:
                    logger.info(f"Regla '{NOMBRE_PBR}' {'activada' if enabled else 'desactivada'} correctamente")              
                    return jsonify({
                        "message": f"Regla '{NOMBRE_PBR}' {'activada' if enabled else 'desactivada'} correctamente",
                        "data": response
                    }), 200 
                else:
                    return jsonify(response), 400
        
        return jsonify({"error": f"No se encontró la regla: {NOMBRE_PBR}"}), 404

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1666)
