# Desenvolvimento

## Setup do ambiente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Crie um arquivo `config.py` na raiz com as variáveis de ambiente (ou configure via `.env`):

```python
import os

MONGO_URI = os.environ["MONGO_URI"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
STRAVA_CLIENT_ID = os.environ["STRAVA_CLIENT_ID"]
STRAVA_CLIENT_SECRET = os.environ["STRAVA_CLIENT_SECRET"]
REDIRECT_URI = os.environ["REDIRECT_URI"]
```

## Rodando os testes

```bash
pytest tests/
```

Os testes unitários usam mocks e não precisam de MongoDB ou API do Strava.

## Estrutura de um serviço de domínio

Todos os serviços seguem o mesmo padrão:

```python
class ExampleService:
    def __init__(self, activities: list):
        self.activities = activities

    def calculate(self) -> list:
        # agrega dados por usuário
        # retorna lista ordenada de (user_id, valor)
        ...
```

Para adicionar um novo serviço:
1. Crie `domain/services/example_service.py`
2. Escreva o teste em `tests/unit/test_example_service.py`
3. Crie o handler em `application/commands/example.py`
4. Registre o comando em `adapters/telegram/telegram_bot.py`

## Adicionando um novo comando

### 1. Handler em application/commands/

```python
# application/commands/example.py
from application.sync_activities import sync_all_activities
from infrastructure.mongo.strava_activity import StravaActivity
from domain.services.example_service import ExampleService
from shared.rank import create_rank

def handle_example_command(group_id) -> str:
    sync_all_activities(group_id)
    activities = StravaActivity.get_activities(group_id, start, end)
    result = ExampleService(activities).calculate()
    return create_rank("Título", result, group)
```

### 2. Registro no telegram_bot.py

```python
@bot.message_handler(commands=["example"])
def example_command(message):
    group_id = message.chat.id
    response = handle_example_command(group_id)
    bot.send_message(group_id, response, parse_mode="HTML")
```

## Linting

O projeto usa pylint. Configuração em `.pylintrc`.

```bash
pylint adapters application domain infrastructure shared
```

## Pontos de extensão

- **Webhook em vez de polling**: substituir `bot.polling()` por `bot.process_new_updates()` com um endpoint HTTP
- **Paginação do Strava**: o `strava_client.py` busca apenas a primeira página (50 atividades). Para sincronizar tudo, implementar loop de paginação
- **Callback OAuth**: falta o endpoint que recebe o código do Strava após autorização e salva as credenciais no banco
- **Notificações automáticas**: enviar ranking automaticamente em horários configurados usando APScheduler ou similar
