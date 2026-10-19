# Monitor da Virada

Inteligência de dados do 2º turno 2026 (Lula × Flávio Bolsonaro, 25/10) a partir do
Google Trends. Duas partes neste repositório:

- **`coletor/`** — job que busca o Google Trends via SerpApi e grava no BigQuery
  (`comite-tecnologia.analise_redes`). Roda de hora em hora pelo GitHub Actions.
- **`web/`** — painel "Monitor da Virada", FastAPI + Cloud Run, lendo direto do
  BigQuery e protegido por IAP. Reproduz o dashboard do Looker Studio como app.

```
SerpApi ──(coletor/, hora em hora)──> BigQuery ──(web/, cache 15 min)──> painel (IAP)
```

## Qual base alimenta cada análise

**[docs/DADOS.md](docs/DADOS.md)** lista, bloco por bloco do painel, exatamente qual
tabela/view do BigQuery, qual dimensão, qual métrica e qual filtro foi usado —
extraído direto da configuração real do relatório no Looker Studio, com os pontos
que ainda dependem de confirmação sinalizados.

Documentação complementar:
- [`coletor/docs/metodologia.md`](coletor/docs/metodologia.md) — como cada tabela é
  preenchida (geos, termos, cálculo do índice vs. âncora).
- [`coletor/docs/operacao.md`](coletor/docs/operacao.md) — operação do coletor
  (orçamento de consultas, grupos de termos, troubleshooting).
- [`web/README.md`](web/README.md) — arquitetura do painel, deploy no Cloud Run,
  custos e segurança.

## Importante: dados sensíveis

A segmentação da campanha (`config/cidades_segmentacao.csv` do coletor: recorte,
segmento, prioridade por cidade) **não está neste repositório público**. Ela fica
listada no `.gitignore` do coletor; para rodar localmente, coloque o arquivo
original em `coletor/config/cidades_segmentacao.csv` (mantendo as colunas
`cod_tse, uf, municipio, municipio_norm, recorte, segmento, porte,
rank_no_segmento_recorte`) — ele nunca é commitado.

## Subir cada parte

- Coletor: `coletor/README.md` (segredos via GitHub Actions secrets, config em
  `coletor/config/*.yaml`).
- Painel: `web/README.md` (`bash web/deploy.sh` no Cloud Shell, com IAP).
