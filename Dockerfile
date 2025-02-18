FROM python:3.12-slim
RUN apt update && apt install git -y
ADD ../strava_bot /app
WORKDIR /app
RUN pip install -r requirements.txt