FROM assistant-base-python:latest
WORKDIR /app
# Todas as dependencias (libs git + PyPI) ja estao assadas na imagem base.
COPY . .
