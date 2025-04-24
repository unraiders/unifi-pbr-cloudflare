# UNIFI-PBR-CLOUDFLARE

Esta utilidad se compone de 2 servicios que se gestionan desde un mismo endpoint /api/route:

- Utilidad para UNIFI: Si tenemos definida la variable **NOMBRE_PBR** con algún valor intentará activar esa regla en nuestro router de Unifi.
- Utilidad para CLOUDFLARE: Si tenemos definidas las variables **CLOUDFLARE_API_URL** y **CLOUDFLARE_API_TOKEN** con algún valor intentará gestionar las opciones en Cloudflare que hemos definido en el fichero zonas.json (explicación mas abajo).

### ENDPOINT PARA UNIFI /api/route

Utilidad para cambiar el estado enable / disable de la ruta basada en política (Policy-Based Routing - PBR) de los routers Unifi mediante el uso de un webhook enviado desde Uptime Kuma haciendo uso del servicio de notificaciones con notificación del evento de activación o desactivación a Telegram o Discord, con esto conseguimos activar una ruta de salida a Internet que tengamos configurada como VPN por ejemplo cuando se bloquean las IP's de Cloudflare cuando deciden los señores de la Liga Española.

**1** - En nuestro usuario en Unifi creamos una API KEY, menú Configuración, vamos a Admins & Users, hacemos click en nuestro usuario y en la ventana lateral que aparece vamos a Control Plane API Key, botón "Create New", le pones un nombre y Crear, copia la KEY que la necesitaremos luego para la variable de entorno UNIFI_API_TOKEN.

**2** - Instalamos el Docker mediante el docker-compose.yml o mediante la plantilla de Unraid, abajo está la descripción de cada variable.

**3** - Nos vamos a Uptime Kuma y en Ajustes -> Notificaciones, botón "Configurar notificación":

- Tipo de notificación: Webhook
- Nombre sencillo: El nombre que quieras ponerle a la notificación.
- URL Post: La URL con la IP de la máquina donde está corriendo el Docker, el puerto que expones en ese Docker y /api/route, quedando por ejemplo así: http://192.168.6.19:1666/api/route
- Request Body: Preset - application/json

Si ya hemos levantado el Docker y le damos al botón Test nos tiene que salir en los logs del contenedor: [INFO] Prueba desde Uptime Kuma satisfactoria.

**4** - Ahora nos vamos a uno de los monitores que tenemos configurados y que esté chequeando una IP de Cloudflare de las que bloquean cada fin de semana o un servicio nuestro que esté detrás de Cloudflare, editamos y arriba a la derecha en Notificaciones activamos la que acabamos de crear.

Si no quieres esperar al fin de semana y quieres hacer una prueba, activa esa Notificación en algún monitor de algún servicio tuyo que puedas parar y te tiene que poner en el router de Unifi la ruta que hayas especificado en la variable **NOMBRE_PBR** como activa al hacer DOWN el servicio y a la inversa, cuando el servicio vuelva a estar UP se tiene que desactivar la ruta en el router de Unifi.


### ENDPOINT PARA CLOUDFLARE /api/route

Utilidad para sacar del túnel y de proxied un registro tipo CNAME del DNS y/o cambiar la IP y/o el estado proxied en un registro A en Cloudflare mediante el uso de un webhook enviado desde Uptime Kuma haciendo uso del servicio de notificaciones con notificación del evento de activación o desactivación a Telegram o Discord, con esto conseguimos sacar de proxied y asignarle otro nombre de dominio destino un registro tipo CNAME en el DNS y en el caso de un registro tipo A sacarlo de proxied y asignarle nuestra IP pública para que pueda estar accesible cuando se bloquean las IP's de Cloudflare los fines de semana, hay que tener en cuenta que debemos tener configurado un servicio proxy como puede ser Nginx Proxy Manager, Pangolin, etc.. en nuestro servidor para que haga la redirección de la url https://subdominio.dominio.com al servicio interno que estamos exponiendo a Internet.

**1** - Vamos a generar un API TOKEN en Cloudflare que nos permita realizar los cambios a nivel de dominio, una vez identificados en nuestra cuenta de Cloudflare nos vamos a nuestro perfil con la opción de arriba a la derecha, seleccionamos la opción "Tokens de API", hacemos click en el botón "Crear token", podemos seleccionar la plantilla "Editar zona DNS", botón "Usar plantilla", en Crear token le damos al lápiz para editar el nombre de nuestro token, aquí solo tenemos que especificar en Recursos de zona en el desplegable la zona específica o todas las que queremos que nuestro token tenga acceso y click en el botón "Ir al resumen" y botón "Crear token", nos copiamos el token ya que no aparecerá más, ese token lo necesitaremos luego para la variable de entorno CLOUDFLARE_API_TOKEN.

**2** - Instalamos el Docker mediante el docker-compose.yml o mediante la plantilla de Unraid, abajo está la descripción de cada variable.

**3** - Nos vamos a Uptime Kuma y en Ajustes -> Notificaciones, botón "Configurar notificación":

- Tipo de notificación: Webhook
- Nombre sencillo: El nombre que quieras ponerle a la notificación.
- URL Post: La URL con la IP de la máquina donde está corriendo el Docker, el puerto que expones en ese Docker y /api/route, quedando por ejemplo así: http://192.168.6.19:1666/api/route
- Request Body: Preset - application/json

Si ya hemos levantado el Docker y le damos al botón Test nos tiene que salir en los logs del contenedor: [INFO] Prueba desde Uptime Kuma satisfactoria.

**4** - Ahora nos vamos a uno de los monitores que tenemos configurados y que esté chequeando una IP de Cloudflare de las que bloquean cada fin de semana o un servicio nuestro que esté detrás de Cloudflare, editamos y arriba a la derecha en Notificaciones activamos la que acabamos de crear.

Si no quieres esperar al fin de semana y quieres hacer una prueba, activa esa Notificación en algún monitor de algún servicio tuyo que puedas parar y tiene ejecutar toda las opciones definidas, desactivar la opción de proxied y cambiar la IP o sacar del túnel ese registro del DNS dependiendo del tipod e registro (A o CNAME) al hacer DOWN el servicio y a la inversa, cuando el servicio vuelva a estar UP se tiene que activar el proxied, restaurar la IP y volver a meter dentro del túnel ese registro del DNS que teníamos antes del cambio.


### Configuración variables de entorno en fichero .env (renombrar el env-example a .env)

| VARIABLE                | NECESARIA | VERSIÓN | VALOR |
|:----------------------- |:---------:| :------:| :-------------|
| UNIFI_URL               |     ✅    | v0.1.0  | Host/IP del router de Unifi. Importante https Ejemplo: https://192.168.2.20 |
| UNIFI_API_TOKEN         |     ✅    | v0.1.0  | Token para el acceso a Unifi a través de la API.                            |
| NOMBRE_PBR              |     ✅    | v0.1.0  | Nombre de la Policy-Based Routing (PBR) en Unifi que se quiere controlar.   |
| CLIENTE_NOTIFICACION    |     ❌    | v0.3.0  | Cliente de notificaciones. (telegram o discord)                             |
| TELEGRAM_BOT_TOKEN      |     ❌    | v0.2.0  | Token del bot de Telegram.                                                  |
| TELEGRAM_CHAT_ID        |     ❌    | v0.2.0  | ID del chat de Telegram.                                                    |
| DISCORD_WEBHOOK         |     ❌    | v0.3.0  | Discord Webhook.                                                            |
| CLOUDFLARE_API_URL      |     ✅    | v1.0.0  | Por defecto: https://api.cloudflare.com/client/v4                           |
| CLOUDFLARE_API_TOKEN    |     ✅    | v1.0.0  | Token para el acceso a Cloudflare a través de la API.                       |
| DEBUG                   |     ✅    | v0.1.0  | Habilita el modo Debug en el log. (0 = No / 1 = Si)                         |
| TZ                      |     ✅    | v0.1.0  | Timezone (Por ejemplo: Europe/Madrid)                                       |

La VERSIÓN indica cuando se añadió esa variable o cuando sufrió alguna actualización. Consultar https://github.com/unraiders/unifi-pbr-cloudflare/releases

---

  > [!IMPORTANT]
  > Debemos descargar 2 ficheros del repositorio que son necesarios para que funcione el endpoint de Cloudflare y colocarlos en la carpeta que mapeamos como volumen en nuestro docker-compose:
  > - check_ip.txt que contiene las url's donde consultar la dirección IP pública de tu conexión a Internet.
  > - zonas_example.json que renombraremos a zonas.json que es el fichero de configuración para que el endpoint haga lo que nosotros queremos que haga. 
 
 ### Explicación del fichero zonas.json

 La estructura del fichero es la siguiente:

```json
[
    {
        "id_zona": "",
        "nombre": "",
        "contenido_anterior": "",
        "target_cname": "",
        "target_cname_anterior": "",
        "cambiar_proxied": false,
        "cambiar_ip": false
    },
    {
        "id_zona": "",
        "name": "",
        "contenido_anterior": "",
        "target_cname": "",
        "target_cname_anterior": "",
        "cambiar_proxied": false,
        "cambiar_ip": false
    }
]

```
- **id_zona**: Cuando entramos en uno de los dominios que tenemos configurados en Cloudflare, abajo a la derecha tenemos un campo en el apartado API que pone "Id. de zona", copiamos ese código en el valor de este campo.  
- **nombre**: Nuestro nombre de registro A o CNAME en el DNS. por ejemplo: subdominio.dominio.com
- **contenido_anterior**: Utilizado internamente, no rellenar.
- **target_cname**: Si el registro es un tipo CNAME aquí pondremos donde queremos que apunte ese registro una vez lo saquemos del túnel de Cloudflare cuando el servicio que exponemos pasa a DOWN, una vez pase a UP otra vez se recupera el valor anterior (guardado en target_cname_anterior) de ese registro.
- **target_cname_anterior**: Utilizado internamente, no rellenar.
- **cambiar_proxied**: Si queremos que cuando se ejecute el endpoint modifique el proxied de ese registro, cuando el servicio que exponemos pasa a DOWN desactiva el proxied y a la inversa, cuando el servicio que exponemos pasa a UP se activa el proxied a ese registro.
- **cambiar_ip**: Si queremos que cuando se ejecute el endpoint modifique la IP con nuestra IP pública del registro, cuando el servicio que exponemos pasa a DOWN modifica la IP y a la inversa, cuando el servicio que exponemos pasa a UP se recupera la IP anterior (guardado en contenido_anterior) de ese registro.

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
    volumes:
        - tu_ruta_local_del_host:/app/data
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
        - CLIENTE_NOTIFICACION=
        - TELEGRAM_BOT_TOKEN=
        - TELEGRAM_CHAT_ID=
        - DISCORD_WEBHOOK=
        - CLOUDFLARE_API_URL=
        - CLOUDFLARE_API_TOKEN=
        - DEBUG=0
        - TZ=Europe/Madrid
    ports:
        - "1666:1666"
    volumes:
        - tu_ruta_local_del_host:/app/data
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

  > [!IMPORTANT]
  > Si seleccionas Discord como destino de tus notificaciones tienes que crear un webhook en el canal que tengas dentro de tu
  > servidor de Discord, nos vamos dentro de nuestro servidor al canal elegido y le damos a la rueda para editar el canal, una vez 
  > dentro nos vamos a Integraciones -> Webhooks y botón "Nuevo webhook", entramos dentro de el, podemos editar el nombre y el 
  > canal donde publicará ese webhook, ya está, le damos al botón "Copiar URL de webhook" y esa URL la pegamos en la variable 
  > DISCORD_WEBHOOK.

---

---

  > [!IMPORTANT]
  > Ojo si tienes un servicio de DDNS que te actualiza la IP pública cuando cambia tu IP al activar a nivel de router una VPN
  > esta también cambiará y tu IP pública pasará a ser la de la conexión VPN.

---

---

  > [!IMPORTANT]
  > Ojo si eres usuario de trackers privados y el uso de los servicios VPN, es importante saber lo que comporta el uso y 
  > la activación automática de un servicio de VPN a nivel de router, ya que a no ser que lo tengamos separado por VLAN's y
  > a la hora de crear la ruta en Unifi le hayamos excluido específicamente la VLAN donde gestionemos las descargas torrents
  > podemos tener bloqueos, bans y la muerte...

---

Se ha probado en un Unifi Cloud Gateway Ultra OS 4.1.22 y Network 9.0.114

---

Te puedes descargar la imagen del icono desde aquí: https://raw.githubusercontent.com/unraiders/unifi-pbr-cloudflare/master/imagenes/unifi-pbr-cloudflare.png

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