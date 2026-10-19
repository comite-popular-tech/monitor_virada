"""Consultas ao BigQuery. Uma por fonte do painel, sempre na última coleta de cada fonte.

Os nomes de projeto e dataset vêm das variáveis de ambiente (veja config.py).
As conversões com SAFE_CAST deixam as consultas funcionando mesmo que uma coluna
tenha sido carregada como texto (ex.: data_coleta, eh_ancora, indice_vs_ancora).
"""

# Em alta: últimas 24h a partir da leitura mais recente (não de "agora"),
# assim o painel não fica vazio quando a coleta atrasa.
EM_ALTA = """
WITH base AS (
  SELECT rotulo, uf, uf_iso, termos_txt, tema, candidato_mencionado, situacao,
         SAFE_CAST(inicio AS TIMESTAMP) AS inicio_ts,
         SAFE_CAST(volume AS FLOAT64) AS volume,
         SAFE_CAST(aumento AS FLOAT64) AS aumento,
         SAFE_CAST(duracao_h AS FLOAT64) AS duracao_h
  FROM `{p}.{d}.vw_em_alta`
), ult AS (SELECT MAX(inicio_ts) AS mx FROM base)
SELECT b.*, EXTRACT(HOUR FROM b.inicio_ts AT TIME ZONE "America/Sao_Paulo") AS hora,
       FORMAT_TIMESTAMP("%Y-%m-%d", ult.mx, "America/Sao_Paulo") AS dia_ref,
       FORMAT_TIMESTAMP("%d/%m/%Y %H:%M", ult.mx, "America/Sao_Paulo") AS leitura_ref
FROM base b CROSS JOIN ult
WHERE b.inicio_ts >= TIMESTAMP_SUB(ult.mx, INTERVAL 24 HOUR)
"""

# Mobilização: uma linha por cidade (a view já está na coleta mais recente)
CIDADE_ACAO = """
SELECT CAST(data_coleta AS STRING) AS data_coleta, uf, cidade, CAST(cod_tse AS STRING) AS cod_tse,
       recorte, segmento, porte, tema_principal, tema_subindo, sinal_busca, prioridade_acao,
       SAFE_CAST(indice_tema_principal AS FLOAT64) AS indice_tema_principal,
       SAFE_CAST(variacao_tema_subindo AS FLOAT64) AS variacao_tema_subindo,
       SAFE_CAST(share_busca_lula AS FLOAT64) AS share_busca_lula,
       SAFE_CAST(voto_lula_1t AS FLOAT64) AS voto_lula_1t,
       SAFE_CAST(diferenca_busca_voto AS FLOAT64) AS diferenca_busca_voto
FROM `{p}.{d}.vw_cidade_acao`
"""

# Índice por tema em cada cidade (Ranking, Ações do dia, Pauta por segmento).
# Só os 3 temas de campanha: termos de ataque e candidatos ficam de fora.
TERRITORIO = """
SELECT uf, cidade, CAST(cod_tse AS STRING) AS cod_tse,
       CASE WHEN macrotema = "Aposentadoria" THEN "Aposentadoria e renda" ELSE macrotema END AS macrotema,
       SAFE_CAST(indice AS FLOAT64) AS indice
FROM `{p}.{d}.vw_territorio_ultimo`
WHERE macrotema IN ("Saúde", "Educação", "Aposentadoria", "Aposentadoria e renda")
"""

# Pautas: lista "em alta" da coleta mais recente de CADA termo
# (temas são coletados a cada 3 dias, candidatos todo dia).
PAUTAS = """
SELECT CAST(data_coleta AS STRING) AS data_coleta, termo_base, alvo, macrotema, consulta, valor,
       SAFE_CAST(valor_num AS FLOAT64) AS valor_num, explosao, nova, tambem_em_alta
FROM `{p}.{d}.vw_pautas`
WHERE lista = "em alta"
QUALIFY SAFE_CAST(data_coleta AS DATE) = MAX(SAFE_CAST(data_coleta AS DATE)) OVER (PARTITION BY termo_base)
"""

# Radar local: interesse por município na última coleta, com variação contra a coleta anterior.
RADAR = """
WITH t AS (
  SELECT SAFE_CAST(data_coleta AS DATE) AS dia, local, uf, termo, macrotema,
         IFNULL(segmento, "") AS segmento, IFNULL(porte, "") AS porte,
         LOWER(CAST(cidade_alvo AS STRING)) IN ("true", "sim") AS cidade_alvo,
         SAFE_CAST(indice_vs_ancora AS FLOAT64) AS indice
  FROM `{p}.{d}.gtrends_monitoramento_cidades`
  WHERE resolucao = "CITY" AND LOWER(CAST(eh_ancora AS STRING)) IN ("false", "não", "nao")
), ult AS (SELECT MAX(dia) AS mx FROM t),
base AS (
  SELECT dia, local, uf, termo, macrotema, segmento, porte, LOGICAL_OR(cidade_alvo) AS cidade_alvo,
         AVG(indice) AS indice
  FROM t, ult
  WHERE indice IS NOT NULL AND dia >= DATE_SUB(ult.mx, INTERVAL 7 DAY)
  GROUP BY 1, 2, 3, 4, 5, 6, 7
), lag AS (
  SELECT *, LAG(indice) OVER (PARTITION BY local, uf, termo ORDER BY dia) AS anterior FROM base
)
SELECT CAST(dia AS STRING) AS dia, local, uf, termo, macrotema, segmento, porte, cidade_alvo, indice,
       ROUND(SAFE_DIVIDE(indice - anterior, anterior) * 100, 1) AS variacao_pct
FROM lag, ult
WHERE dia = ult.mx
"""

TODAS = {
    "em_alta": EM_ALTA,
    "cidade_acao": CIDADE_ACAO,
    "territorio": TERRITORIO,
    "pautas": PAUTAS,
    "radar": RADAR,
}
