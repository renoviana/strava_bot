# Deploy sem segurar o runner do GitHub

**Aprovado em 2026-11-13.**

## Projetos afetados

`assistant_bot` (scripts `em_segundo_plano.sh` e `avisar_deploy.py`, `deploy.yml` e `update_base_image.yml`) e o
`deploy.yml` de `assistant_api`, `assistant_schedule`, `assistant_promotion`, `carros_app`, `metro_bot`, `soro_bot`,
`posto_bot`, `strava_bot`, `weednotifier`, `site_podas` e `viagem_app`. `pedal_app` e `graffiti-maps` (fora desta
pasta) ficam para depois.

## Objetivo

Em 1-13/11/2026 o Actions gastou ~2.200 minutos (747 no *Update Base Image*, 353 no deploy do schedule, ~400 no
viagem_app) e a conta `renoviana` bateu no limite: os workflows seguravam a sessão SSH aberta enquanto o Pi
construía, e cada minuto de espera é cobrado. Os alertas horários (`checkservice.yml`, `mongo-collection-check.yml`)
já estavam desativados desde 2026-10-03. Meta: cortar ~80% dos minutos sem perder aviso de falha.

## Mudanças

| Onde | Mudança |
|---|---|
| `assistant_bot/scripts/em_segundo_plano.sh` | Recebe um nome e os comandos por stdin (heredoc), dispara com `setsid nohup` e devolve na hora. Log em `~/deploy_logs/<nome>-<data>.log` (apaga os de mais de 14 dias). Falha: aviso no tópico de erros (`ERROR_ID`) com a duração e as últimas 15 linhas do log. `AVISAR_SUCESSO=1`: avisa o sucesso no tópico de notificações (`AVISAR_TITULO_SUCESSO` dá o texto) |
| `assistant_bot/scripts/avisar_deploy.py` | Conecta no `assistant-db` (`MONGO_URI`) e chama `assistant_send` (fila; o sender entrega). Escapa o trecho do log num `<pre>` (o sender usa HTML). Roda num container descartável da base com o `.env`, sem depender de serviço no ar |
| `deploy.yml` dos 12 repos | O bloco de comandos de antes vira o heredoc do `em_segundo_plano.sh`, sem outra mudança; `timeout-minutes: 10`; `paths-ignore` com `**/*.md`, `docs/**` e `tests/**` (nada disso entra na imagem desde o `.dockerignore`) |
| `viagem_app/.github/workflows/deploy.yml` | Com alguma opção manual (catálogo, cidades, simular/aplicar), roda na frente como antes, para a saída aparecer no log do Actions; push e deploy sem opção vão para o segundo plano. Timeout fica em 40 min |
| `assistant_bot/.github/workflows/update_base_image.yml` | O script inteiro no heredoc. Saem os dois passos que chamavam a API do Telegram direto (fora da fila): a falha vem pelo servidor no tópico de erros, e o sucesso do reset (`redeploy=true`) no de notificações, com o mesmo texto de antes. `timeout-minutes: 10`, `command_timeout: 5m` |

## Fluxo

push → o GitHub conecta por SSH, faz `git pull` do `assistant_bot` e dispara o deploy em segundo plano (segundos de
runner) → o Pi roda o `deploy_compose.sh` como antes, um por vez pela trava → falha vira aviso no tópico de erros.

## Decisões e riscos

- Verde no GitHub passa a querer dizer "disparado". O resultado vem pelo Telegram (só falhas; o reset também avisa o
  sucesso) e o log fica no servidor.
- `/reset`, `/resetar` e o health check continuam disparando o mesmo workflow; `reset_service` não muda.
- Pushes seguidos esperam na trava do `deploy_compose.sh` (até 30 min); passou disso, falha e avisa.
- Se o próprio aviso falhar (Mongo fora do ar), sobra o log no servidor.
- O `site_podas` ainda faz `docker-compose down` + `up --build` sem o `deploy_compose.sh` (derruba o site a cada
  deploy e pula a checagem de disco): fica como está, envolvido no segundo plano, e o ajuste vai para plano próprio.

## Testes

- `assistant_bot/tests/test_em_segundo_plano.py`: devolve na hora, roda na pasta de quem chamou, grava o log, avisa
  na falha com o fim do log, fica quieto no sucesso, avisa o sucesso quando pedido, apaga logs antigos (precisa de
  `setsid`: roda no Linux; passou num container descartável no servidor); `avisar_deploy.py` com a fila mockada;
  estrutura dos dois workflows do bot.
- Nos repos com suíte: o `deploy.yml` usa o `em_segundo_plano.sh` e tem o `paths-ignore`; no viagem_app, também o
  caminho na frente das opções manuais.
- Verificação real pelo SSH (o Actions estava bloqueado): o comando novo do `metro_bot`, extraído do `deploy.yml`.

## Checklist

- [x] Scripts e testes
- [x] `deploy.yml` dos 12 repos e `update_base_image.yml`
- [x] Docs e planos
- [x] Suítes completas, commits e push
- [ ] Verificação real pelo SSH (depois do push)
- [ ] Primeiro deploy pelo GitHub quando o limite do Actions liberar
