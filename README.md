# UNIFI-PBR-CLOUDFLARE

Utilidad para cambiar el estado enable / disable de la ruta basada en política (Policy-Based Routing - PBR) de los routers Unifi mediante el uso de un Webhook enviado desde Uptime Kuma haciendo uso del servicio de noticaciones, con esto conseguimos activar una ruta de salida a Internet que tengamos configurada como VPN por ejemplo cuando se bloquean las IP's de Cloudflare los fines de semana.

---

**1** - En nuestro usuario en Unifi creamos una API KEY, menú Configuración, vamos a Admins & Users, hacemos click en nuestro usuario y en la ventana lateral que aparece vamos a Control Plane API Key, botón "Create New", le pones un nombre y Crear, copia la KEY que la necesitaremos luego para la variable UNIFI_API_TOKEN.

**2** - Instalamos el docker mediante el docker-compose.yml o mediante la plantilla de Unraid, abajo está la descripción de cada variable.

**3** - Nos vamos a Uptime Kuma y en Ajustes -> Notificaciones, botón "Configurar notificacion":

- Tipo de notificacacion: Webhook
- Nombre sencillo: El nombre que quieras ponerle a la notificación.
- URL Post: La URL con la IP de la máquina donde está corriendo el Docker, el puerto que expones en ese Docker y /api/route, quedando por ejemplo así: http://192.168.6.19:1666/api/route
- Request Body: Preset - application/json

Si ya hemos levantado el Docker y le damos a Test nos tiene que salir en los logs del contenedor [INFO] Prueba desde Uptime Kuma satisfactoria.

**4** - Ahora nos vamos a uno de los monitores que tenemos configurados y que esté chequeando una IP de Cloudflare de las que bloquean cada fin de semana. editamos y arriba a la derecha en Notificaciones activamos la que acabamos de crear.

Si no quieres esperar al fin de semana y quieres hacer una prueba, activa esa Notificación en algún monitor de algún servicio tuyo que puedas parar y te tiene que poner en el router de Unifi la ruta que hayas especificado en la variable NOMBRE_PBR como activa al hacer Down el servicio y a la inversa, cuando el servicio vuelva a estar UP se tiene que desactivar la ruta en el router de Unifi. 

### Configuración variables de entorno en fichero .env (renombrar el env-example a .env)

| VARIABLE                | NECESARIA | VERSIÓN | VALOR |
|:----------------------- |:---------:| :------:| :-------------|
| UNIFI_URL               |     ✅    | v0.1.0  | Host/IP del router de Unifi. Importante https Ejemplo: https://192.168.2.20               |
| UNIFI_API_TOKEN         |     ✅    | v0.1.0  | Token para el acceso a Unifi a través de la API.                         |
| NOMBRE_PBR              |     ✅    | v0.1.0  | Nombre de la Policy-Based Routing (PBR) en Unifi que se quiere controlar.|
| WORKERS                 |     ✅    | v0.1.0  | Número de peticiones simultáneas. (podemos dejarlo en 1)                 |
| DEBUG                   |     ✅    | v0.1.0  | Habilita el modo Debug en el log. (0 = No / 1 = Si) |
| TZ                      |     ✅    | v0.1.0  | Timezone (Por ejemplo: Europe/Madrid) |

La VERSIÓN indica cuando se añadió esa variable o cuando sufrió alguna actualización. Consultar https://github.com/unraiders/unifi-pbr-cloudflare/releases

---

Se ha probado en un Unifi Cloud Gateway Ultra OS 4.1.22 y Network 9.0.114

---

Te puedes descargar la imagen del icono desde aquí: https://raw.githubusercontent.com/unraiders/unifi-pbr-cloudflare/master/imagenes/unifi-pbr-cloudflare.png

---

### Ejemplo docker-compose.yml (con fichero .env aparte)
```yaml
services:
  unifi-pbr-cloudflare:
    image: unraiders/unifi-pbr-cloudflare
    container_name: unifi-pbr-cloudflare
    env_file:
        - .env
    ports:
        - "1666:1666"
    network_mode: bridge
    restart: unless-stopped
```

---

### Ejemplo docker-compose.yml (con variables incorporadas)
```yaml
services:
  unifi-pbr-cloudflare:
    image: unraiders/unifi-pbr-cloudflare
    container_name: unifi-pbr-cloudflare
    environment:
        - UNIFI_URL=
        - UNIFI_API_TOKEN=
        - NOMBRE_PBR=
        - WORKERS=1
        - DEBUG=0
        - TZ=Europe/Madrid
    ports:
        - "1666:1666"
    network_mode: bridge
    restart: unless-stopped
```

---

## Instalación plantilla en Unraid.

- Nos vamos a una ventana de terminal en nuestro Unraid, pegamos esta línea y enter:
```sh
wget -O /boot/config/plugins/dockerMan/templates-user/my-unifi-pbr-cloudflare.xml https://raw.githubusercontent.com/unraiders/unifi-pbr-cloudflare/refs/heads/main/my-unifi-pbr-cloudflare.xml
```
- Nos vamos a DOCKER y abajo a la izquierda tenemos el botón "AGREGAR CONTENEDOR" hacemos click y en seleccionar plantilla seleccionamos unifi-pbr-cloudflare y rellenamos las variables de entorno necesarias, tienes una explicación en cada variable en la propia plantilla.

---

## Imágenes

![alt text](https://github.com/unraiders/unifi-pbr-cloudflare/blob/main/imagenes/log_unifi-pbr-cloudflare.png)

**Log contenedor**

---

![alt text](https://github.com/unraiders/unifi-pbr-cloudflare/blob/main/imagenes/rutas_unifi-pbr-cloudflare.png)

**Rutas en el router Unifi**

---

![alt text](https://github.com/unraiders/unifi-pbr-cloudflare/blob/main/imagenes/webhook_unifi-pbr-cloudflare.png)

**Configuración Notificación en Uptime Kuma**

---
