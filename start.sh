cd strava_bot && git pull && cd ..
screen -X -S strava_bot quit
screen -d -m -S strava_bot bash -c  "cd strava_bot && python3 bot.py"