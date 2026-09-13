# Banco de Dados

O projeto usa MongoDB via MongoEngine, com os models e CRUDs do **`assistant_model`**:
- models: `StravaGroup` e `StravaActivity`;
- CRUD: `crud/strava.py`.

O bot não tem models próprios (regra 3 do CLAUDE.md). A conexão usa o alias `assistant-db`.

## Coleções

### strava_group

Um documento por grupo do Telegram.

| Campo | Tipo | Descrição |
|---|---|---|
| `telegram_group_id` | int | ID do grupo no Telegram |
| `membros` | dict | Dados dos membros (chave = nome do membro) |
| `metas` | dict | Metas do grupo (uso futuro) |
| `medalhas` | dict | Placar de medalhas por mês/modalidade/atleta |
| `segments_ids` | list | IDs de segmentos do Strava (opcional) |
| `last_sync` | datetime | Último sync (UTC, naive) |

#### Estrutura de `membros`

```json
{
  "Nome do Membro": {
    "access_token": "...",
    "refresh_token": "...",
    "athlete_id": 12345678
  }
}
```

- `last_activity_date` (legado): era o cursor do sync antigo. Pode existir em documentos antigos, mas é ignorado.
- O mesmo atleta pode estar em mais de um grupo. O token renovado é gravado em todos (`update_strava_member_tokens`).
- Dois atletas com o mesmo nome colidem na chave. No cadastro, o segundo ganha o sufixo ` (<athlete_id>)`.

#### Estrutura de `medalhas`

```json
{
  "8_2026": {
    "Ride": {
      "12345678": 1
    }
  }
}
```

A chave do mês é `"<mes>_<ano>"`, e o valor é a posição (1 = ouro, 2 = prata, 3 = bronze).

- **Formato atual:** a chave do atleta é `str(athlete_id)`.
- **Formato legado:** usa o nome do membro. O bot lê os dois formatos, e `assistant_model/scripts/migrate_medalhas_athlete_id.py` converte.
- **Quem grava:** as medalhas são gravadas pelo fechamento do mês no `assistant_schedule/strava_schedule`.

---

### strava_activity

Um documento por atividade do Strava **por grupo**. O índice único é `(activity_id, group_id)`.

| Campo | Tipo | Descrição |
|---|---|---|
| `activity_id` | int | ID da atividade no Strava |
| `group_id` | int | ID do grupo ao qual pertence |
| `athlete` | embedded | Dados do atleta (id, resource_state) |
| `sport_type` | str | Tipo de esporte (Run, Ride, etc.) |
| `activity_type` | str | Tipo de atividade (campo legado) |
| `name` | str | Nome da atividade |
| `distance` | float | Distância em metros |
| `moving_time` | int | Tempo em movimento em segundos |
| `elapsed_time` | int | Tempo total em segundos |
| `start_date` | datetime | Início em UTC |
| `start_date_local` | datetime | Início na hora local do atleta (filtros por período) |
| `activity_map` | dict | Dados do mapa (polyline, etc.) |

O modelo armazena todos os campos retornados pela API do Strava (~70 campos). A gravação é **upsert**: uma edição feita no Strava sobrescreve a versão salva no próximo sync.

---

## Consultas principais (`assistant_model.crud.strava`)

```python
list_strava_activities(group_id, start, end, athlete_ids=[12345, 67890])
list_strava_sports(group_id, start, end)          # ["Run", "Ride", ...]
get_strava_group(group_id)
remove_strava_member(group_id, athlete_id)        # membro + medalhas + atividades
```

No bot, o acesso passa por `infrastructure/strava_repository.py`.

## Índices

Declarados no `assistant_model` (`StravaActivity.meta["indexes"]`) e aplicados por `assistant_model/scripts/manage_indexes.py`:

- `strava_activity`: `(activity_id, group_id)` único; `(group_id, -start_date_local)`
- `strava_group`: `telegram_group_id`
