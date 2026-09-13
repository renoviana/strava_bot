class RankService:
    """
    Soma a métrica de um esporte por atleta.

    A métrica ("distance" ou "moving_time") vem de fora: a regra de qual
    esporte é ranqueado por tempo é compartilhada com o fechamento de medalhas
    do strava_schedule (`assistant_util.strava.rank_metric`).
    """

    def __init__(self, activities: list):
        self.activities = activities

    def calculate(self, sport_type: str, metric: str) -> list:
        """
        Returns:
            list[tuple[int, float]]: (athlete_id, total), do maior para o menor
        """
        totals = {}
        for act in self.activities:
            if act.sport_type != sport_type:
                continue
            athlete_id = act.athlete.id
            totals[athlete_id] = totals.get(athlete_id, 0) + (getattr(act, metric) or 0)

        return sorted(totals.items(), key=lambda x: x[1], reverse=True)
