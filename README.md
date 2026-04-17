# Strava Bot

Bot de Telegram especializado em integração com o Strava para monitoramento, análise e gamificação de atividades físicas (Corrida, Ciclismo, etc).

**Telegram:** [@brstravabot] (Privado)  
**Stack:** Python · Clean Architecture · MongoDB · Strava API · Docker

---

## Principais Funcionalidades

### 🏆 Gamificação & Estatísticas
- **Rankings:** Classificações por distância, ganho de elevação ou tempo, filtradas por tipo de esporte e período.
- **Medalhas:** Sistema de conquistas baseadas em marcos históricos e metas alcançadas.
- **Streaks:** Acompanhamento de sequências de dias consecutivos de atividades.
- **Frequência:** Análise de constância e volume semanal/mensal.

### 🔄 Sincronização
- **Auto-Sync:** Sincronização automática das atividades do Strava para o banco de dados local via use cases de aplicação.
- **Notificações:** Alertas sobre novas atividades e marcos batidos no grupo.

---

## Arquitetura

O projeto segue os princípios da **Clean Architecture**, garantindo que as regras de negócio sejam independentes de detalhes externos como o banco de dados ou a API do Telegram.

- **Domain:** Regras de negócio puras (Serviços de Ranking, Medalhas, etc).
- **Application:** Casos de uso e lógica de comandos do bot.
- **Infrastructure:** Implementações concretas de banco de dados (MongoDB).
- **Adapters:** Interfaces com o mundo externo (Telegram Bot API).

---

## Rodando Localmente

### Pré-requisitos
- Python 3.10+
- Imagem base `assistant-base-python` (ou dependências equivalentes: `telebot`, `mongoengine`).

### Instalação

```bash
# Instalar dependências (se não estiver usando a imagem base)
pip install -r requirements.txt
```

### Execução

```bash
python bot.py
```

---

## Estrutura do Projeto

```
bot.py              # Entry point do bot
adapters/           # Implementações de frameworks e drivers (Telegram API)
application/        # Casos de uso, comandos e lógica de sincronização
domain/             # Entidades e serviços de negócio (Núcleo)
infrastructure/     # Persistência de dados (MongoDB)
shared/             # Utilitários compartilhados no projeto
```

> Para detalhes sobre os padrões de desenvolvimento, veja `CLAUDE.md`.
