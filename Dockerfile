FROM python:3.13-alpine

LABEL maintainer="unraiders"
LABEL description="Control enable/disable de rutas basadas en políticas en Unifi a través del servicio de Uptime Kuma enviando un webhook cuando caen los proxys de Cloudflare con notificación a Telegram."

ARG VERSION=0.2.0 
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

RUN chmod +x entrypoint.sh && \
    chown -R tebas_user:tebas_user /app

EXPOSE 1666

USER tebas_user

ENTRYPOINT ["/app/entrypoint.sh"]