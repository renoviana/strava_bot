cd strava_bot && git pull && cd ..
docker compose down strava_bot
docker compose rm -f strava_bot
docker compose build strava_bot
docker compose up -d strava_bot