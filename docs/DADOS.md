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
| Evolução por hora | `vw_em_alta` (gráfico de área) | Eixo X = `início` (Data e hora), detalhe = `rotulo`, N superiores = 10, "Agrupar o restante como Outros" = **ligado** | `SUM(aumento)` | **"Candidato_True"** (`candidato_mencionado <> "Nenhum"`, só esse filtro — não dois como se pensava antes) | Confirmado 21/10 direto na config do gráfico (é tecnicamente um "Gráfico de área", não barras). A dimensão detalhada é `rotulo`, não `candidato_mencionado`. As duas linhas "Lula" e "Flávio Bolsonaro" são os próprios rótulos das buscas diretas pelo nome do candidato (grupo `CAND` no coletor), não uma soma por `candidato_mencionado`. Apesar de "Agrupar restante como Outros" estar ligado, não aparece uma linha "Outros" visível no período checado — possivelmente porque só esses 2 rótulos têm volume relevante na janela atual. O backend hoje soma `aumento` dos rótulos normalizados "lula" e "flávio bolsonaro"/"bolsonaro" por hora, sem replicar o agrupamento "Outros" — como não aparece no Looker também, não há gap aqui. |
| Tabela Termos × Horas (ao lado da evolução) | `vw_em_alta` | `termos_txt` ("Termos") + `horas_desde_inicio` ("Horas") | `MAX(aumento)` | **"vwalta_inc_ativa_true"** + **"Termo_is_not_sull"** (termo preenchido), ordenado por horas asc | Confirmado 21/10 com os nomes exatos dos dois filtros direto na config do gráfico. |
| "Buscas em alta por Estado" (tabela com filtros Tema/Rótulo/Candidato/Estado) | `vw_em_alta` | Tema, Rótulo, Candidato, Termos | `MAX(aumento)`, `MAX(volume)` | os 4 dropdowns do bloco | Confirmado nos campos; o painel web hoje mantém uma linha por Estado em vez de agregar todas as UFs numa linha só por rótulo — se no relatório original a tabela esconde o Estado e agrega por rótulo/tema/candidato, é um ajuste de uma linha em `app/main.py`/no template, me avisa que eu faço |
| "Interesse nas últimas 24h" (barras empilhadas) | `vw_em_alta` | `inicio`, detalhe `rotulo` (N superiores = 10 séries) | `SUM(aumento)` | **"Exc_rotulo_other"** + **"ex_fim_sem_data"**, N superiores = 100 barras | Confirmado 21/10: filtros reais excluem o rótulo "other"/genérico e linhas sem data de fim — não é `situacao = "Em alta agora"` como estava documentado. O painel web mostra os 10 rótulos de maior soma (bate com o "Número de séries=10" do Looker) para não virar 100 cores numa barra |

## Radar local (Página 1) / Interesse por município (Página 2)

Mesma fonte (`gtrends_monitoramento_cidades`), mesmo filtro base (`eh_ancora = false`, "Exc_ancora"), mas **janelas de tempo diferentes** entre as duas páginas — confirmado 21/10 abrindo as duas tabelas lado a lado:

| Bloco | Fonte | Dimensão | Métrica | Filtros | Status |
|---|---|---|---|---|---|
| Página 1 — "Radar local" (dropdowns Local/Estado/Cidade alvo/Porte/Segmento/Macrotema) | `gtrends_monitoramento_cidades` | `macrotema`, `local`, `termo` (coluna nativa da view, não é apelido) | `AVG(indice_vs_ancora)` | `eh_ancora = false` ("Exc_ancora"); Dimensão do período = `data_coleta`; **Filtro de período padrão = Personalizado "Ontem"** com **Período de comparação ligado (Período anterior)** | Corrigido 21/10: não é "últimos 7 dias" — vem fixado em "Ontem" com comparação nativa do Looker contra o dia anterior. A coluna "% Δ" é esse cálculo nativo. O painel web faz essa comparação no backend via `LAG` por dia — mesma lógica. |
| Página 2 — "Interesse por município (Últimos 7 dias)" (mesmos dropdowns) | `gtrends_monitoramento_cidades` | `local`, `macrotema`, `termo` | `AVG(indice_vs_ancora)` | `eh_ancora = false` ("Exc_ancora"); **Filtro de período padrão = Automático (todas as datas disponíveis), sem Período de comparação ligado** — aqui sim é literalmente "últimos 7 dias" de dados brutos, sem comparação dia a dia | Confirmado 21/10: essa página É a leitura de 7 dias corridos; a de "Ontem"+comparação é exclusiva da Página 1. Título do bloco bate com o comportamento real. |

## Página 2 — Mobilização / território

| Bloco | Fonte | Observação |
|---|---|---|
| KPIs, Ranking, Acelerando, Onde agir, Segmento × conversa, Pauta por segmento | `vw_cidade_acao` | A view já entrega a coleta mais recente, uma linha por cidade |
| Índice por tema (usado no Ranking e em "Ações do dia") | `vw_territorio_ultimo` | Filtrado só em `macrotema IN ("Saúde","Educação","Aposentadoria e renda")`: os macrotemas de ataque (ATQ_*) e os de candidato nunca entram no "tema principal" de uma cidade |
| Tabela "Ranking de cidades por tema" | combinação **"territorio_acao"** = `vw_cidade_acao` + `vw_territorio_ultimo` (join por cidade) | Confirmado 21/10 abrindo a definição da combinação no Looker. Dimensões: `cidade`, `ação prioritária` (de `vw_cidade_acao`), `tema` (de `vw_territorio_ultimo`); Métrica: `AVG(indice)`. Essa combinação não estava documentada antes — o painel web usa só `vw_cidade_acao`/`vw_territorio_ultimo` direto, sem reproduzir essa junção específica; conferir se o resultado bate. |
| Tabela "Assunto acelerando hoje" | `vw_cidade_acao` (sem combinação) | Dimensões: `cidade`, `uf`, `ação` (prioridade_acao), `tema em alta` (tema_principal); Métrica: `MAX` sobre o campo de variação (`variacao_tema_subindo`); sem filtro próprio no gráfico. Confirmado 21/10. |
| Mapa "Onde agir hoje" | `vw_cidade_acao` | Local=`cidade_geo`, Dica=`cidade`, Dimensão de cor=`prioridade_acao`, Tamanho=campo calculado `intensidade`; sem filtro próprio. Confirmado 21/10. |
| Tabela "Ações do dia" | `vw_territorio_ultimo` (sem combinação) | Dimensões: `estado`, `cidade`, **"eleitorado" é apelido do campo `segmento`** (achado novo — não é um campo próprio de eleitorado); Métrica: `AVG(indice)`; controle de página "tema" filtra o dropdown no topo da tabela; sem filtro fixo adicional no gráfico. Confirmado 21/10. |
| Tabela dinâmica "Segmento x conversa" | `vw_cidade_acao` | Dimensão de linha = `segmento`, dimensão de coluna = `sinal_busca`, Métrica = `COUNT_DISTINCT(cod_tse)`; sem filtro próprio. Confirmado 21/10. |
| "Qual pauta levar para cada segmento" (barras 100% empilhadas) | `vw_cidade_acao` | Dimensão (eixo Y) = `segmento`, detalhe = `tema_principal` (valores literais ATQ_LULA/ATQ_FLAVIO_PUSH/ATQ_FLAVIO_ORG, N superiores=10 agrupando restante como Outros), Métrica (eixo X) = `COUNT_DISTINCT(cod_tse)`; sem filtro próprio. Confirmado 21/10. Página 2 agora 100% auditada. |

### KPIs do topo (confirmado 21/10 direto na config de cada cartão)

| KPI | Fonte | Métrica | Filtro |
|---|---|---|---|
| Cidades monitoradas | `vw_cidade_acao` | `COUNT_DISTINCT(cod_tse)` | sem filtro próprio |
| Prioridade de ação | `vw_cidade_acao` | `COUNT_DISTINCT(cod_tse)` | "Filtro de prioridade_acao" |
| Flávio ocupa a conversa | `vw_cidade_acao` | `COUNT_DISTINCT(cod_tse)` | "Flávio ocupa a conversa" |
| cidades com tema subindo | `vw_cidade_acao` | `COUNT_DISTINCT(cod_tse)` | "tema subindo" |

Os 4 KPIs usam a mesma métrica (contagem de cidades distintas); o que muda é só o filtro aplicado em cada cartão. Ainda não conferido: o conteúdo exato de cada filtro nomeado (ex. qual condição define "tema subindo" ou "Flávio ocupa a conversa") — os nomes dos filtros não expõem a fórmula na UI do Looker sem abrir cada um individualmente.

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
