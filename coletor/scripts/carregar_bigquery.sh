#!/usr/bin/env bash
# Carrega os CSVs de data/ no BigQuery de forma segura: sempre SUBSTITUI a tabela
# (WRITE_TRUNCATE), nunca soma (WRITE_APPEND). Os CSVs já são a fonte completa e
# sem duplicidade (o coletor nunca grava a mesma busca duas vezes no mesmo dia),
# então recarregar por cima é o jeito idempotente: rodar isso 1x ou 50x no mesmo
# dia dá sempre o mesmo resultado na tabela, nunca duplica linha.
#
# Uso (a partir da raiz do coletor, com `gcloud auth login` ou dentro do Cloud Shell):
#   PROJETO=comite-tecnologia DATASET=analise_redes bash scripts/carregar_bigquery.sh
set -euo pipefail

PROJETO="${PROJETO:-comite-tecnologia}"
DATASET="${DATASET:-analise_redes}"
LOCAL="${BQ_LOCATION:-southamerica-east1}"
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

carregar() {
  local csv="$1" tabela="$2"
  if [ ! -f "$RAIZ/data/$csv" ]; then
    echo "aviso: $csv não existe em data/, pulando"
    return
  fi
  echo "Carregando $csv -> ${DATASET}.${tabela} (substituindo a tabela inteira)"
  bq load --project_id="$PROJETO" --location="$LOCAL" \
    --source_format=CSV --skip_leading_rows=1 --autodetect --replace \
    "${DATASET}.${tabela}" "$RAIZ/data/$csv"
}

# geo_map.csv -> gtrends_monitoramento_cidades (busca por estado e por cidade, inclusive termos de ataque)
carregar geo_map.csv gtrends_monitoramento_cidades
# related_queries.csv -> gtrends_monitoramento_temas (buscas relacionadas de candidatos e temas)
carregar related_queries.csv gtrends_monitoramento_temas

echo "Pronto. --replace garante que rodar de novo não duplica nada."
