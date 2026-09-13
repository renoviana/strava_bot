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

> O callback fica no `assistant_api` (`router/strava_router.py`). Ele enfileira o código em `Config "strava_user"`, e o `assistant_schedule` (`add_strava_user_job`) troca o código pelos tokens.

### Sync (`assistant_util.strava.sync_group`)

É o mesmo caminho para o bot e para o `assistant_schedule`. A cada sync, para cada membro:

1. Busca as atividades iniciadas nos últimos 7 dias (ou desde `since`, por exemplo o dia 1 no `/reset` e no fechamento do mês), **paginando até o fim**.
2. Faz **upsert** de cada uma por `(activity_id, group_id)`. Edição no Strava sobrescreve, e `flagged` é removida.
3. Remove da janela o que não voltou na busca (apagado ou tornado privado). Isso só acontece se a busca terminou sem erro.

Não existe mais cursor. O antigo guardava a data de início da última atividade baixada, e como o `after` do Strava filtra pela data de *início*, upload atrasado nunca era baixado.

A falha de um membro é registrada via `tratar_error` e não impede o sync dos outros.

### Renovação de token

Os tokens do Strava expiram a cada 6 horas. O sync renova automaticamente:

```
fetch_activities → HTTPError 401
    → refresh_access_token() → novo access_token (e talvez novo refresh_token)
    → grava na hora, em todos os grupos do atleta
    → fetch_activities() (retry)
```

O Strava invalida o refresh_token antigo quando emite um novo. Por isso o token é gravado antes de qualquer outra coisa e em todas as cópias do atleta.

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
  after: <unix timestamp, UTC>
  per_page: 200
  page: 1, 2, ... (até vir uma página incompleta)
```

Retorna as atividades do atleta autenticado iniciadas depois da data fornecida.

**Limitações:**
- O rate limit do Strava é de 100 req/15min e 1000 req/dia por app. Na prática gasta 1 requisição por membro por sync, e o bot espera no mínimo 1 minuto entre syncs do mesmo grupo.
- Atividades privadas ("só eu") não vêm com o escopo `activity:read`.

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
@seguro
def rank_month_callback_handler(call):
    sport_type = call.data.split("_", 1)[1]
    _responder(call.message.chat.id, handle_rank_month_command(call.message.chat.id, sport_type))
```

Todo handler passa pelo `@seguro`. Uma exceção vai para o `tratar_error`, o chat recebe um aviso e, em callback, o `answer_callback_query` é sempre chamado.

### Formatação das respostas

O bot usa `parse_mode="HTML"` para formatar mensagens. Links para perfis do Strava usam:

```html
<a href="https://www.strava.com/athletes/{athlete_id}">{nome}</a>
```

### Configuração necessária

O token do bot é obtido via `@BotFather` no Telegram e configurado na variável `TELEGRAM_TOKEN`.

O bot precisa ser adicionado ao grupo e ter permissão de enviar mensagens.
