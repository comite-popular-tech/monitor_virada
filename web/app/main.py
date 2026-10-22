"""Monitor da Virada: página + API lendo o BigQuery, para rodar no Cloud Run atrás do IAP."""
import json
import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse

from . import queries, transform

PROJETO = os.getenv("BQ_PROJECT", "comite-tecnologia")
DATASET = os.getenv("BQ_DATASET", "analise_redes")
LOCAL_BQ = os.getenv("BQ_LOCATION", "southamerica-east1")
TTL = int(os.getenv("CACHE_TTL_S", "900"))  # 15 min
BASE = Path(__file__).parent
TEMPLATE = (BASE / "static" / "index.tpl.html").read_text(encoding="utf-8")
GEO = json.loads((BASE / "data" / "geo.json").read_text(encoding="utf-8"))
log = logging.getLogger("monitor")
app = FastAPI(title="Monitor da Virada", docs_url=None, redoc_url=None)

_cliente = None
_lock = threading.Lock()
_cache = {"t": 0.0, "pagina": None, "radar": None}


def cliente():
    global _cliente
    if _cliente is None:
        from google.cloud import bigquery
        _cliente = bigquery.Client(project=PROJETO, location=LOCAL_BQ)
    return _cliente


def consultar(nome):
    sql = queries.TODAS[nome].format(p=PROJETO, d=DATASET)
    t0 = time.time()
    df = cliente().query(sql).to_dataframe(create_bqstorage_client=False)
    log.info("consulta %s: %s linhas em %.1fs", nome, len(df), time.time() - t0)
    return df


def _montar():
    agora = datetime.now(ZoneInfo("America/Sao_Paulo"))
    # as 5 consultas rodam em paralelo (a primeira abertura depois de 15 min fica mais rápida)
    with ThreadPoolExecutor(max_workers=len(queries.TODAS)) as ex:
        r = dict(zip(queries.TODAS, ex.map(consultar, queries.TODAS)))
    ea = r["em_alta"]
    dia = ea["dia_ref"].iloc[0] if len(ea) else agora.strftime("%Y-%m-%d")
    emalta, hora, h24 = transform.em_alta(ea, dia)
    # D.days: todos os dias presentes em vw_em_alta (não só o mais recente) —
    # a página usa isso pra montar a janela padrão de exibição (ver index.tpl.html)
    dias = sorted({str(d) for d in ea["dia"].dropna().unique()}) if len(ea) and "dia" in ea else [dia]
    if dia not in dias:
        dias = sorted(set(dias) | {dia})
    dados = dict(GEO, days=dias, emalta=emalta, hora=hora, h24=h24,
                 cid=transform.cidades(r["cidade_acao"], r["territorio"], dia),
                 pautas=transform.pautas(r["pautas"], dia), radar=[], radarApi=True,
                 atualizado=agora.strftime("%d/%m/%Y %H:%M"))
    return dados, transform.preparar_radar(r["radar"])


def dados(forcar=False):
    """Devolve (pagina, radar), refazendo as consultas no máximo a cada TTL segundos."""
    if not forcar and _cache["pagina"] is not None and time.time() - _cache["t"] < TTL:
        return _cache["pagina"], _cache["radar"]
    with _lock:
        if forcar or _cache["pagina"] is None or time.time() - _cache["t"] >= TTL:
            try:
                pagina, radar = _montar()
            except Exception:
                log.exception("falha ao consultar o BigQuery")
                if _cache["pagina"] is None:
                    raise
                # mantém a última versão boa e tenta de novo em 1 minuto
                _cache["t"] = time.time() - TTL + 60
                return _cache["pagina"], _cache["radar"]
            _cache.update(t=time.time(), pagina=pagina, radar=radar)
    return _cache["pagina"], _cache["radar"]


SEM_CACHE = {"Cache-Control": "no-store"}


@app.exception_handler(Exception)
def erro(_req, _exc):
    return HTMLResponse("<!doctype html><meta charset=utf-8><title>Monitor da Virada</title>"
                        "<body style='font-family:sans-serif;padding:40px'><h1>Monitor da Virada</h1>"
                        "<p>Não foi possível ler o BigQuery agora. Tente de novo em instantes.</p>"
                        "<p style='color:#777'>Detalhes nos logs do Cloud Run.</p>", status_code=503)


# chaves pesadas que crescem a cada dia que vw_em_alta acumula (sem recorte fixo
# de 24h, ver queries.py): não vão inline no HTML, o template busca via /api/dados
PESADAS = ("emalta", "hora", "h24", "cid", "pautas")


@app.get("/", response_class=HTMLResponse)
def pagina():
    d, _ = dados()
    leve = {**{k: v for k, v in d.items() if k not in PESADAS}, **{k: [] for k in PESADAS}, "dadosApi": True}
    js = json.dumps(leve, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return HTMLResponse(TEMPLATE.replace("/*DATA*/", js), headers=SEM_CACHE)


@app.get("/api/dados")
def api_dados():
    d, _ = dados()
    return JSONResponse({k: v for k, v in d.items() if k not in GEO}, headers=SEM_CACHE)


@app.get("/api/radar")
def api_radar(local: str = "", uf: str = "", alvo: str = "", porte: str = "", seg: str = "", mac: str = "",
              pf_uf: str = "", q: str = Query("", max_length=80)):
    _, radar = dados()
    filtros = dict(local=local, uf=uf, alvo=alvo, porte=porte, seg=seg, mac=mac)
    return JSONResponse(transform.filtrar_radar(radar, filtros, pf_uf or None, q or None), headers=SEM_CACHE)


@app.get("/saude")
def saude():
    idade = time.time() - _cache["t"] if _cache["pagina"] else None
    return {"ok": True, "cache_s": None if idade is None else round(idade)}
