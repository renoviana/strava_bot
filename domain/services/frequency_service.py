from datetime import datetime
from collections import defaultdict

class FrequencyService:
    def __init__(self, activities: list):
        self.activities = activities

    def calculate(self):
        user_days = defaultdict(set)

        for act in self.activities:
            user_id = act.athlete.id
            date_str = act["start_date_local"]
            date_obj = date_str if isinstance(date_str, datetime) else datetime.fromisoformat(date_str)
            day = date_obj.date()
            user_days[user_id].add(day)

        ranking = sorted(user_days.items(), key=lambda x: len(x[1]), reverse=True)
        return [(user_id, len(days)) for user_id, days in ranking]
