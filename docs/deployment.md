# Deploy

## Requisitos

- Docker (recomendado)
- MongoDB 4.4+
- Imagem base `assistant-base-python:latest` disponível no host
- Conta de desenvolvedor no Strava
- Bot criado via @BotFather no Telegram

## Variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
MONGO_URI=mongodb://<host>:27017/strava_bot
TELEGRAM_TOKEN=<token-do-botfather>
STRAVA_CLIENT_ID=<id-do-app-strava>
STRAVA_CLIENT_SECRET=<secret-do-app-strava>
REDIRECT_URI=https://seu-dominio.com/callback/{}
```

> `REDIRECT_URI` deve conter `{}` — será substituído pelo `group_id` ao gerar o link OAuth.

## Com Docker

```bash
# Build
docker build -t strava_bot .

# Run
docker run -d \
  --name strava_bot \
  --env-file .env \
  --restart unless-stopped \
  strava_bot
```

## Localmente

```bash
pip install -r requirements.txt
python bot.py
```

## Configuração do Strava App

1. Acesse https://www.strava.com/settings/api
2. Crie um app e anote `Client ID` e `Client Secret`
3. Configure o **Authorization Callback Domain** com o domínio do seu servidor
4. O `REDIRECT_URI` deve apontar para um endpoint que processa o código OAuth e salva as credenciais no MongoDB

## Configuração inicial do grupo

1. Adicione o bot ao grupo do Telegram
2. Execute `/link` para gerar o link OAuth
3. Cada membro que quiser participar deve abrir o link e autorizar o Strava
4. Após autorizar, as credenciais são salvas e o membro aparece nos rankings

## Monitoramento

O bot roda em polling contínuo. Logs de erro são impressos no stdout.

Para reiniciar automaticamente em caso de falha:

```bash
docker run -d --restart unless-stopped --name strava_bot ...
```

## Banco de dados

O MongoDB pode ser local ou hospedado (MongoDB Atlas, etc.). Exemplo com Atlas:

```env
MONGO_URI=mongodb+srv://user:password@cluster.mongodb.net/strava_bot
```

Para performance em grupos com muitos membros, crie os índices recomendados em [database.md](database.md).
