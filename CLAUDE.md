# CLAUDE.md — AI-First Rules for Strava Bot

## Project Overview

Specialized Strava integration bot for Telegram. It follows a strict Clean Architecture pattern to separate domain logic from external frameworks. Its main goal is to provide rankings and gamified statistics for a group of athletes.

---

## AI-First Rules

### 0. Plano Antes de Qualquer Desenvolvimento
Toda nova feature ou alteração arquitetural requer um plano aprovado. O plano deve identificar em qual camada da Clean Architecture a mudança reside (Domain, Application, Infrastructure ou Adapters).

### 1. Respeito à Clean Architecture
- **Domain:** Não deve importar nada de outras camadas. Contém apenas serviços de negócio (`RankService`, `MedalService`).
- **Application:** Contém comandos do bot e casos de uso de sincronização.
- **Infrastructure:** Contém apenas repositórios e conexões com DB.
- **Adapters:** Contém o driver do Telegram. **Não coloque lógica de negócio nos adapters.**

### 2. Adição de Novos Rankings ou Regras
Novas métricas ou regras de medalhas devem ser implementadas primeiro no `domain/services/` com testes unitários, e depois expostas via comandos em `application/commands/`.

### 3. Integração com Strava
Utilize os modelos de dados já estabelecidos em `assistant_model` para persistir atividades. Não crie novos esquemas de banco de dados locais para dados que já existem no ecossistema compartilhado.

### 4. Gestão de Estado e Sync
A sincronização deve ser idempotente. Nunca duplique atividades no banco de dados durante processos de sync.

---

## Guia de Desenvolvimento

### Fluxo de um Comando
1. `Adapter` (Telegram) recebe a mensagem.
2. `Adapter` chama o `Application Command`.
3. `Command` usa um `Domain Service` para calcular os dados.
4. `Command` retorna a resposta formatada para o `Adapter`.

### Adicionando um Novo Comando
1. Implemente a lógica de negócio no `domain/` (se necessário).
2. Crie o comando em `application/commands/`.
3. Registre o comando no roteador do bot em `adapters/telegram/telegram_bot.py`.

### Regras de Ouro
- **No Framework Leak:** O domínio nunca deve saber que o Telegram existe.
- **Dependency Injection:** Prefira passar dependências (repositórios, serviços) via construtor ou parâmetros para facilitar testes.
- **Testing:** O domínio deve ter 100% de cobertura de testes unitários.
