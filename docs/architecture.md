# Arquitetura

## Visão geral

O projeto segue uma arquitetura em camadas com separação clara de responsabilidades, inspirada em Clean Architecture.

```
┌────────────────────────────────────────────┐
│              adapters/                     │
│  telegram_bot.py     strava_client.py      │
│  (entrada de comandos)  (chamadas API)     │
└──────────────────┬─────────────────────────┘
                   │
┌──────────────────▼─────────────────────────┐
│             application/                   │
│  commands/           sync_activities.py    │
│  (orquestração)      (sincronização)       │
└──────────────────┬─────────────────────────┘
                   │
┌──────────────────▼─────────────────────────┐
│               domain/                      │
│  rank_service  frequency_service           │
│  streak_service  medal_service             │
│  (regras de negócio puras)                 │
└──────────────────┬─────────────────────────┘
                   │
┌──────────────────▼─────────────────────────┐
│           infrastructure/                  │
│  StravaActivity  StravaGroup  Athlete      │
│  (persistência MongoDB)                    │
└────────────────────────────────────────────┘
```

## Camadas

### adapters/
Integra o bot com sistemas externos. Não contém regras de negócio.

- `telegram_bot.py` — registra handlers de comandos e callbacks do Telegram, delega para `application/`
- `strava_client.py` — encapsula chamadas HTTP para a API do Strava

### application/
Orquestra o fluxo de cada funcionalidade: sincroniza dados, chama serviços de domínio, formata resposta.

- `sync_activities.py` — busca atividades novas no Strava e persiste no banco
- `commands/rank.py` — prepara e formata ranking por distância/tempo
- `commands/frequency.py` — prepara e formata ranking de frequência
- `commands/streak.py` — prepara e formata sequência de dias ativos
- `commands/medal.py` — prepara e formata placar de medalhas
- `commands/admin.py` — gerencia membros do grupo

### domain/
Contém apenas lógica de cálculo, sem dependências externas. Recebe listas de atividades e retorna métricas calculadas.

- `RankService` — soma distância ou tempo por usuário por modalidade
- `FrequencyService` — conta dias únicos com atividade por usuário
- `StreakService` — calcula sequência de dias consecutivos de hoje para trás
- `MedalService` — agrega medalhas e calcula pontuação

### infrastructure/
Modelos MongoEngine que representam as coleções do banco.

- `StravaActivity` — atividade individual do Strava
- `StravaGroup` — grupo do Telegram com membros, credenciais e medalhas
- `Athlete` — documento embarcado com ID do atleta

### shared/
Utilitários reutilizáveis entre camadas.

- `rank.py` — formata string de ranking em HTML para o Telegram
- `user.py` — busca membro pelo ID ou nome

## Fluxo de dados (exemplo: /rank)

```
Telegram → /rank
    ↓ telegram_bot.py
    ↓ handle_rank_month_command()
    ↓ sync_all_activities()        ← busca atividades novas no Strava
    ↓ StravaActivity.get_activities()  ← lê banco
    ↓ RankService.calculate()      ← calcula ranking
    ↓ create_rank()                ← formata HTML
    ↓ bot.send_message()           → Telegram
```

## Decisões de design

**Serviços de domínio stateless**: cada serviço recebe a lista de atividades no construtor e calcula via `calculate()`. Facilita testes unitários sem dependência de banco.

**Sincronização antes de cada consulta**: `sync_all_activities` é chamado antes de qualquer ranking. Tem proteção de rate-limit (ignora se sincronizou há menos de 1 minuto).

**Refresh automático de token**: quando a API do Strava retorna 401, o cliente renova o token e repete a requisição automaticamente.

**Medalhas como dado persistido**: o placar de medalhas é armazenado no documento do grupo (`StravaGroup.medalhas`), não calculado dinamicamente a partir das atividades.
