# Comandos do Bot

## /rank

Exibe o ranking do mês atual para uma modalidade esportiva.

Ao executar, o bot mostra um menu inline com as modalidades que tiveram atividades no mês. Após selecionar, exibe o ranking ordenado por:
- **Distância** (km) para a maioria das modalidades
- **Tempo** (HH:MM:SS) para modalidades sem distância relevante (yoga, musculação, etc.)

**Exemplo de resposta:**
```
Ranking de Run - Abril/2026

1º - João Silva 🥇1 - 85.3km
2º - Maria Souza - 72.1km
3º - Pedro Costa 🥉1 - 68.5km
```

---

## /yrank

Mesmo comportamento do `/rank`, mas considera o ano inteiro (1º de janeiro até hoje). O título leva o ano, por exemplo "Ranking de Run - 2026".

Os esportes sem distância (futebol, tênis, crossfit, musculação, yoga etc.) são ranqueados por tempo em movimento. A lista fica em `assistant_util.strava.SPORTS_RANKED_BY_TIME` e é a mesma usada no fechamento das medalhas.

---

## /frequency

Ranking de frequência do mês atual: quantos dias únicos cada membro treinou.

**Exemplo de resposta:**
```
Frequência - Abril 2026

1º - Maria Souza - 18/30 dias
2º - João Silva - 15/30 dias
3º - Pedro Costa - 12/30 dias
```

---

## /yfrequency

Frequência do ano inteiro: dias únicos treinados / total de dias no ano.

---

## /streak

Sequência de dias consecutivos com atividade, contando de hoje para trás.

Só exibe membros que treinaram hoje (no horário de Brasília). Calcula quantos dias consecutivos (sem pular nenhum) cada um tem, olhando até 365 dias para trás.

**Exemplo de resposta:**
```
Streak - 16/04/2026

1º - João Silva - 7 dias
2º - Maria Souza - 3 dias
```

---

## /medalhas

Placar acumulado de medalhas de todos os rankings mensais já registrados.

**Sistema de pontos:**
- 🥇 1º lugar = 3 pontos
- 🥈 2º lugar = 2 pontos
- 🥉 3º lugar = 1 ponto

**Exemplo de resposta:**
```
Medalhas

1º - João Silva 🥇3🥈1 - 11pts
2º - Maria Souza 🥇1🥈2🥉1 - 8pts
3º - Pedro Costa 🥉3 - 3pts
```

---

## /link

Gera um link OAuth do Strava para que um novo membro autorize o bot a ler suas atividades.

O link direciona para a página de autorização do Strava com o `group_id` embutido no redirect URI.

---

## /admin

**Só administradores do grupo** (ou o próprio usuário, em chat privado).

Exibe um menu inline para remover um membro do grupo.

Ao selecionar um membro:
- Remove do `StravaGroup.membros`
- Remove suas medalhas de `StravaGroup.medalhas`
- Deleta todas suas atividades da coleção `strava_activity`

---

## /reset

**Só administradores do grupo.**

Re-sincroniza com o Strava as atividades do mês inteiro, ignorando o intervalo mínimo entre syncs. Se algum membro falhar (por exemplo, token revogado), a resposta diz quem.

---

## Notas gerais

- Todos os rankings sincronizam atividades do Strava antes de calcular, com intervalo mínimo de 1 minuto entre sincronizações do mesmo grupo.
- As respostas usam HTML para formatação (links clicáveis para perfis do Strava), e os nomes são escapados.
- O bot opera em modo polling (`infinity_polling`, não webhook).
- Uma exceção num comando é registrada via `tratar_error` (origem `strava_bot`). O chat recebe "Não consegui processar o comando agora", e o bot continua de pé.
- Em grupo não cadastrado, os comandos respondem "Grupo não cadastrado. Use /link para conectar o Strava."
- `/rank@nome_do_bot` funciona: o sufixo é removido por `extract_command`.
