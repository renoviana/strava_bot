# CLAUDE.md — AI-First Rules for Strava Bot

<!-- BEGIN regras-ecossistema: bloco idêntico em todos os repos do ecossistema; fonte e versão completa no CLAUDE.md da pasta raiz do ecossistema. Altere em todos juntos. -->
## Regras do ecossistema Assistant (valem para qualquer alteração)

Este projeto faz parte do ecossistema `assistant_*` (api, bot, mcp, model,
promotion, schedule, scrap, ui, util) e dos repos irmãos (`carros_app`,
`carros_mcp`, `metro_bot`, `soro_bot`, `posto_bot`, `strava_bot`, `weednotifier`).
As regras abaixo são comuns a todos. As seções seguintes deste arquivo
acrescentam regras específicas deste projeto; em conflito, vale a mais restritiva.

1. **AI-first: plano aprovado antes de qualquer código.** Todo ajuste, correção,
   feature, refactor ou melhoria, mesmo de uma linha, exige plano.
   - Layout de `docs/plans/TEMPLATE.md`, ou o mesmo layout se o projeto não
     tiver o arquivo: projetos afetados, objetivo, arquivos por projeto, fluxo,
     decisões e riscos, testes, checklist.
   - Única exceção: edição só de documentação.
   - Responder perguntas do plano **não** é aprovação: reescreva o plano e peça
     confirmação.
   - Só implemente após **`aprovar`** (ou "aprovado", "pode seguir", "vamos em
     frente"). `reprovar`, "não" ou "cancela" descartam o plano.
   - O plano aprovado vai para `docs/plans/YYYY-MM-DD_nome.md` em cada projeto
     afetado, no mesmo commit da implementação.
2. **Testes.** Feature nova ganha teste, e comportamento alterado exige ajustar os
   testes. A suite inteira precisa passar antes de concluir (e o `flake8`, se
   configurado). Sem rede nem banco reais: use mocks.
3. **Documentação no mesmo commit.** `docs/`, `README.md` e `CLAUDE.md`/`AGENTS.md`
   refletem a mudança. Sem changelogs nem `.md` avulsos.
4. **Mudou aqui, verifica lá.** Mudança em model, CRUD, lib ou contrato só termina
   quando os projetos consumidores estão consistentes. Libs mantêm compatibilidade
   retroativa: campo novo entra com `default`, e nada é removido ou renomeado sem
   migração.
   - **Nome público é contrato.** Document, coleção, módulo, função e campo de
     lib já existentes nunca são reaproveitados para outro propósito: entidade
     nova ganha nome novo (`Gasto` de viagem sobrescreveu o `/gastos` do bot e
     derrubou o bot em 2026-11-01).
   - **Busca de consumidores no plano.** Antes de mudar, remover, renomear ou
     reescrever um nome público, busque os usos em todos os repos do ecossistema
     (`gh api -X GET search/code -f q='<nome> user:renoviana'` ou grep nos
     clones) e liste no plano cada uso encontrado e o que acontece com ele. Plano
     sem essa busca não está pronto para aprovação.
   - **Módulo existente só ganha.** Em arquivo de lib que outro projeto importa,
     acrescente; não troque o conteúdo. Função removida, renomeada ou com
     assinatura incompatível exige a migração dos consumidores no mesmo plano.
   - **Import quebrado falha no CI, não em produção.** Todo consumidor tem teste
     que importa todos os seus módulos (comandos, routers, jobs), e a lib tem
     teste do contrato que cada consumidor importa.
5. **Commits direto na `main`**, sem branch nem PR, depois de os testes passarem.
   - Um commit por repositório afetado.
   - Mensagem em português no estilo do histórico:
     `feat:`/`fix:`/`perf:`/`docs:`/`refactor:`/`test:` + o comportamento
     resultante.
   - Push e deploy só quando o usuário pedir: push na `main` de um repo com
     `deploy.yml` já faz o deploy dele. Nunca `--no-verify` nem force push.
6. **Convenções.** Docstrings, comentários, logs, mensagens, docs e commits em
   português (Brasil). Identificadores seguem a convenção do projeto. Segredos só
   por variável de ambiente. Use os caminhos únicos:
   - `assistant_send`;
   - `tratar_error(..., job_tag=)`;
   - `historico_job`;
   - `assistant_scrap.tools`;
   - `criar_client_gemini`;
   - CRUDs do `assistant_model`.
7. **Cada projeto na sua competência.**
   - **Donos:**
     - toda extração de dados da web é do `assistant_scrap`;
     - todo acesso a banco (Documents, CRUDs, queries, índices) é do
       `assistant_model`;
     - infra transversal (segredos, mensageria, erro, histórico) é do
       `assistant_util`.
   - `api`, `bot`, `mcp` e `schedule` só orquestram e aplicam regra de negócio.
     `assistant_ui` só consome a API.
   - Publicar ou enviar (Telegram, Bluesky, Discord) não é extração.
   - **Exceção única:** o `assistant_promotion` é um sistema à parte, com scrap e
     models próprios.
   - **Coleção declarada em mais de um projeto** (espelhos do `assistant_promotion`,
     models do `assistant_util`): todas as declarações levam `"strict": False` no
     `meta`. O schema nasce no dono, e o espelho replica **todos** os campos dele,
     com os mesmos tipos e defaults, sem `indexes` (índice é do dono). Campo novo
     entra no dono e em todos os espelhos no mesmo plano. Rename, remoção, troca de
     tipo, `db_alias` ou nome da coleção mudam em todas as declarações juntas.
8. **Problema encontrado é problema nosso.** Todo o ecossistema foi feito por
   nós: não existe "já estava quebrado". Teste falhando, erro de coleta, bug
   ou código com problema encontrado em qualquer tarefa entra no levantamento,
   seja pré-existente ou não.
   - Levante a causa e o ajuste de cada problema.
   - Preveja o ajuste: no plano da tarefa atual, quando couber, ou num plano
     próprio proposto na mesma entrega.
   - Nunca encerre a tarefa só registrando que a falha é pré-existente.

> **Regra de ouro:** nunca altere código sem plano aprovado. Nunca finalize sem
> testes passando, docs atualizadas, projetos relacionados consistentes, cada coisa
> no projeto dono, commit na `main` e todo problema encontrado levantado, com
> ajuste previsto.
<!-- END regras-ecossistema -->

---


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

---

## Deploy

- `docker-compose.yml` deste repo: serviço `strava_bot` (`python3 -u bot.py`), imagem `strava-bot` sobre a
  `assistant-base-python` (o `Dockerfile` só faz `COPY`), rede externa `webnet`, `.env` único em `../.env`.
- **Push na `main` já faz o deploy** (`.github/workflows/deploy.yml`: SSH, `git pull`, checagem de espaço com limpeza automática pelo `assistant_bot/scripts/deploy_compose.sh`, `docker-compose build` e
  `up -d`, sem `down` em `assistant_project/strava_bot`). Push só quando o usuário pedir.
- O sync do Strava é o caminho único do `assistant_util` (`StravaClient` + `sync_group`), compartilhado com o
  `strava_schedule`. Mudança lá ou no `assistant_model` só chega aqui depois do *Update Base Image* do
  `assistant_bot` e de um novo deploy deste repo.
- Testes: `python -m pytest` (`tests/`).
