import mongoengine

from application.commands.frequency import handle_frequency_command
from application.commands.rank import handle_rank_command
from application.commands.streak import handle_streak_command
from config import MONGO_URI



mongoengine.connect(host=MONGO_URI)
# data = handle_frequency_command(-1001964162405)
# sport_type = "Ride"
# rank = handle_rank_command(-1001964162405, sport_type)
streak = handle_streak_command(-1001964162405)
pass
# strava_client = StravaClient()
# data = strava_client.fetch_activities("54c0c904a8498b044112c4e7055ead36d215fa45", after_days=30, per_page=50)
# service = FrequencyService(data)
# result = service.calculate()
# pass