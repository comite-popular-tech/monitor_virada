# SQL das views do BigQuery

As views que alimentam o painel (`vw_cidade_acao`, `vw_territorio`, `vw_em_alta` etc.)
vivem só no BigQuery (`comite-tecnologia.analise_redes`), não são geridas por nenhum
código deste repositório — o painel web só faz `SELECT` nelas (`web/app/queries.py`).

Esta pasta guarda cópias do SQL de views que foram alteradas manualmente no console
do BigQuery, como registro histórico e ponto de restauração caso alguém sobrescreva
uma view sem querer. Não é aplicado automaticamente em lugar nenhum — pra rodar, copia
e cola no BigQuery Studio (ou `bq query`) manualmente.

## `vw_territorio.sql` e `vw_lula_flavio_cidade.sql`

Corrigidas em 22/10 pela Renata (SQL preparado nesta sessão). Contexto: o painel
mostrava só 589 "cidades monitoradas" (KPI do topo da Página 2), mas a tabela bruta
`gtrends_monitoramento_cidades` já tinha 1.912 municípios distintos coletados — o
gargalo era o campo `cod_tse`, que só vinha preenchido pra 634 deles.

Investigação: das 1.312 cidades sem `cod_tse`, a maioria (recorte/segmento já
preenchidos, ou seja, já fazem parte da lista priorizada) tinha nome normal, incluindo
capitais de estado (Manaus, Maceió, Rio Branco) — não era um recorte deliberado, era
falha de correspondência de texto (acento, apóstrofo, maiúscula) contra
`tse_municipios_2026`. Normalizando `uf + nome do município` (NFD, minúsculo, sem
marca diacrítica, sem pontuação) recuperou 1.211 das 1.312 (92%), sem colisão de
chave verificada contra `tse_municipios_2026`.

Resultado: cobertura de municípios no painel foi de 589 para ~1.669 (a diferença pro
teto teórico de ~1.845 é o filtro `macrotema != 'Candidatos'` de `vw_territorio`, que
já existia antes e não foi alterado).

**Isso não amplia a coleta do Google Trends** — só recupera municípios que o
coletor (`trends_monitor`, fora deste repo) já buscava mas que ficavam de fora por
causa do `cod_tse` não casado. Pra cobrir os ~5.570 municípios do Brasil de verdade,
seria preciso ampliar o que o coletor busca, não essas views.
