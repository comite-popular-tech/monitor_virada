# Operação

## Primeiro uso (uma vez)

1. Configure a chave (`.env` local ou secret `SERPAPI_KEY` no GitHub).
2. `python -m coletor cota` para confirmar que a chave funciona e ver o saldo.
3. `python -m coletor plano` para ver as buscas do dia.
4. `python -m coletor teste --n 5` para gastar só 5 buscas e conferir `data/geo_map.csv`.
5. Se estiver tudo certo, deixe o GitHub Actions rodar todo dia (ou rode `executar`).

## Rotina diária (5 minutos)

1. Confira na aba **Actions** se a execução de hoje ficou verde.
2. Abra `data/log_coletas.csv` e veja se as buscas do dia estão com `status = ok`.
3. Rode `python -m coletor cota` (ou veja o log do workflow) e confira se o saldo bate com o plano.
4. Puxe os CSVs para a planilha ou o painel.

## Status no log

| status | Significado | O que fazer |
|---|---|---|
| `ok` | Coletou e salvou | nada |
| `sem_resultados` | Google não tem volume para essa consulta | normal em termos pequenos; não repete |
| `erro` | Falha pontual (rede, resposta estranha) | rode `executar` de novo: só as que falharam são refeitas |
| `erro_fatal` | Chave inválida ou cota/limite estourado | veja abaixo |

## Problemas comuns

- **"Chave SerpApi inválida (401)"**: confira o secret ou o `.env`, sem espaços nem aspas.
- **"Limite por hora atingido"**: espere a próxima hora e rode de novo. O que já foi coletado não é refeito.
- **"A reserva mínima seria atingida"**: a cota está acabando. Opções: contratar mais buscas, baixar `reserva_minima` em `config/coletas.yaml` ou tirar estados de `geos` no job `cidades` (cada estado = 11 buscas/dia).
- **Workflow não roda no horário**: o agendamento do GitHub pode atrasar até ~1h em horários de pico. Use **Run workflow** para rodar na mão.

## Mudar o plano sem estourar a cota

1. Edite `config/termos.yaml` ou `config/coletas.yaml`.
2. Rode `python -m coletor plano`: a última linha mostra o **total previsto até o fim do período**.
3. Some com o que já foi gasto (`coletor cota`) e confira se cabe no saldo da conta com folga.
4. Rode os testes (`python -m pytest -q`). O teste `test_plano_respeita_orcamento` vai falhar se o total mudar: atualize o número esperado de propósito.

Regras que o próprio script verifica:
- no máximo 4 termos por grupo (+ âncora);
- todo termo precisa de um macrotema;
- grupos usados nos jobs precisam existir.

## Atualizar a segmentação

Para mudar quais cidades recebem segmento, substitua `config/cidades_segmentacao.csv` mantendo as colunas `cod_tse, uf, municipio, municipio_norm, recorte, segmento, porte, rank_no_segmento_recorte`. O cruzamento é feito por `uf` + `municipio` (sem acento), então a grafia precisa ser a oficial do TSE/IBGE.

## Carregar no BigQuery sem duplicar

Este repositório só coleta e grava CSVs em `data/`; carregar isso no BigQuery é
um passo separado. **Nunca carregue em modo append** (`WRITE_APPEND`/sem
`--replace`): como `data/geo_map.csv` e `data/related_queries.csv` são
cumulativos (o coletor nunca reseta, só acrescenta o que é novo), um load em
append duplica o histórico inteiro toda vez que roda.

Use `scripts/carregar_bigquery.sh`, que faz `bq load --replace` (substitui a
tabela inteira pelo conteúdo atual do CSV a cada carga):

```bash
PROJETO=comite-tecnologia DATASET=analise_redes bash scripts/carregar_bigquery.sh
```

Como o coletor já garante que o CSV não tem a mesma busca duplicada no mesmo
dia (`ja_coletadas()` em `coletor/armazenamento.py`), rodar esse script
quantas vezes quiser no mesmo dia dá sempre a mesma tabela, nunca duplica
linha. Ele carrega:
- `geo_map.csv` → `gtrends_monitoramento_cidades`
- `related_queries.csv` → `gtrends_monitoramento_temas`

`gtrends_em_alta_brasil` (fonte de `vw_em_alta`) **não é gerada por este
repositório** — é produzida por outro processo (provavelmente uma consulta
agendada no próprio BigQuery, detectando o que está "em alta" a partir dos
dados brutos). Se esse processo também estiver em modo append sobre dados que
não mudam, a mesma correção (substituir em vez de somar) resolve lá também,
mas a definição dele está fora deste repositório.

## Depois de 24/10

O script não coleta nada fora do período. Para encerrar:
1. Desative o workflow (**Actions → … → Disable workflow**).
2. Troque ou apague a chave na SerpApi.
3. Exporte `data/` para o arquivo do projeto.
