#!/bin/sh

echo "$(date +'%d-%m-%Y %H:%M:%S') - Arrancando entrypoint.sh" >&2
echo "$(date +'%d-%m-%Y %H:%M:%S') - Versión: $VERSION" >&2
echo "$(date +'%d-%m-%Y %H:%M:%S') - URL Unifi: $UNIFI_URL" >&2
echo "$(date +'%d-%m-%Y %H:%M:%S') - Nombre PBR: $NOMBRE_PBR" >&2
echo "$(date +'%d-%m-%Y %H:%M:%S') - Notificación a: $CLIENTE_NOTIFICACION" >&2
echo "$(date +'%d-%m-%Y %H:%M:%S') - Número de workers: $WORKERS" >&2
echo "$(date +'%d-%m-%Y %H:%M:%S') - Zona horaria: $TZ" >&2
echo "$(date +'%d-%m-%Y %H:%M:%S') - Debug: $DEBUG" >&2
echo "$(date +'%d-%m-%Y %H:%M:%S') - Arrancando servidor..." >&2

exec gunicorn -w $WORKERS -b 0.0.0.0:1666 unifi-pbr-cloudflare:app