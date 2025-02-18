from python:3.12-slim
COPY ../telebot_tools /app/telebot_tools
ADD ../strava_bot /app
WORKDIR /app
RUN pip install -e ./telebot_tools
RUN pip install -r requirements.txt