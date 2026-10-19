"""Confere as 5 consultas no BigQuery antes do deploy.

    python check.py              # dry run: valida colunas e mostra quanto cada consulta lê (não cobra)
    python check.py --executar   # roda de verdade e mostra linhas e uma amostra

Usa a sua credencial (no Cloud Shell já está pronta; no computador: gcloud auth application-default login).
"""
import os
import sys

from google.cloud import bigquery

from app import queries

PROJETO = os.getenv("BQ_PROJECT", "comite-tecnologia")
DATASET = os.getenv("BQ_DATASET", "analise_redes")
LOCAL = os.getenv("BQ_LOCATION", "southamerica-east1")


def main():
    executar = "--executar" in sys.argv
    cli = bigquery.Client(project=PROJETO, location=LOCAL)
    falhas = 0
    for nome, sql in queries.TODAS.items():
        sql = sql.format(p=PROJETO, d=DATASET)
        try:
            if executar:
                df = cli.query(sql).to_dataframe(create_bqstorage_client=False)
                print(f"OK  {nome:12} {len(df):>8} linhas")
                if len(df):
                    print("    " + df.head(3).to_string(max_colwidth=28).replace("\n", "\n    "))
            else:
                job = cli.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False))
                print(f"OK  {nome:12} lê {job.total_bytes_processed / 1e6:,.1f} MB")
        except Exception as e:  # mostra o erro do BigQuery (ex.: coluna que não existe)
            falhas += 1
            msg = getattr(e, "message", None) or str(e)
            print(f"ERRO {nome:11} {msg.splitlines()[0][:300]}")
    print("\nTudo certo." if not falhas else f"\n{falhas} consulta(s) com erro: ajuste app/queries.py antes do deploy.")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
