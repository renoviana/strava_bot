# Banco de Dados

O projeto usa MongoDB via MongoEngine. Há duas coleções principais.

## Coleções

### strava_group

Uma documento por grupo do Telegram.

| Campo | Tipo | Descrição |
|---|---|---|
| `telegram_group_id` | int | ID do grupo no Telegram |
| `membros` | dict | Dados dos membros (chave = nome do membro) |
| `metas` | dict | Metas do grupo (uso futuro) |
| `medalhas` | dict | Placar de medalhas por mês/modalidade/usuário |
| `segments_ids` | list | IDs de segmentos do Strava (opcional) |
| `last_sync` | datetime | Timestamp da última sincronização |

#### Estrutura de `membros`

```json
{
  "Nome do Membro": {
    "access_token": "...",
    "refresh_token": "...",
    "last_activity_date": "2026-04-15T12:00:00",
    "athlete_id": 12345678
  }
}
```

#### Estrutura de `medalhas`

```json
{
  "2026-01": {
    "Run": {
      "Nome do Membro": 1
    }
  }
}
```

Onde o valor é a posição (1 = ouro, 2 = prata, 3 = bronze).

---

### strava_activity

Uma documento por atividade do Strava.

| Campo | Tipo | Descrição |
|---|---|---|
| `activity_id` | int | ID único da atividade no Strava |
| `group_id` | int | ID do grupo ao qual pertence |
| `athlete` | embedded | Dados do atleta (id, resource_state) |
| `sport_type` | str | Tipo de esporte (Run, Ride, etc.) |
| `activity_type` | str | Tipo de atividade (campo legado) |
| `name` | str | Nome da atividade |
| `distance` | float | Distância em metros |
| `moving_time` | int | Tempo em movimento em segundos |
| `elapsed_time` | int | Tempo total em segundos |
| `start_date_local` | datetime | Data/hora local de início |
| `activity_map` | dict | Dados do mapa (polyline, etc.) |

O modelo armazena todos os campos retornados pela API do Strava (~70 campos).

---

## Consultas principais

### Buscar atividades por período

```python
StravaActivity.get_activities(
    group_id=group_id,
    start=datetime(2026, 4, 1),
    end=datetime(2026, 4, 30),
    member_id_list=[12345, 67890]  # opcional
)
```

### Verificar se atividade já existe

```python
StravaActivity.exists(activity_id=123456789, group_id=group_id)
```

### Listar modalidades com atividade no período

```python
StravaActivity.list_sports(group_id, start_date, end_date)
# retorna: ["Run", "Ride", "Swim"]
```

### Buscar grupo pelo ID do Telegram

```python
StravaGroup.get_group(group_id)
```

---

## Índices recomendados

Para performance em grupos grandes, criar índices compostos:

```javascript
db.strava_activity.createIndex({ group_id: 1, start_date_local: 1 })
db.strava_activity.createIndex({ group_id: 1, "athlete.id": 1 })
db.strava_group.createIndex({ telegram_group_id: 1 })
```
