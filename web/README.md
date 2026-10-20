# Monitor da Virada (web)

Painel "Monitor da Virada" rodando no **Cloud Run**, lendo direto do **BigQuery** (`comite-tecnologia.analise_redes`) e protegido pelo **IAP**: só abre para quem tiver acesso liberado com conta Google.

```
navegador ──(login Google, IAP)──> Cloud Run: FastAPI ──> BigQuery (5 fontes)
                                     │  cache de 15 min
                                     ├─ /            página com os dados da última coleta
                                     ├─ /api/radar   radar por município, filtrado no servidor
                                     ├─ /api/dados   os mesmos dados da página, em JSON
                                     └─ /saude       verificação simples
```

## Fontes

| Bloco do painel | Fonte | Recorte |
|---|---|---|
| Página 1: share, pizza, top termos, mapa e barras por UF, Evolução por hora, Em alta agora, Interesse 24h | `vw_em_alta` | últimas 24h a partir da leitura mais recente |
| Radar local (p1) e Interesse por município (p2) | `gtrends_monitoramento_cidades` | últimos 7 dias, sem âncora, só cidades |
| Página 2: KPIs, Ranking, Acelerando, Onde agir, Segmento x conversa, Pauta por segmento | `vw_cidade_acao` | a view já traz a coleta mais recente |
| Índice por tema (Ranking, Ações do dia) | `vw_territorio_ultimo` | só Saúde, Educação e Aposentadoria e renda |
| Página 3 | `vw_pautas` | lista "em alta", última coleta de cada termo |

**[../docs/DADOS.md](../docs/DADOS.md)** detalha, bloco a bloco, a dimensão, a métrica e o filtro exatos usados em cada gráfico/tabela — confirmado contra a configuração real do relatório no Looker Studio. Leia antes de mexer em `app/queries.py` ou `app/transform.py`: as fórmulas já foram ajustadas pra bater com o relatório original.

Como os dados de cidade passam de centenas de milhares de linhas, o radar é filtrado no servidor e a página recebe só as 100 linhas de maior índice, com as opções dos filtros já calculadas.

As coordenadas das cidades do mapa "Onde agir hoje" vêm de `app/data/municipios.csv` (IBGE, projeto aberto kelvins/municipios-brasileiros), cruzadas por UF + nome.

## Subir (Cloud Shell)

1. Abra o [Cloud Shell](https://shell.cloud.google.com) no projeto `comite-tecnologia` e envie o zip (menu ⋮ → Upload).
2. Descompacte e entre na pasta:
   ```bash
   unzip monitor-virada-web.zip && cd monitor-virada-web
   ```
3. Confira as consultas (dry run, não cobra):
   ```bash
   pip install -q -r requirements.txt && python check.py
   ```
   Se alguma der `ERRO`, a mensagem diz qual coluna não existe; ajuste em `app/queries.py`.
4. Suba, liberando quem pode abrir:
   ```bash
   ACESSOS="user:voce@dominio.com group:comite@dominio.com" bash deploy.sh
   ```
   No fim aparece a URL do painel.

Para publicar uma versão nova, rode `bash deploy.sh` de novo.

### Liberar ou tirar acesso depois

```bash
gcloud iap web add-iam-policy-binding --member=user:pessoa@dominio.com \
  --role=roles/iap.httpsResourceAccessor --region=southamerica-east1 --resource-type=cloud-run --service=monitor-virada
# para tirar: remove-iam-policy-binding com os mesmos parâmetros
```

## Se der erro

- **"IAP ... OAuth" ou pedido de tela de consentimento**: projetos fora de uma organização precisam ativar o IAP uma vez pelo console (Segurança → Identity-Aware Proxy). Para liberar contas de fora do domínio, a tela de consentimento OAuth precisa estar como "Externo".
- **Build falha por permissão** (`cloudbuild` / `artifactregistry`): dê à conta de serviço padrão do Compute (`NUMERO-compute@developer.gserviceaccount.com`) os papéis *Cloud Build Service Account* e *Artifact Registry Writer*, e rode de novo.
- **GRANT ... ON SCHEMA falha**: quem roda o script precisa ser admin do dataset. Alternativa: no console do BigQuery, compartilhe o dataset com `monitor-virada@comite-tecnologia.iam.gserviceaccount.com` como *Leitor de dados*.
- **Página demora na primeira abertura**: é o cache vazio (as 5 consultas rodam em paralelo). Depois disso, 15 minutos de respostas imediatas.
- **Logs**: `gcloud run services logs read monitor-virada --region southamerica-east1` mostra o tempo e o número de linhas de cada consulta.

## Rodar no computador

```bash
pip install -r requirements-dev.txt
python -m pytest -q                 # testes com BigQuery simulado
python -m tests.falso               # painel com dados simulados em http://127.0.0.1:8080
gcloud auth application-default login && uvicorn app.main:app --port 8080   # com o BigQuery de verdade
```

## Custos e segurança

- Cloud Run com mínimo de 0 instâncias: sem acesso, sem custo. As consultas rodam no máximo a cada 15 min e só quando alguém abre o painel.
- A conta de serviço só lê o dataset `analise_redes` e roda consultas. Não escreve nada.
- Sem acesso público: o serviço exige o IAP. Não use `--allow-unauthenticated`.
- O painel mostra a segmentação da campanha (segmento, prioridade). Libere acesso só para quem precisa.
