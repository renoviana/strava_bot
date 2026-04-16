# Strava Bot

Bot do Telegram que integra com a API do Strava para criar rankings competitivos de atividades físicas em grupos.

## O que faz

- Sincroniza atividades de todos os membros do grupo via API do Strava
- Calcula rankings por distância ou tempo por modalidade
- Rastreia frequência de treinos, sequências (streaks) e medalhas
- Exibe rankings formatados diretamente no Telegram

## Comandos disponíveis

| Comando | Descrição |
|---|---|
| `/rank` | Ranking do mês atual por modalidade |
| `/yrank` | Ranking do ano atual por modalidade |
| `/frequency` | Frequência de treinos no mês atual |
| `/yfrequency` | Frequência de treinos no ano atual |
| `/streak` | Sequência de dias consecutivos com atividade |
| `/medalhas` | Placar de medalhas acumuladas |
| `/link` | Gera link OAuth para autorizar membro no grupo |
| `/admin` | Remove membro do grupo |
| `/reset` | Redefine data de última atividade para o 1º do mês |

## Início rápido

### Pré-requisitos

- Docker
- MongoDB
- Conta de desenvolvedor no Strava (para Client ID e Client Secret)
- Token de bot no Telegram

### Variáveis de ambiente

```env
MONGO_URI=mongodb://localhost:27017/strava_bot
TELEGRAM_TOKEN=<token-do-bot>
STRAVA_CLIENT_ID=<client-id-strava>
STRAVA_CLIENT_SECRET=<client-secret-strava>
REDIRECT_URI=https://seu-dominio.com/callback/{}
```

### Rodando com Docker

```bash
docker build -t strava_bot .
docker run --env-file .env strava_bot
```

### Rodando localmente

```bash
pip install -r requirements.txt
python bot.py
```

## Estrutura do projeto

```
strava_bot/
├── adapters/           # Integrações externas (Strava API, Telegram)
├── application/        # Handlers de comandos e sincronização
├── domain/             # Serviços de negócio (cálculos de rank, streak, etc.)
├── infrastructure/     # Modelos do MongoDB
├── shared/             # Utilitários de formatação e busca
├── tests/              # Testes unitários
└── bot.py              # Ponto de entrada
```

Veja [architecture.md](architecture.md) para detalhes de design e [deployment.md](deployment.md) para guia completo de deploy.
