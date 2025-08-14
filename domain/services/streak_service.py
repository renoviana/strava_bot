from datetime import datetime, timedelta

class StreakService:
    def __init__(self, activities: list):
        self.activities = activities

    def calculate(self):
        user_streak = {}
        streak_result = []
        today = datetime.now().date()
        for act in self.activities:
            user_id = act.athlete.id
            date_str = act["start_date_local"]
            date_obj = date_str if isinstance(date_str, datetime) else datetime.fromisoformat(date_str)
            day = date_obj.date()

            if user_id not in user_streak:
                user_streak[user_id] = {}

            user_streak[user_id][day] = True

        for user_id, streak_days in user_streak.items():
            today = datetime.now().date()
            streak = 0
            while today in streak_days.keys():
                streak += 1
                today -= timedelta(days=1)

            if streak == 0:
                continue

            streak_result.append((user_id, streak))
        sorted_streak_result = sorted(streak_result, key=lambda x: x[1], reverse=True)
        return sorted_streak_result