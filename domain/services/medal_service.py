PONTOS = {1: 3, 2: 2, 3: 1}


class MedalService:
    """
    Placar de medalhas: soma as posições de todos os meses e esportes.

    As medalhas são chaveadas por athlete_id (str). Dado legado usa o nome do
    membro: é resolvido para o athlete_id via `membros`; nome que não é mais
    membro fica de fora.
    """

    def __init__(self, medalhas: dict, membros: dict):
        self.medalhas = medalhas
        self.membros = membros

    def _athlete_id(self, chave):
        if isinstance(chave, int):
            return chave
        if isinstance(chave, str) and chave.isdigit():
            return int(chave)
        membro = self.membros.get(chave)
        return membro.get("athlete_id") if membro else None

    def calculate(self) -> dict:
        """
        Returns:
            dict: {athlete_id: {1: ouros, 2: pratas, 3: bronzes, "points": pontos}},
            do maior para o menor número de pontos
        """
        placar = {}
        for esportes in self.medalhas.values():
            for posicoes in esportes.values():
                for chave, posicao in posicoes.items():
                    athlete_id = self._athlete_id(chave)
                    try:
                        posicao = int(posicao)
                    except (TypeError, ValueError):
                        continue
                    if athlete_id is None or posicao not in PONTOS:
                        continue

                    atleta = placar.setdefault(athlete_id, {1: 0, 2: 0, 3: 0, "points": 0})
                    atleta[posicao] += 1
                    atleta["points"] += PONTOS[posicao]

        return dict(sorted(placar.items(), key=lambda x: x[1]["points"], reverse=True))
