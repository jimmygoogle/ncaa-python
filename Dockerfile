FROM python:3.8-alpine

COPY requirements.txt /

RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev libressl-dev \
  && pip install -r /requirements.txt \
  && apk del .build-deps gcc musl-dev libffi-dev libressl-dev

COPY . /app
WORKDIR /app

COPY . .