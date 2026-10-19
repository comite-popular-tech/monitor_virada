#!/usr/bin/env bash
# Sobe o Monitor da Virada no Cloud Run, protegido pelo IAP (só entra quem tiver acesso liberado).
# Rode no Cloud Shell, dentro da pasta do projeto:  bash deploy.sh
# Pode rodar de novo a qualquer momento: cada passo é idempotente e o último publica a versão nova.
set -euo pipefail

PROJETO="${PROJETO:-comite-tecnologia}"
REGIAO="${REGIAO:-southamerica-east1}"
SERVICO="${SERVICO:-monitor-virada}"
DATASET="${DATASET:-analise_redes}"
SA_NOME="${SA_NOME:-monitor-virada}"
# e-mails ou grupos que podem abrir o painel, separados por espaço. Ex.:
#   ACESSOS="user:renata@exemplo.com group:comite@exemplo.com" bash deploy.sh
ACESSOS="${ACESSOS:-user:$(gcloud config get-value account 2>/dev/null)}"

SA="${SA_NOME}@${PROJETO}.iam.gserviceaccount.com"
gcloud config set project "$PROJETO" >/dev/null
NUM=$(gcloud projects describe "$PROJETO" --format='value(projectNumber)')

echo "1/6 Ativando APIs"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com \
  iap.googleapis.com bigquery.googleapis.com

echo "2/6 Conta de serviço do painel (só leitura no dataset)"
gcloud iam service-accounts describe "$SA" >/dev/null 2>&1 || \
  gcloud iam service-accounts create "$SA_NOME" --display-name="Monitor da Virada (leitura BigQuery)"
gcloud projects add-iam-policy-binding "$PROJETO" --member="serviceAccount:$SA" \
  --role=roles/bigquery.jobUser --condition=None >/dev/null
bq query --location="$REGIAO" --nouse_legacy_sql \
  "GRANT \`roles/bigquery.dataViewer\` ON SCHEMA \`${PROJETO}.${DATASET}\` TO \"serviceAccount:${SA}\""

echo "3/6 Build e deploy no Cloud Run (com IAP, sem acesso público)"
gcloud run deploy "$SERVICO" --source . --region "$REGIAO" \
  --service-account "$SA" --no-allow-unauthenticated --iap \
  --memory 2Gi --cpu 1 --min-instances 0 --max-instances 3 --concurrency 40 --timeout 120 \
  --set-env-vars "BQ_PROJECT=${PROJETO},BQ_DATASET=${DATASET},BQ_LOCATION=${REGIAO},CACHE_TTL_S=900"

echo "4/6 Permitindo que o IAP chame o serviço"
gcloud beta services identity create --service=iap.googleapis.com --project="$PROJETO" >/dev/null 2>&1 || true
gcloud run services add-iam-policy-binding "$SERVICO" --region "$REGIAO" \
  --member="serviceAccount:service-${NUM}@gcp-sa-iap.iam.gserviceaccount.com" --role=roles/run.invoker >/dev/null

echo "5/6 Liberando acesso: $ACESSOS"
for m in $ACESSOS; do
  gcloud iap web add-iam-policy-binding --member="$m" --role=roles/iap.httpsResourceAccessor \
    --region="$REGIAO" --resource-type=cloud-run --service="$SERVICO" >/dev/null
done

echo "6/6 Pronto"
gcloud run services describe "$SERVICO" --region "$REGIAO" --format='value(status.url)'
