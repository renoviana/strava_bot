from datetime import datetime
from collections import defaultdict

class RankService:
    sport_rank_by_time_list = [
        "workout",
        "weighttraining",
        "velomobile",
        "standuppaddling",
        "yoga",
        "stairstepper",
        "pilates",
    ]


    def __init__(self, activities: list):
        self.activities = activities

    def get_rank_type(self):
        if self.sport_type.lower() in self.sport_rank_by_time_list:
            return "moving_time"
        return "distance"

    def calculate(self, sport_type: str):
        self.sport_type = sport_type
        self.rank_params = self.get_rank_type()

        user_rank = {}

        for act in self.activities:
            if act['sport_type'] != self.sport_type:
                continue

            user_id = act.athlete.id
            rank_params = getattr(act, self.rank_params)

            if not user_id in user_rank:
                user_rank[user_id] = 0

            user_rank[user_id] += rank_params

        return sorted(user_rank.items(), key=lambda x: x[1], reverse=True)
        

    def list_sports(self):
        return list(set([act.sport_type for act in self.activities]))