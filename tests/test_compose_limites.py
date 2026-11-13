"""Todo serviço do docker-compose.yml tem limite de memória (plano 2026-11-13_gestao_de_recursos_do_servidor).

Sem limite, um serviço que cresce empurra os outros containers do Raspberry Pi (3,7 GB de RAM) para o swap.
Lido como texto, sem pyyaml, que não está nos requirements.
"""
import re
from pathlib import Path

COMPOSE = next(
    p / "docker-compose.yml" for p in Path(__file__).resolve().parents if (p / "docker-compose.yml").exists()
)


def _servicos():
    servicos, atual, dentro = {}, None, False
    for linha in COMPOSE.read_text(encoding="utf-8").splitlines():
        if re.match(r"^services:\s*$", linha):
            dentro = True
            continue
        if re.match(r"^\S", linha):
            dentro = False
        nome = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", linha)
        if dentro and nome:
            atual = nome.group(1)
            servicos[atual] = False
        elif dentro and atual and re.match(r"^\s+(mem_limit|memory):", linha):
            servicos[atual] = True
    return servicos


def test_todo_servico_tem_limite_de_memoria():
    servicos = _servicos()
    assert servicos
    assert [nome for nome, limitado in servicos.items() if not limitado] == []
