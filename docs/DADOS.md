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
| Evolução por hora | `vw_em_alta` | `inicio` (data/hora da leitura) | `SUM(aumento)` | mesmos dois filtros da barra por Estado | Confirmado quanto à métrica (SUM(Aumento), não volume — isso estava diferente na primeira versão do painel e já foi corrigido). A quebra em duas linhas (Lula / Flávio) é reconstruída somando `aumento` dos assuntos com `candidato_mencionado` igual a cada um deles ou "Os dois" — essa regra de quebra não aparece no print, é a leitura que explica as duas séries da legenda. |
| Tabela Termos × Horas (ao lado da evolução) | `vw_em_alta` | `termos_txt` + `horas_desde_inicio` | `MAX(aumento)` | mesmos dois filtros, ordenado por horas asc | Confirmado |
| "Buscas em alta por Estado" (tabela com filtros Tema/Rótulo/Candidato/Estado) | `vw_em_alta` | Tema, Rótulo, Candidato, Termos | `MAX(aumento)`, `MAX(volume)` | os 4 dropdowns do bloco | Confirmado nos campos; o painel web hoje mantém uma linha por Estado em vez de agregar todas as UFs numa linha só por rótulo — se no relatório original a tabela esconde o Estado e agrega por rótulo/tema/candidato, é um ajuste de uma linha em `app/main.py`/no template, me avisa que eu faço |
| "Interesse nas últimas 24h" (barras empilhadas) | `vw_em_alta` | `inicio`, detalhe `rotulo` | `SUM(aumento)` | `situacao = "Em alta agora"`, top N | Confirmado na métrica; o Looker pede "N superiores = 100" e o painel web mostra os 10 rótulos de maior soma para não virar 100 cores numa barra — mantive 10 de propósito |

## Radar local / Interesse por município (últimos 7 dias)

| Bloco | Fonte | Dimensão | Métrica | Filtros | Status |
|---|---|---|---|---|---|
| Tabela "Radar local" (com dropdowns Local/Estado/Cidade alvo/Porte/Segmento/Macrotema) | `gtrends_monitoramento_cidades` | `macrotema`, `local`, `termo` | `AVG(indice_vs_ancora)` | `eh_ancora = false` (filtro "Exc_ancora"), últimos 7 dias | Confirmado na dimensão/métrica/filtro. A coluna de variação % (dia contra dia anterior) é um cálculo do painel web (`LAG` por dia no SQL), não localizei esse campo específico no recorte de tela do Looker — mantive porque é isso que aparece desenhado na tabela renderizada, mas se o campo oficial for outro me manda o print dele |

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

1. **"Share de pauta eleitoral"**: é um campo calculado que já existe em `vw_em_alta` no Looker; o print mostra só o nome, não a fórmula. Se você abrir o relatório → Recurso → Gerenciar campos adicionados/editor de campo calculado e me mandar a fórmula, eu troco o cálculo do backend por ela.
2. **Quebra Lula/Flávio na Evolução por hora**: o print não mostra uma dimensão de detalhe configurada nessa área do gráfico, só `inicio` + `SUM(Aumento)`; a legenda com duas linhas é reconstruída no painel web agrupando por `candidato_mencionado`. Se o gráfico original usa dois gráficos sobrepostos com filtro próprio (um por candidato) em vez de uma dimensão de detalhe, me avisa que ajusto.
3. **Variação % no radar local**: calculada no backend (dia contra dia anterior), não identifiquei um campo equivalente no recorte de tela do Looker.

Nenhum desses três pontos muda a fonte (tabela/view) usada — só a conta exata de um número dentro dela.
