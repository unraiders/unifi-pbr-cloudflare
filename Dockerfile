FROM python:3.13-alpine

LABEL maintainer="unraiders"
LABEL description="Control enable/disable de rutas basadas en políticas en Unifi a través del servicio de Uptime Kuma enviando un webhook cuando caen los proxys de Cloudflare con notificación a Telegram o Discord y salida del túnel, cambio de estado de proxied e IP en Cloudflare."

ARG VERSION=1.0.0 
ENV VERSION=${VERSION}

RUN apk add --no-cache mc

RUN adduser -D tebas_user

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY utils.py .
COPY config.py .
COPY unifi-pbr-cloudflare.py .
COPY entrypoint.sh .
COPY ip_info.py .
COPY cloudflare_zones.py .

RUN mkdir -p /app/data && \
    chown -R tebas_user:tebas_user /app && \
    chmod +x entrypoint.sh
    
USER tebas_user

EXPOSE 1666

ENTRYPOINT ["/app/entrypoint.sh"]