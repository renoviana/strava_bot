
class MedalService:
    def __init__(self, group):
        self.group = group

    def calculate(self) -> dict:
        points_dict = {
            1: 3,
            2: 2,
            3: 1
        }
        medalhas = self.group.medalhas
        user_dict = {}
        for sport_ride_data in medalhas.values():
            for medal_data in sport_ride_data.values():
              for user_id, user_data in medal_data.items():
                if user_id not in user_dict:
                      user_dict[user_id] = {
                          1:0,
                          2:0,
                          3:0,
                          "points":0
                  }

                user_dict[user_id][user_data] += 1
                user_dict[user_id]["points"] += points_dict.get(user_data, 0)
        sorted_users = sorted(user_dict.items(), key=lambda x: x[1]["points"], reverse=True)
        return {user[0]: user[1] for user in sorted_users}