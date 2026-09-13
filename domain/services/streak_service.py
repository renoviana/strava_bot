from datetime import date, datetime, timedelta


def _dia(valor) -> date:
    data = valor if isinstance(valor, datetime) else datetime.fromisoformat(valor)
    return data.date()


class StreakService:
    """
    Sequência de dias seguidos com atividade, contando de `today` para trás.

    `today` é injetado: o "hoje" é o de Brasília, e quem sabe disso é a camada
    de aplicação.
    """

    def __init__(self, activities: list, today: date):
        self.activities = activities
        self.today = today

    def calculate(self) -> list:
        """
        Returns:
            list[tuple[int, int]]: (athlete_id, dias seguidos), do maior para o
            menor; quem não treinou em `today` fica de fora
        """
        dias_por_atleta = {}
        for act in self.activities:
            dias_por_atleta.setdefault(act.athlete.id, set()).add(_dia(act["start_date_local"]))

        streak_result = []
        for athlete_id, dias in dias_por_atleta.items():
            dia = self.today
            streak = 0
            while dia in dias:
                streak += 1
                dia -= timedelta(days=1)

            if streak:
                streak_result.append((athlete_id, streak))

        return sorted(streak_result, key=lambda x: x[1], reverse=True)
