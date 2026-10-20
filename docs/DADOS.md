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
| KPI "% com pauta Eleitoral" | `vw_em_alta` | — | campo calculado **"Share de pauta eleitoral"** (já existe na view) | — | Interpretação: o Looker mostra o nome do campo calculado, não a fórmula. O painel web reproduz hoje como proporção do volume de busca em `tema = "Eleição"` sobre o total das últimas 24h. Pode não ser exatamente a fórmula original — se tiver a definição do campo (Recurso → Editor de campos calculados no relatório), me manda que eu ajusto. |
| Pizza por candidato | `vw_em_alta` | `candidato_mencionado` | `SUM(volume)` | — | Confirmado |
| Tabela "Top termos" | `vw_em_alta` | `termos_txt` ("Termos") | `MAX(aumento)`, ordenado desc | — | Confirmado |
| Mapa "Onde está em alta" | `vw_em_alta` | `uf_iso` (cor por `candidato_mencionado`) | `SUM(aumento)` (tamanho da bolha) | `candidato_mencionado <> "Nenhum"` (filtro "Candidato_True") | Confirmado |
| Barras por Estado | `vw_em_alta` | `uf` (detalhe `candidato_mencionado`) | `SUM(aumento)` | `situacao = "Em alta agora"` + `termos_txt` preenchido, top 10 UFs | Confirmado (nome exato das duas condições do filtro composto não está nos prints, mantive a leitura mais direta de "vw_alta_situacao_altaagora" e "Termo_is_not_sull") |
| Evolução por hora | `vw_em_alta` | `rotulo`, N superiores = 10 | `SUM(aumento)` | mesmos dois filtros da barra por Estado | Confirmado (2º print de 20/10): a dimensão detalhada é `rotulo`, não `candidato_mencionado`. As duas linhas "Lula" e "Flávio Bolsonaro" são os próprios rótulos das buscas diretas pelo nome do candidato (grupo `CAND` no coletor: lula, flávio bolsonaro, bolsonaro), não uma soma por `candidato_mencionado`. O backend hoje soma `aumento` dos rótulos normalizados "lula" e "flávio bolsonaro"/"bolsonaro" por hora. |
| Tabela Termos × Horas (ao lado da evolução) | `vw_em_alta` | `termos_txt` + `horas_desde_inicio` | `MAX(aumento)` | mesmos dois filtros, ordenado por horas asc | Confirmado |
| "Buscas em alta por Estado" (tabela com filtros Tema/Rótulo/Candidato/Estado) | `vw_em_alta` | Tema, Rótulo, Candidato, Termos | `MAX(aumento)`, `MAX(volume)` | os 4 dropdowns do bloco | Confirmado nos campos; o painel web hoje mantém uma linha por Estado em vez de agregar todas as UFs numa linha só por rótulo — se no relatório original a tabela esconde o Estado e agrega por rótulo/tema/candidato, é um ajuste de uma linha em `app/main.py`/no template, me avisa que eu faço |
| "Interesse nas últimas 24h" (barras empilhadas) | `vw_em_alta` | `inicio`, detalhe `rotulo` | `SUM(aumento)` | `situacao = "Em alta agora"`, top N | Confirmado na métrica; o Looker pede "N superiores = 100" e o painel web mostra os 10 rótulos de maior soma para não virar 100 cores numa barra — mantive 10 de propósito |

## Radar local / Interesse por município (últimos 7 dias)

| Bloco | Fonte | Dimensão | Métrica | Filtros | Status |
|---|---|---|---|---|---|
| Tabela "Radar local" (com dropdowns Local/Estado/Cidade alvo/Porte/Segmento/Macrotema) | `gtrends_monitoramento_cidades` | `macrotema`, `local`, `termo` | `AVG(indice_vs_ancora)` | `eh_ancora = false` (filtro "Exc_ancora"), últimos 7 dias | Confirmado (2º print de 20/10): o campo `indice_vs_ancora` está com "Cálculo de comparação: Nenhum" no Looker, ou seja, a variação dia-a-dia não é um campo nativo da métrica principal. A coluna "% Δ" da tabela é calculada à parte; o painel web reproduz isso no backend (`LAG` por dia no SQL, dia contra dia anterior), consistente com o texto do bloco ("veja a evolução de ontem para hoje") |

## Página 2 — Mobilização / território

| Bloco | Fonte | Observação |
|---|---|---|
| KPIs, Ranking, Acelerando, Onde agir, Segmento × conversa, Pauta por segmento | `vw_cidade_acao` | A view já entrega a coleta mais recente, uma linha por cidade |
| Índice por tema (usado no Ranking e em "Ações do dia") | `vw_territorio_ultimo` | Filtrado só em `macrotema IN ("Saúde","Educação","Aposentadoria e renda")`: os macrotemas de ataque (ATQ_*) e os de candidato nunca entram no "tema principal" de uma cidade |

## Página 3 — Pautas

| Bloco | Fonte | Observação |
|---|---|---|
| Lista "em alta" | `vw_pautas` | Uma linha por termo, sempre a coleta mais recente dele (`QUALIFY` pela data máxima por `termo_base`) |

## O que ainda precisa de confirmação sua

1. **"Share de pauta eleitoral"**: é um campo que já existe fisicamente em `vw_em_alta` (criado direto na view, não é um campo calculado do Looker). Para pegar a fórmula exata, rode no console do BigQuery e me mande o resultado:
   ```sql
   SELECT ddl FROM `comite-tecnologia.analise_redes.INFORMATION_SCHEMA.VIEWS` WHERE table_name = 'vw_em_alta'
   ```
   Esta sessão não tem credencial do BigQuery pra rodar isso direto.

Os outros dois pontos (quebra Lula/Flávio na Evolução por hora e variação % do radar local) foram confirmados em 20/10 e já estão corrigidos no código e na tabela acima.
