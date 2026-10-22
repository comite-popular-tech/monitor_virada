import json

import pytest
from fastapi.testclient import TestClient

from app import main, queries, transform
from tests import falso


@pytest.fixture()
def cli(monkeypatch):
    chamadas = []

    def consultar(nome):
        chamadas.append(nome)
        return falso.consultar(nome)

    monkeypatch.setattr(main, "consultar", consultar)
    main._cache.update(t=0.0, pagina=None, radar=None)
    c = TestClient(main.app)
    c.chamadas = chamadas
    return c


def _D(html):
    i = html.index("const D=") + len("const D=")
    return json.loads(html[i:html.index(";\n", i)])


def test_pagina_injeta_dados_leve(cli):
    """A página inicial vem leve (emalta/hora/h24/cid/pautas vazios, dadosApi=True):
    esses arrays crescem a cada dia que vw_em_alta acumula (sem recorte fixo de 24h,
    ver queries.py) e por isso não vão mais inline no HTML -- o template busca o
    resto via fetch('/api/dados') no browser (ver test_api_dados abaixo)."""
    r = cli.get("/")
    assert r.status_code == 200 and "/*DATA*/" not in r.text
    D = _D(r.text)
    assert D["radarApi"] is True and D["dadosApi"] is True and D["days"] == ["2026-10-18", "2026-10-19"]
    assert {"focus", "brasil", "cent", "emalta", "hora", "h24", "cid", "pautas"} <= set(D)
    assert D["emalta"] == [] and D["hora"] == [] and D["h24"] == [] and D["cid"] == [] and D["pautas"] == []


def test_api_dados_traz_o_pesado(cli):
    cli.get("/")  # popula o cache
    j = cli.get("/api/dados").json()
    assert j["days"] == ["2026-10-18", "2026-10-19"]
    # duas datas de coleta nos dados falsos (ver tests/falso.py) -> 48 horas na série
    assert len(j["hora"]) == 48 and all(e["d"] in j["days"] for e in j["emalta"])
    c = {x["c"]: x for x in j["cid"]}
    assert c["Sabará"]["x"] is not None and set(c["Sabará"]["idx"]) == {"Saúde", "Educação", "Aposentadoria e renda"}
    assert c["Munhoz de Mello"]["x"] is not None          # grafia diferente no IBGE (Munhoz de Melo)


def test_cache_nao_repete_consultas(cli):
    cli.get("/")
    cli.get("/api/radar")
    cli.get("/")
    assert sorted(cli.chamadas) == sorted(queries.TODAS)  # cada consulta uma vez só


def test_radar_filtra_e_opcoes_dependentes(cli):
    j = cli.get("/api/radar").json()
    assert len(j["rows"]) <= 100 and j["rows"] == sorted(j["rows"], key=lambda r: -r["idx"])
    assert "Aposentadoria e renda" in j["opts"]["mac"] and "Aposentadoria" not in j["opts"]["mac"]
    j = cli.get("/api/radar", params={"uf": "MG"}).json()
    assert {r["uf"] for r in j["rows"]} == {"MG"}
    assert "Maringá" not in j["opts"]["local"]            # local respeita o estado escolhido
    assert "PR" in j["opts"]["uf"]                         # o próprio campo continua mostrando todas as opções
    j = cli.get("/api/radar", params={"alvo": "Não"}).json()
    assert {r["local"] for r in j["rows"]} <= {"Santos", "Salvador"}
    j = cli.get("/api/radar", params={"q": "milic"}).json()
    assert {r["termo"] for r in j["rows"]} == {"flavio miliciano"}


def test_sem_html_injetavel(cli, monkeypatch):
    df = falso.pautas()
    df.loc[0, "consulta"] = "</script><script>alert(1)</script>"
    monkeypatch.setitem(falso.FONTES, "pautas", lambda: df)
    r = cli.get("/")
    # pautas não vai mais inline em "/" (ver test_pagina_injeta_dados_leve), mas a
    # escapagem do JSON embutido no HTML continua valendo pro que ainda é inline
    assert "</script><script>alert(1)" not in r.text
    # o conteúdo malicioso só aparece de fato via /api/dados -- que é JSON puro
    # (content-type application/json), não HTML, então não tem risco de quebra de tag
    assert cli.get("/api/dados").json()["pautas"][0]["q"].startswith("</script>")


def test_consultas_usam_projeto_e_dataset():
    for sql in queries.TODAS.values():
        s = sql.format(p="comite-tecnologia", d="analise_redes")
        assert "`comite-tecnologia.analise_redes." in s


def test_projecao_igual_ao_mockup():
    # Juiz de Fora no mockup fica em (482, 283) no mapa de 600x520
    x, y = transform.P_FOCO(*transform.coord("MG", "Juiz de Fora"))
    assert abs(x - 482) < 4 and abs(y - 283) < 4


def test_bigquery_fora_mantem_ultima_versao(cli, monkeypatch):
    assert cli.get("/").status_code == 200
    def quebra(nome):
        raise RuntimeError("bq fora")
    monkeypatch.setattr(main, "consultar", quebra)
    main._cache["t"] = 0.0                                  # cache vencido
    assert cli.get("/").status_code == 200                  # serve a versão anterior
    main._cache.update(t=0.0, pagina=None, radar=None)
    r = TestClient(main.app, raise_server_exceptions=False).get("/")
    assert r.status_code == 503 and "BigQuery" in r.text
