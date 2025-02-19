FROM python:3.12-slim
ENV TZ=America/Sao_Paulo
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install git tzdata -y
RUN echo $TZ > /etc/timezone
RUN dpkg-reconfigure -f noninteractive tzdata
ADD ../strava_bot /app
WORKDIR /app
RUN pip install -r requirements.txt