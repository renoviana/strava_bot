FROM python:3.12-slim
RUN apt update && apt install git -y
COPY ../telebot_tools /app/telebot_tools
ADD ../strava_bot /app
WORKDIR /app
RUN pip install -r requirements.txt