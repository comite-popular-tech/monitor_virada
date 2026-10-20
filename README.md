# Monitor da Virada (web)

Painel "Monitor da Virada" do 2º turno 2026 (Lula × Flávio Bolsonaro, 25/10):
FastAPI + Cloud Run, lendo direto do BigQuery (`comite-tecnologia.analise_redes`)
e protegido por IAP. Reproduz o relatório do Looker Studio como app.

```
BigQuery (comite-tecnologia.analise_redes) ──(web/, cache 15 min)──> painel (IAP)
```

A coleta (SerpApi → BigQuery) é feita por outro repositório, não por este.

## Qual base alimenta cada análise

**[docs/DADOS.md](docs/DADOS.md)** lista, bloco por bloco do painel, exatamente qual
tabela/view do BigQuery, qual dimensão, qual métrica e qual filtro foi usado —
extraído direto da configuração real do relatório no Looker Studio.

## Subir

`web/README.md` tem a arquitetura completa, deploy no Cloud Run (`bash web/deploy.sh`
no Cloud Shell, com IAP) e custos/segurança.
