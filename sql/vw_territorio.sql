-- comite-tecnologia.analise_redes.vw_territorio
-- Corrigida em 22/10: recupera cod_tse pra municípios que o join original perdia
-- por diferença de grafia (acento/apóstrofo/caixa) contra tse_municipios_2026.
-- Ver sql/README.md pro contexto completo.
CREATE OR REPLACE VIEW `comite-tecnologia.analise_redes.vw_territorio` AS
WITH g AS (
  SELECT *
  FROM `comite-tecnologia.analise_redes.gtrends_monitoramento_cidades`
  WHERE resolucao = 'CITY' AND NOT eh_ancora
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY data_coleta, geo_busca, grupo, local, termo
    ORDER BY hora_ingestao DESC) = 1
),
chave_tse AS (
  SELECT cod_tse, uf, municipio,
    TRIM(REGEXP_REPLACE(LOWER(REGEXP_REPLACE(NORMALIZE(uf || '|' || municipio, NFD), r"\p{Mn}", "")), r"[^a-z0-9|]+", " ")) AS k
  FROM `comite-tecnologia.analise_redes.tse_municipios_2026`
),
m AS (
  SELECT
    g.data_coleta,
    COALESCE(g.uf, SUBSTR(g.geo_busca, 4)) AS uf,
    g.local AS cidade,
    COALESCE(g.cod_tse, t.cod_tse) AS cod_tse,
    g.recorte, g.segmento, g.porte, g.macrotema,
    AVG(g.indice_vs_ancora) AS indice
  FROM g
  LEFT JOIN chave_tse t
    ON t.k = TRIM(REGEXP_REPLACE(LOWER(REGEXP_REPLACE(NORMALIZE(COALESCE(g.uf, SUBSTR(g.geo_busca, 4)) || '|' || g.local, NFD), r"\p{Mn}", "")), r"[^a-z0-9|]+", " "))
  WHERE g.macrotema != 'Candidatos'
  GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
)
SELECT *,
  indice - LAG(indice) OVER (PARTITION BY uf, cidade, macrotema ORDER BY data_coleta) AS variacao_dia,
  CONCAT(cidade, ', ', uf, ', Brasil') AS cidade_geo,
  RANK() OVER (PARTITION BY data_coleta, uf, cidade ORDER BY indice DESC) = 1 AS tema_principal
FROM m
