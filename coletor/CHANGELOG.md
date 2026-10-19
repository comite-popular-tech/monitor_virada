# Mudanças

## 1.2.0 (19/10/2026)

**Todos os estados**
- O job `cidades` passa a coletar o mapa por cidade nos **27 estados**. Cidades fora da segmentação entram com `cidade_alvo = false` e segmento vazio.

**Termos de ataque**
- 3 macrotemas novos e 20 termos: `ATQ_LULA` (8), `ATQ_FLAVIO_ORG` (6), `ATQ_FLAVIO_PUSH` (6), em 6 grupos (`ATQ_LULA_1/2`, `ATQ_FLAVIO_ORG_1/2`, `ATQ_FLAVIO_PUSH_1/2`), todos com a âncora "bolsa família".
- Os 6 grupos entram nos jobs `estados` e `cidades`.
- Novo campo `macrotemas_relacionadas` em `config/termos.yaml`: as buscas relacionadas de temas continuam só com Saúde, Educação e Aposentadoria e renda (14 termos).

**Plano e orçamento**
- 311 buscas/dia (325 em 19 e 22/10), **1.894 de 19/10 a 24/10**. Exige plano pago.
- `limite_por_hora` sobe para 1000; o limite real continua sendo o da conta.
- Workflow passa a rodar de hora em hora (9h47 a 17h47 UTC). Execuções seguintes só pegam o que faltou; se o dia já estiver completo, não gastam buscas.

## 1.1.0 (17/10/2026)

**Segmentação completa no coletor**
- Novo arquivo `config/cidades_segmentacao.csv` com as 1.794 cidades da segmentação (RM SP, interior PR, interior SC, GO, MG).
- O job `cidades_sp` foi substituído pelo job `cidades`, que coleta o mapa por cidade em **SP, MG, PR, SC e GO**, com os **5 grupos** de termos, todo dia (25 buscas/dia).
- Cada linha de cidade em `geo_map.csv` agora traz `uf`, `cod_tse`, `recorte`, `segmento`, `porte` e `rank_no_segmento_recorte` quando a cidade está na segmentação.
- `cidade_alvo = true` para cidades da segmentação e para as 5 cidades do interior de SP já monitoradas.

**Formato**
- `eh_ancora` e `cidade_alvo` passaram de `sim`/`não` para `true`/`false`, compatíveis com BOOLEAN no BigQuery.
- Um `geo_map.csv` já existente é migrado sozinho na primeira coleta: ganha as colunas novas (vazias nas linhas antigas) e tem `sim`/`não` convertidos.

**Plano e orçamento**
- O limite da cota gratuita não restringe mais o plano: 33 buscas/dia (47 em 19 e 22/10), **292 de 17/10 a 24/10**.
- A trava `reserva_minima` (30) continua ativa; `0` desliga.
- Novos campos de agendamento: `geos` (vários estados num job) e `deslocamento` (escalonar jobs entre dias).
- `python -m coletor plano` agora mostra o total previsto **da data consultada até o fim**.
- IDs de busca de jobs com vários estados incluem o estado (ex.: `cidades:BR-MG:G1`).

**BigQuery**
- Adicionar ao esquema de `trends_geo_map`: `uf STRING, cod_tse STRING, recorte STRING, segmento STRING, porte STRING, rank_no_segmento_recorte INT64`.
- Com carga `--replace`, basta recriar a tabela com o esquema novo; com append, usar `--schema_update_option=ALLOW_FIELD_ADDITION`.

## 1.0.0 (16/10/2026)
- Versão inicial.
