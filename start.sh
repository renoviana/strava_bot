cd strava_bot && git pull && cd ..
killall screen
docker compose down
docker compose build
screen -d -m -S docker bash -c  "docker compose up -d"