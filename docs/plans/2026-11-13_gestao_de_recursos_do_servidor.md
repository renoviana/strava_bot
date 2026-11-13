# Gestão de recursos do servidor (Raspberry Pi 4)

**Aprovado em 2026-11-13.**

## Projetos afetados

Servidor (host), `assistant_bot`, `assistant_schedule` e os composes de `assistant_api`, `assistant_promotion`,
`carros_app`, `metro_bot`, `soro_bot`, `posto_bot`, `strava_bot`, `weednotifier` e `site_podas`.

## Objetivo

O Pi 4 tem 3,7 GB de RAM e um SD de 29 GB. Em 2026-11-13 estava com 3,9 GB livres (o `deploy_compose.sh` exige 5)
e o swap (zram de 2 GB) cheio: o deploy do bot e do schedule falharam. Ganhar folga de disco e memória e avisar antes
de travar.

## Diagnóstico (2026-11-13)

- Disco: `/var/lib/docker` 13 GB (imagens 8,8 GB, cache de build até 1,6 GB, volumes 0,9 GB), `/usr` 5,5 GB com resto
  do desktop, `/var/swap` 2 GB (disco de apoio do zram, fica), Plex parado (692 MB) e dados do atelie sem container.
- Os "~3 GB sem dono" no `overlay2` eram snapshots do BuildKit (cache de build), não camadas órfãs.
- Todo *Update Base Image* sem redeploy deixa, em cada serviço não refeito, uma cópia da camada de libs antiga
  (`pedal_app` e `viagem_app` tinham ~620 MB exclusivos cada por isso).
- Memória: 46 containers, a maioria com pico abaixo de 100 MB; picos maiores no `correio_schedule` (838 MB, Chromium),
  WordPress (621 MB) e `mongo_carros` (302 MB). Só 9 serviços tinham limite. `wordpress_db`, `mongo_carros` e
  `wordpress` declaravam limite desde março, mas os containers (de outubro) foram criados sem ele, e o compose não os
  recria porque o hash da configuração não muda.

## Mudanças

| Onde | Mudança |
|---|---|
| Servidor | Removidos firefox, chromium, lightdm, kubectl, docker-model-plugin e 93 dependências do desktop; `apt-get clean`; journal limitado a 100 MB (`/etc/systemd/journald.conf.d/limite.conf`); apagados `/root/plex`, `~/plex` e `atelie_*`; redeploy do `pedal_app` e do `viagem_app` sobre a base atual |
| `assistant_bot/ImageBase` | Sem `xvfb`, `--no-install-recommends`, um único `apt-get` com limpeza das listas |
| `assistant_bot/.github/workflows/update_base_image.yml` | Reconstrói a `assistant-imagem-python` quando o `ImageBase` muda (label `imagebase_hash`), não só quando falta |
| `assistant_bot/scripts/deploy_compose.sh` | Cache de build mantido em até 2 GB (era 10 GB) |
| `assistant_bot/.github/workflows/checkservice.yml` | Alerta horário também com menos de 6 GB livres no disco do Docker |
| `assistant_bot/docker-compose.yml` | Limite no `redis` (320 MB) e `--innodb-buffer-pool-size=64M` no mariadb do WordPress |
| `assistant_schedule/correio_schedule/Dockerfile` | Instala o `xvfb` (saiu da imagem raiz) |
| `assistant_schedule/pessoal_schedule/jobs/saude_diaria.py` | O resumo diário avisa com disco abaixo de 6 GB livres ou swap acima de 90% |
| Composes de todos os repos de serviço | `mem_limit` em todo serviço: 256 MB por padrão; `pessoal_schedule` e `carro_ingestao` 384 MB, `bot_schedule` 512 MB, API 384 MB, nginx 128 MB, `carros_app` 384 MB |

O poppler fica na imagem raiz: o `atacadao_pdf` do `pessoal_schedule` usa o `pdf2image`.

## Fluxo

`checkservice.yml` (de hora em hora) e `saude_diaria_job` (08:00) medem o disco; o deploy continua recusando abaixo
de 5 GB. O limite de memória faz o container que passa dele usar o próprio swap (até 2× o limite) antes de ser morto
e reiniciado (`restart: always`), sem empurrar os outros.

## Decisões e riscos

- Limites com folga de 2× ou mais sobre o pico medido. Risco: um pico raro maior que o medido faz o serviço reiniciar.
  Se acontecer, o `checkservice` e o `/saude` mostram, e o limite daquele serviço sobe.
- O alerta a 6 GB pode tocar de hora em hora enquanto o disco estiver apertado: é a intenção, até o SSD.
- `pedal_app` e `viagem_app` não estão nesta pasta: ficam sem limite de memória por enquanto.
- Para os limites antigos valerem no `wordpress_db`, `mongo_carros` e `wordpress`, o deploy do bot desta mudança roda
  com `--force-recreate` desses três (o compose não os recriaria).
- Solução estrutural recomendada: SSD USB (o usuário vai comprar), com migração do boot.

## Testes

- `assistant_bot/tests/test_recursos_servidor.py` (limites, mariadb, ImageBase, workflows, cache) e os testes do
  `deploy_compose.sh` (rodados num container Linux, pois usam `flock`).
- `assistant_schedule/tests/test_compose_recursos.py` e `tests/pessoal_schedule/test_saude_diaria.py`.
- `tests/test_compose_limites.py` em api, promotion, carros_app, metro_bot, strava_bot e weednotifier.
- `soro_bot`, `posto_bot` e `site_podas` não têm suíte; o limite foi conferido com a leitura do YAML.

## Checklist

- [x] Fase 0 no servidor (pacotes, apt, journal) e deploys do schedule e do bot
- [x] Fase 1: Plex e atelie apagados; overlay2 investigado; cache de build limitado
- [x] Fase 2: ImageBase menor e reconstrução por hash; xvfb no correio; pedal e viagem na base atual
- [x] Fase 3: limites de memória em todos os composes; mariadb menor
- [x] Fase 4: alerta de disco no checkservice e de disco/swap na saúde diária
- [ ] Deploy: base nova, serviços e `--force-recreate` dos três serviços antigos do bot
