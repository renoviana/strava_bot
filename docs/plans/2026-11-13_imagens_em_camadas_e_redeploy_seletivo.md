# Imagens em camadas por frequência de mudança e redeploy só de quem usa

## Contexto

Em 2026-11-13 o Raspberry Pi 4 (3,7 GB de RAM, SD de 29 GB) reiniciou pelo watchdog durante o redeploy do *Update
Base Image*: o `docker-compose build` do schedule construiu schedule, aves e correio **em paralelo**, refazendo apt,
Chromium e moviepy, com os 46 containers rodando. O usuário quer refazer deploys o mínimo possível, com actions mais
rápidas, dentro dos limites do Pi.

Medido em 30 dias:

| O que muda | Quantas vezes |
|---|---|
| Commits nas nossas libs (scrap 39, model 32, util 14) | 85 |
| *Update Base Image* | 59 (média 16 min, 4 falhas) |
| Commits em `requirements.txt` (terceiros) | 3 |
| Mudança nas dependências declaradas pelas libs (`pyproject.toml`) | 0 |

Hoje a base é uma camada só: cada commit de lib reinstala ~400 MB de pacotes de terceiros que quase nunca mudam, e
toda imagem filha muda junto: as 46 containers reiniciam e o correio/aves refazem apt/Chromium/moviepy (~1 GB).

Outros achados:
- 9 de 10 repos não têm `.dockerignore`: o `.git` vai para a imagem a cada deploy (no schedule, 151 MB × 3 imagens
  por commit; o código tem ~7 MB).
- Nem todo serviço usa toda lib (busca de imports, sem `tests/`):

| Repo | util | model | scrap | telebot_tools | carros_mcp |
|---|---|---|---|---|---|
| api | x | x | x | | |
| bot | x | x | x | x | |
| schedule | x | x | x | | x |
| carros_app | x | x | x | | x |
| metro_bot | x | | x | x | |
| promotion | x | x | | x | |
| soro_bot | x | x | | x | |
| posto_bot | | x | | x | |
| strava_bot | x | x | | | |
| weednotifier | | | | | |

O scrap, que mais muda, não é usado por promotion, soro, posto, strava nem weednotifier.

## Abordagem aprovada (2026-11-13)

### 1. Base em duas camadas (por frequência de mudança)

```
assistant-imagem-python   (ImageBase: sistema)            muda ~nunca
  └─ assistant-base-deps  (pacotes de terceiros, ~400 MB)  muda com requirements (3×/mês)
       └─ assistant-base-python (libs em /opt/libs, ~30 MB) muda a cada commit de lib
```

- `ImageLib` vira dois estágios/tags:
  - **deps**: `pip install` do requirements consolidado (com as libs, para trazer as dependências delas) e depois
    `pip uninstall` das 5 libs; fica só terceiros. Chave de reconstrução: `REQS_VERSION` (md5 do consolidado) +
    `forcar`. Label `reqs_version`.
  - **libs**: `FROM assistant-base-deps`, `pip install --no-deps --target /opt/libs` das 5 libs git
    (`CACHEBUST` = hash das libs, como hoje), `ENV PYTHONPATH=/opt/libs`. Labels `libs_version` e o novo
    `libs_commits` (commit de cada lib).
  - **Checagem de dependência**: depois da camada de libs, um script confere se os `Requires-Dist` de cada lib em
    `/opt/libs` estão no `site-packages`. Se faltar algo (lib ganhou dependência nova), o workflow refaz a camada
    deps sozinho e tenta de novo; persistindo, falha com mensagem clara.
- O nome `assistant-base-python` não muda: todos os `FROM assistant-base-python` (serviços, carros_app, pedal_app,
  viagem_app) seguem iguais.
- Efeito: commit de lib refaz só ~30 MB (estimado em 1-2 min, contra 16 min). Base antiga presa em serviço não
  refeito custa ~30 MB, não ~400 MB.

### 2. Imagens específicas partem da camada estável

- `assistant_schedule/correio_schedule/Dockerfile`: `FROM assistant-base-deps` → camada pesada (apt `libatomic1`
  `xvfb`, Playwright, Chromium; como hoje, com cache mounts) → `COPY --from=assistant-base-python /opt/libs /opt/libs`
  → `ENV PYTHONPATH=/opt/libs` → `COPY . .`.
- `assistant_schedule/aves_schedule/Dockerfile`: mesmo desenho, com `pip install moviepy` na camada pesada (o Pillow
  11.3 que o moviepy exige continua valendo, como hoje).
- Efeito: commit de lib → só a cópia de ~30 MB. Apt/Chromium/moviepy só refazem quando os requirements mudam
  (raro), e sem duplicar disco (compartilham a `base-deps`).

### 3. Redeploy só dos repos afetados

- Novo `assistant_bot/scripts/repos_afetados.sh <libs>`: para cada repo de serviço, procura imports das libs que
  mudaram (mesma busca da tabela acima, sem `tests/`), e devolve a lista. Sem mapa fixo para manter.
- `update_base_image.yml`: compara os `libs_commits` da base antiga com a nova e descobre quais libs mudaram.
  - Novo input `redeploy_afetados` (padrão `true`): sobe de novo só os repos que usam as libs que mudaram.
  - `redeploy` (todos) fica igual: é o que o `/reset`, o `/fullreset`, o `/resetar` e o health check disparam via
    `assistant_util.service.reset_service`, que não muda.
  - Se a camada deps mudou, todos os repos são afetados.
- Exemplo: commit só no scrap → redeploy de api, bot, schedule, carros_app e metro_bot; promotion, soro, posto,
  strava e weednotifier (12 containers) não são tocados.

### 4. Build sequencial e contexto enxuto

- `assistant_bot/scripts/deploy_compose.sh`: build com `COMPOSE_PARALLEL_LIMIT=1` (uma imagem por vez). Protege a
  nova `assistant-base-deps` na limpeza profunda (lista de protegidas).
- `.dockerignore` (`.git`, `tests`, `docs`, `__pycache__`, `.pytest_cache`, `*.md`, `node_modules` onde couber) em
  api, bot, schedule, promotion, carros_app, metro_bot, soro_bot, posto_bot e strava_bot.

## Projetos e arquivos

- `assistant_bot`: `ImageLib`, `.github/workflows/update_base_image.yml`, `scripts/deploy_compose.sh`,
  `scripts/hash_libs.sh` (saída por lib), novos `scripts/repos_afetados.sh` e `scripts/checar_deps_libs.py`,
  `.dockerignore`, testes, `CLAUDE.md`, plano.
- `assistant_schedule`: `correio_schedule/Dockerfile`, `aves_schedule/Dockerfile`, `.dockerignore`,
  `tests/test_compose_recursos.py`, `CLAUDE.md`, `docs/architecture.md`, plano.
- `assistant_api`, `assistant_promotion`, `carros_app`, `metro_bot`, `soro_bot`, `posto_bot`, `strava_bot`:
  `.dockerignore` e o plano.
- `CLAUDE.md` da raiz (não versionado): seções "Imagens" e "Fluxo de deploy".
- Consumidores: `assistant_util.service.reset_service` não muda (usa `redeploy=true`). `pedal_app`, `viagem_app`
  (FROM base) e `graffiti-maps` não mudam.

## Decisões e riscos

- **Não mover código do scrap** (correio, wikiaves): as imagens continuariam dependendo de util/model da base, e a
  regra 7 ganharia exceção. O acoplamento estava nas camadas, não no código.
- **Não criar uma base por grupo de serviços** (ex.: base sem scrap para promotion): com as libs numa camada de
  ~30 MB, o ganho vem do redeploy seletivo, sem manter várias bases.
- **`PYTHONPATH=/opt/libs`**: se algum serviço definir `PYTHONPATH` no compose ou no Dockerfile, ele precisa
  incluir `/opt/libs`; a implementação busca e ajusta. Teste de import em cada container depois do deploy.
- **Dependência nova numa lib** sem mudar requirements: coberta pela checagem com refação automática da camada deps.
- **Serviços não afetados ficam com a base anterior**: correto, porque não usam a lib que mudou; custo de disco
  ~30 MB por versão presa.
- Primeira execução: refaz deps + libs + todas as imagens (uma vez), em sequência; acompanhar memória.
- Os 3 achados anteriores (Redis sem senha, tentativas de senha de root no SSH, pedal/viagem/graffiti sem limite de
  memória) seguem como planos próprios.

## Verificação

1. Suítes completas e flake8 de bot e schedule; testes do `deploy_compose.sh` e do `repos_afetados.sh` num
   container Linux descartável (usam `flock`/bash), como feito hoje.
2. Testes novos: estrutura do `ImageLib` (dois estágios, `--target /opt/libs`, `PYTHONPATH`), workflow (comparação
   de `libs_commits`, input `redeploy_afetados`), Dockerfiles do correio/aves (`FROM assistant-base-deps`, cópia de
   `/opt/libs` depois da camada pesada), `.dockerignore` presente nos repos com suíte.
3. No servidor, primeira execução do *Update Base Image* com `redeploy=true`, acompanhando `free`/load; depois em
   cada container: `python -c "import assistant_util, assistant_model, assistant_scrap"`, `Xvfb` e `playwright` no
   correio, `moviepy` + Pillow 11.3 no aves.
4. Prova do ganho: um commit trivial só no scrap → *Update Base Image* (`redeploy_afetados`) deve levar poucos
   minutos, refazer só a camada de libs e subir só api, bot, schedule, carros_app e metro_bot; correio/aves sem apt.
5. Disco antes/depois (`df`, `docker system df`).

## Checklist

- [ ] ImageLib em duas camadas + checagem de dependências
- [ ] update_base_image: deps por `REQS_VERSION`, libs por hash, `libs_commits`, `redeploy_afetados`
- [ ] repos_afetados.sh e hash por lib
- [ ] deploy_compose.sh sequencial e `assistant-base-deps` protegida
- [ ] Dockerfiles do correio e do aves sobre a `base-deps`
- [ ] `.dockerignore` nos 9 repos
- [ ] Testes, docs (CLAUDE.md de bot/schedule/raiz, architecture) e planos em cada repo
- [ ] Commits por repo, push (bot primeiro), Update Base Image com `redeploy=true`, verificação e prova do ganho

## Decisões tomadas na implementação

- As duas camadas são dois arquivos no `assistant_bot`, e não dois estágios do mesmo arquivo: `ImageDeps`
  (`assistant-base-deps`) e `ImageLib` (`assistant-base-python`, `FROM assistant-base-deps:latest`). Assim o
  workflow pula a camada de terceiros quando o `reqs_version` não mudou, sem nem chamar o build dela.
- A base nova é construída como `assistant-base-python:nova` e só vira a `latest` depois da checagem de
  dependências. Build ou checagem que falha deixa a base anterior em uso.
- `forcar` refaz as duas camadas (`CACHEBUST_DEPS` e `CACHEBUST` com a hora).
- Imagem raiz refeita (`ImageBase` mudou) obriga a refazer a camada de terceiros, que parte dela.
- O marcador "todas as libs" do `repos_afetados.sh` é a palavra `todas`, não `*`: no Windows o bash do Git expande
  o `*` dos argumentos e o teste ia falhar.
- O `.dockerignore` não exclui `*.md` (o plano previa): nenhum ganho real e risco de algum serviço ler um `.md`.
  Exclui `.git/`, `.github/`, `tests/`, `docs/`, caches, `.venv`/`venv`, `node_modules`, `.env*` e `*.log`.
- O `assistant_promotion` definia `PYTHONPATH=/app` (Dockerfile e compose), o que esconderia `/opt/libs`: passou a
  `/app:/opt/libs`, com teste.
- Medido no servidor com tags de teste, antes do deploy: camada de terceiros 375 s (uma vez), camada das libs 150 s
  e 26 MB em `/opt/libs`; checagem de dependências ok; imports de util, model, scrap, telebot_tools e carros_mcp a
  partir de `/opt/libs`; `COPY --from` de imagem local gera camada de 24,6 MB.
