-- comite-tecnologia.analise_redes.vw_lula_flavio_cidade
-- Corrigida em 22/10: mesma correção de cod_tse de vw_territorio.sql.
-- Ver sql/README.md pro contexto completo.
CREATE OR REPLACE VIEW `comite-tecnologia.analise_redes.vw_lula_flavio_cidade` AS
WITH g AS (
  SELECT
    data_coleta,
    COALESCE(uf, SUBSTR(geo_busca, 4)) AS uf,
    local AS cidade,
    cod_tse AS cod_tse_bruto, recorte, segmento, termo, valor
  FROM `comite-tecnologia.analise_redes.gtrends_monitoramento_cidades`
  WHERE resolucao = 'CITY' AND grupo = 'CAND'
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY data_coleta, geo_busca, local, termo
    ORDER BY hora_ingestao DESC) = 1
),
chave_tse AS (
  SELECT cod_tse, uf, municipio,
    TRIM(REGEXP_REPLACE(LOWER(REGEXP_REPLACE(NORMALIZE(uf || '|' || municipio, NFD), r"\p{Mn}", "")), r"[^a-z0-9|]+", " ")) AS k
  FROM `comite-tecnologia.analise_redes.tse_municipios_2026`
),
p AS (
  SELECT
    g.data_coleta, g.uf, g.cidade,
    COALESCE(g.cod_tse_bruto, t.cod_tse) AS cod_tse,
    g.recorte, g.segmento,
    MAX(IF(g.termo = 'lula', g.valor, NULL)) AS busca_lula,
    MAX(IF(g.termo = 'flávio bolsonaro', g.valor, NULL)) AS busca_flavio,
    MAX(IF(g.termo = 'bolsonaro', g.valor, NULL)) AS busca_bolsonaro
  FROM g
  LEFT JOIN chave_tse t
    ON t.k = TRIM(REGEXP_REPLACE(LOWER(REGEXP_REPLACE(NORMALIZE(g.uf || '|' || g.cidade, NFD), r"\p{Mn}", "")), r"[^a-z0-9|]+", " "))
  GROUP BY 1, 2, 3, 4, 5, 6
)
SELECT p.*,
  SAFE_DIVIDE(busca_lula, busca_lula + busca_flavio + busca_bolsonaro) AS share_busca_lula,
  t.lula_2cand_pct AS voto_lula_1t,
  SAFE_DIVIDE(busca_lula, busca_lula + busca_flavio + busca_bolsonaro) - t.lula_2cand_pct AS diferenca_busca_voto
FROM p
LEFT JOIN `comite-tecnologia.analise_redes.tse_municipios_2026` t
  ON SAFE_CAST(t.cod_tse AS INT64) = p.cod_tse
