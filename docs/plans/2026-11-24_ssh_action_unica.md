# Plano: appleboy/ssh-action fixada por versão no lugar do nekiro/ssh-job

- **Data:** 2026-11-24
- **Status:** aprovado

## Projetos afetados

Workflows de `assistant_api`, `assistant_bot` (`deploy.yml`, `checkservice.yml`, `update_base_image.yml`),
`assistant_promotion`, `assistant_schedule`, `carros_app`, `danibproject`, `metro_bot`, `posto_bot`, `site_podas`,
`soro_bot`, `strava_bot`, `viagem_app` e `weednotifier`. Nenhuma lib muda; não há impacto em consumidores.

## Objetivo

- Uma action de SSH só no ecossistema.
- Sair do runtime Node 20 (o `nekiro/ssh-job` declara `using: node20`; o GitHub já força o Node 24 e avisa a cada run).
- Fixar a action pelo SHA do commit: os deploys entregam a chave SSH do servidor à action, e `@main`/`@master`
  rodaria qualquer commit novo dela.

## Mudanças

Em cada step de SSH:

- `uses: appleboy/ssh-action@0ff4204d59e8e51228ff73bce53f80d53301dee2  # v1.2.5` (composite: baixa o `drone-ssh` e
  confere o checksum; não depende do Node do runner);
- `user:` → `username:` e `command:` → `script:` (conteúdo inalterado; secrets `HOST`/`USER`/`KEY` iguais);
- `command_timeout: 5m` nos deploys que só disparam em segundo plano (o padrão da action é 10m);
  `40m` no `viagem_app`, cujas opções manuais esperam os scripts (`timeout-minutes: 40`).

O `update_base_image.yml` já usava a appleboy, em `@master`: passa a usar o mesmo SHA. O `checkservice.yml` segue
desativado, migrado para quando voltar.

## Decisões e riscos

- A forma de executar o script no servidor não é idêntica entre as actions: migração começa pelo `danibproject`,
  validado antes dos outros.
- Commit em `.github/` não está no `paths-ignore`: cada push é um deploy real, feito um repo por vez, conferindo o run.
- Atualizar a action passa a ser trocar o SHA à mão (a versão fica no comentário).

## Validação

Run verde, sem o aviso de Node 20, em cada repo; `viagem_app` também numa execução manual de simulação. O
*Update Base Image* só é validado quando for disparado de novo.

## Checklist de entrega

- [x] Workflows migrados
- [x] `CLAUDE.md` do ecossistema atualizado (e `danibproject`/`viagem_app` incluídos no mapa)
- [x] Plano arquivado em cada repo
- [x] Commit e push um repo por vez
