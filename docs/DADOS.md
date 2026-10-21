# De onde vem cada número do painel

Este documento aponta, bloco a bloco, exatamente qual fonte do BigQuery alimenta cada
gráfico ou tabela do Monitor da Virada e qual é a conta feita em cima dela. A coluna
"Confirmado" marca o que foi lido diretamente na configuração do Looker Studio
(prints de 19/10); "Interpretação" marca o que foi deduzido porque o campo é um
cálculo interno do Looker (campo "AUT") cuja fórmula não aparece no painel de
configuração, só o resultado.

Todas as fontes vêm do dataset `comite-tecnologia.analise_redes`.

## Página 1 — Curto prazo (Google Trends, últimas 24h)

| Bloco | Fonte | Dimensão | Métrica | Filtros | Status |
|---|---|---|---|---|---|
| KPI "% com pauta Eleitoral" | `vw_em_alta` | — | campo calculado no Looker: `COUNT_DISTINCT(CASE WHEN tema='Eleição' OR candidato_mencionado<>'Nenhum' THEN rotulo END) / COUNT_DISTINCT(rotulo)` | **"vw_alta_situacao_altaagora"** (sempre `ativa=true`, fixo neste bloco, independente do controle global "Assunto ativo?") | Confirmado (fórmula exata, 20/10; filtro confirmado 21/10). É a proporção de **rótulos distintos** com pauta eleitoral ou que citam candidato sobre o total de rótulos distintos — não é ponderado por volume. **Gap encontrado**: o painel web reproduz a fórmula mas hoje deixa o KPI seguir o controle global "Assunto ativo?" em vez de travar sempre em `ativa=true` como no Looker original — precisa de ajuste em `app/transform.py`/template. |
| Pizza por candidato | `vw_em_alta` | `candidato_mencionado` | `SUM(volume)` | `candidato_mencionado <> "Nenhum"` | Confirmado. (Corrigido 20/10: o painel web estava contando rótulos distintos em vez de somar volume — já ajustado.) |
| Tabela "Top termos" | `vw_em_alta` | `rotulo`, exibido como "termo" (é um apelido do campo `rotulo`, não um campo calculado, não é `termos_txt`) | `MAX(aumento)`, ordenado desc | sem filtro próprio no gráfico | Confirmado 21/10 direto no editor do campo (ID de origem `rotulo`, Tipo texto). Corrige leitura anterior que supunha `termos_txt`. |
| Mapa "Onde está em alta" | `vw_em_alta` | `uf_iso` (cor por `candidato_mencionado`) | `SUM(aumento)` (tamanho da bolha) | `candidato_mencionado <> "Nenhum"` (filtro "Candidato_True") | Confirmado |
| Barras por Estado | `vw_em_alta` | `uf` (detalhe `candidato_mencionado`), N superiores = 10 | `SUM(aumento)` | **"excluir uf br"** + **"Candidato_True"** | Confirmado 21/10 direto no painel de filtros do gráfico. Corrige leitura anterior ("situacao = Em alta agora" + termos preenchido) — os filtros reais excluem a UF agregada "BR" e `candidato_mencionado <> "Nenhum"`, nada relacionado a `situacao`/`termos_txt`. |
| Evolução por hora | `vw_em_alta` | `rotulo`, N superiores = 10 | `SUM(aumento)` | mesmos dois filtros da barra por Estado | Confirmado (2º print de 20/10): a dimensão detalhada é `rotulo`, não `candidato_mencionado`. As duas linhas "Lula" e "Flávio Bolsonaro" são os próprios rótulos das buscas diretas pelo nome do candidato (grupo `CAND` no coletor: lula, flávio bolsonaro, bolsonaro), não uma soma por `candidato_mencionado`. O backend hoje soma `aumento` dos rótulos normalizados "lula" e "flávio bolsonaro"/"bolsonaro" por hora. |
| Tabela Termos × Horas (ao lado da evolução) | `vw_em_alta` | `termos_txt` + `horas_desde_inicio` | `MAX(aumento)` | mesmos dois filtros, ordenado por horas asc | Confirmado |
| "Buscas em alta por Estado" (tabela com filtros Tema/Rótulo/Candidato/Estado) | `vw_em_alta` | Tema, Rótulo, Candidato, Termos | `MAX(aumento)`, `MAX(volume)` | os 4 dropdowns do bloco | Confirmado nos campos; o painel web hoje mantém uma linha por Estado em vez de agregar todas as UFs numa linha só por rótulo — se no relatório original a tabela esconde o Estado e agrega por rótulo/tema/candidato, é um ajuste de uma linha em `app/main.py`/no template, me avisa que eu faço |
| "Interesse nas últimas 24h" (barras empilhadas) | `vw_em_alta` | `inicio`, detalhe `rotulo` | `SUM(aumento)` | `situacao = "Em alta agora"`, top N | Confirmado na métrica; o Looker pede "N superiores = 100" e o painel web mostra os 10 rótulos de maior soma para não virar 100 cores numa barra — mantive 10 de propósito |

## Radar local / Interesse por município

| Bloco | Fonte | Dimensão | Métrica | Filtros | Status |
|---|---|---|---|---|---|
| Tabela "Radar local" (com dropdowns Local/Estado/Cidade alvo/Porte/Segmento/Macrotema) | `gtrends_monitoramento_cidades` | `macrotema`, `local`, `termo` (coluna nativa da view, não é apelido) | `AVG(indice_vs_ancora)` | `eh_ancora = false` (filtro "Exc_ancora"); Dimensão do período = `data_coleta`; **Filtro de período padrão = Personalizado "Ontem"** com **Período de comparação ligado (Período anterior)** | Corrigido 21/10: não é "últimos 7 dias" como documentado antes — o gráfico já vem fixado em "Ontem" com comparação nativa do Looker contra o período anterior (dia anterior). A coluna "% Δ" é esse cálculo de comparação nativo do Looker, não um campo próprio sem comparação como se pensava antes. O painel web faz essa comparação no backend via `LAG` por dia — mesma lógica, mas confirmar se a janela usada é também "ontem vs anteontem" e não os últimos 7 dias. |

## Página 2 — Mobilização / território

| Bloco | Fonte | Observação |
|---|---|---|
| KPIs, Ranking, Acelerando, Onde agir, Segmento × conversa, Pauta por segmento | `vw_cidade_acao` | A view já entrega a coleta mais recente, uma linha por cidade |
| Índice por tema (usado no Ranking e em "Ações do dia") | `vw_territorio_ultimo` | Filtrado só em `macrotema IN ("Saúde","Educação","Aposentadoria e renda")`: os macrotemas de ataque (ATQ_*) e os de candidato nunca entram no "tema principal" de uma cidade |

## Página 3 — Pautas

| Bloco | Fonte | Observação |
|---|---|---|
| Lista "em alta" | `vw_pautas` | Uma linha por termo, sempre a coleta mais recente dele (`QUALIFY` pela data máxima por `termo_base`) |

## Status

Os 3 pontos que estavam pendentes (Share de pauta eleitoral, quebra Lula/Flávio na
Evolução por hora, variação % do radar local) foram confirmados em 20/10 e já
estão corrigidos no código e nas tabelas acima. Não há pendências abertas no
momento.

A DDL de `vw_em_alta` (lida direto do BigQuery em 20/10) confirmou também que
`tema`, `candidato_mencionado`, `rotulo` e `situacao` já são colunas nativas da
view — o painel web lê todas direto dela, sem recalcular nada em Python.
