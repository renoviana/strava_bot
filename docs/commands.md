# Comandos do Bot

## /rank

Exibe o ranking do mês atual para uma modalidade esportiva.

Ao executar, o bot mostra um menu inline com as modalidades que tiveram atividades no mês. Após selecionar, exibe o ranking ordenado por:
- **Distância** (km) para a maioria das modalidades
- **Tempo** (HH:MM:SS) para modalidades sem distância relevante (yoga, musculação, etc.)

**Exemplo de resposta:**
```
Ranking Run - Abril 2026

1º - João Silva 🥇1 - 85.3km
2º - Maria Souza - 72.1km
3º - Pedro Costa 🥉1 - 68.5km
```

---

## /yrank

Mesmo comportamento do `/rank`, mas considera o ano inteiro (1º de janeiro até hoje).

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

Só exibe membros que treinaram hoje. Calcula quantos dias consecutivos (sem pular nenhum) cada um tem.

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

Exibe um menu inline para remover um membro do grupo.

Ao selecionar um membro:
- Remove do `StravaGroup.membros`
- Remove suas medalhas de `StravaGroup.medalhas`
- Deleta todas suas atividades da coleção `strava_activity`

---

## /reset

Redefine o campo `last_activity_date` de todos os membros para o dia 1º do mês atual ao meio-dia.

Útil quando o bot precisa re-sincronizar as atividades do mês desde o início.

---

## Notas gerais

- Todos os rankings sincronizam atividades do Strava antes de calcular (com proteção de rate-limit de 1 minuto entre sincronizações).
- As respostas usam HTML para formatação (links clicáveis para perfis do Strava).
- O bot opera em modo polling (não webhook).
