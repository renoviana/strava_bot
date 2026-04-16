# Integrações de API

## Strava API

### Autenticação

O bot usa OAuth 2.0 do Strava. Cada membro do grupo precisa autorizar o acesso individualmente.

**Fluxo de autorização:**
1. Admin executa `/link` no grupo
2. Bot gera URL: `https://www.strava.com/oauth/authorize?client_id=...&redirect_uri=.../callback/{group_id}`
3. Membro clica e autoriza no Strava
4. Strava redireciona para `REDIRECT_URI` com `code` na query string
5. Backend (externo ao bot) troca o `code` por `access_token` e `refresh_token`
6. Credenciais são salvas em `StravaGroup.membros`

> **Nota:** O endpoint de callback OAuth não está implementado no bot. Precisa ser implementado separadamente.

### Renovação de token

Os tokens do Strava expiram a cada 6 horas. O bot renova automaticamente:

```
sync_activities → fetch_activities → HTTPError 401
    → refresh_access_token() → novo access_token
    → fetch_activities() (retry)
    → salva novo token no banco
```

Endpoint de refresh:
```
POST https://www.strava.com/oauth/token
{
  "client_id": STRAVA_CLIENT_ID,
  "client_secret": STRAVA_CLIENT_SECRET,
  "grant_type": "refresh_token",
  "refresh_token": "<token>"
}
```

### Busca de atividades

```
GET https://www.strava.com/api/v3/athlete/activities
Headers: Authorization: Bearer <access_token>
Params:
  after: <unix timestamp>
  per_page: 50
  page: 1
```

Retorna lista de atividades do atleta autenticado após a data fornecida.

**Limitações:**
- Máximo 50 atividades por chamada (paginação não implementada)
- Rate limit do Strava: 100 req/15min, 1000 req/dia por token

### Campos salvos

O bot salva todos os campos retornados pela API. Os mais usados:

| Campo Strava | Campo no banco | Uso |
|---|---|---|
| `id` | `activity_id` | Chave única |
| `type` | `activity_type` | Tipo legado |
| `sport_type` | `sport_type` | Tipo atual |
| `distance` | `distance` | Ranking de distância |
| `moving_time` | `moving_time` | Ranking de tempo |
| `start_date_local` | `start_date_local` | Filtros por período |
| `map` | `activity_map` | Dados de rota |
| `flagged` | `flagged` | Validação (atividades flagadas são ignoradas) |

---

## Telegram Bot API

### Biblioteca

Usa `pyTelegramBotAPI` (telebot) em modo polling.

### Tipos de handlers

**Message handlers** — respondem a comandos de texto:

```python
@bot.message_handler(commands=["rank"])
def rank_command(message):
    group_id = message.chat.id
    sports = handle_rank_menu(group_id, start, end)
    # exibe inline keyboard com as modalidades
```

**Callback query handlers** — respondem a cliques em botões inline:

```python
@bot.callback_query_handler(func=lambda call: call.data.startswith("rank_"))
def rank_callback(call):
    sport_type = call.data.replace("rank_", "")
    response = handle_rank_month_command(group_id, sport_type)
    bot.send_message(...)
```

### Formatação das respostas

O bot usa `parse_mode="HTML"` para formatar mensagens. Links para perfis do Strava usam:

```html
<a href="https://www.strava.com/athletes/{athlete_id}">{nome}</a>
```

### Configuração necessária

O token do bot é obtido via `@BotFather` no Telegram e configurado na variável `TELEGRAM_TOKEN`.

O bot precisa ser adicionado ao grupo e ter permissão de enviar mensagens.
