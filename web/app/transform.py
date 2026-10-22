"""Converte o resultado das consultas no formato que a página do painel lê (objeto D)."""
import csv
import math
import unicodedata
from collections import defaultdict
from pathlib import Path

import pandas as pd

DATA = Path(__file__).parent / "data"
UF_COD = {11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA", 16: "AP", 17: "TO", 21: "MA", 22: "PI", 23: "CE",
          24: "RN", 25: "PB", 26: "PE", 27: "AL", 28: "SE", 29: "BA", 31: "MG", 32: "ES", 33: "RJ", 35: "SP",
          41: "PR", 42: "SC", 43: "RS", 50: "MS", 51: "MT", 52: "GO", 53: "DF"}


def _norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return " ".join(s.replace("'", " ").replace("-", " ").split())


def _proj(lon0, lon1, lat0, lat1, W, H):
    k = math.cos(math.radians((lat0 + lat1) / 2))
    s = min(W / ((lon1 - lon0) * k), H / (lat1 - lat0))
    ox = (W - (lon1 - lon0) * k * s) / 2
    oy = (H - (lat1 - lat0) * s) / 2
    return lambda lon, lat: (ox + (lon - lon0) * k * s, oy + (lat1 - lat) * s)


# mesma projeção do mapa "Onde agir hoje" (SP, MG, PR, SC, GO)
P_FOCO = _proj(-55, -40.5, -27, -15.5, 600, 520)
_COORD = {}
with (DATA / "municipios.csv").open(encoding="utf-8") as f:
    for r in csv.DictReader(f):
        uf = UF_COD.get(int(r["codigo_uf"]))
        _COORD[(uf, _norm(r["nome"]))] = (float(r["longitude"]), float(r["latitude"]))
# grafias que mudaram entre IBGE e TSE
_APELIDOS = {"embu": "embu das artes", "moji mirim": "mogi mirim", "moji das cruzes": "mogi das cruzes",
             "moji guacu": "mogi guacu", "munhoz de mello": "munhoz de melo", "bom jesus": "bom jesus de goias"}


def coord(uf, cidade):
    n = _norm(cidade)
    return _COORD.get((uf, n)) or _COORD.get((uf, _APELIDOS.get(n, n)))


def _nn(v):
    """NaN/None vira None (JSON null)."""
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    return v


def _b(v):
    v = _nn(v)
    if isinstance(v, str):
        return v.strip().lower() in ("true", "sim", "1")
    return bool(v) if v is not None else False


def em_alta(df, dia):
    """Monta as linhas de vw_em_alta e as duas séries por hora do Looker.

    df traz todo o conteúdo atual de vw_em_alta (sem recorte de 24h), cada linha
    com seu próprio dia de coleta (`r.dia`) — não um único `dia` fixo para tudo.
    `dia` aqui só serve de fallback para quando `r.dia` vem vazio.

    Evolução por hora e Interesse 24h usam SUM(Aumento), não volume, mas cada
    uma com seu próprio filtro fixo, confirmado direto na config de cada
    gráfico no Looker (docs/DADOS.md):
    - Evolução por hora: só "Candidato_True" (candidato_mencionado <> "Nenhum").
    - Interesse 24h: "Exc_rotulo_other" (rótulo genérico "other" fora) +
      "ex_fim_sem_data" (linha precisa ter duração/fim preenchido).
    Nenhuma das duas usa situacao="Em alta agora" nem termos_txt preenchido —
    esse filtro ("vwalta_inc_ativa_true" + "Termo_is_not_sull") é da tabela
    Termos × Horas, aplicado no frontend (ver index.tpl.html).

    A Evolução por hora é dimensão=início (data e hora), SUM(aumento), N
    superiores=10 (confirmado no Looker); as duas linhas Lula/Flávio Bolsonaro
    são os próprios rótulos das buscas diretas pelo nome do candidato (grupo
    CAND no coletor), não uma soma por candidato_mencionado. Veja docs/DADOS.md.
    """
    LULA, FLAVIO = "lula", "flávio bolsonaro"
    rows, hora, h24 = [], defaultdict(lambda: [0.0, 0.0]), defaultdict(float)
    dias = set()
    for r in df.itertuples(index=False):
        cand = _nn(r.candidato_mencionado) or "Nenhum"
        vol = float(_nn(r.volume) or 0)
        aum = float(_nn(r.aumento) or 0)
        h = int(_nn(r.hora) or 0)
        d = _nn(getattr(r, "dia", None)) or dia
        ativa = _nn(r.situacao) == "Em alta agora"
        termo = _nn(r.termos_txt) or ""
        rot = r.rotulo
        dur_raw = _nn(r.duracao_h)
        dias.add(d)
        rows.append(dict(d=d, geo=_nn(r.uf_iso) or "", uf=_nn(r.uf) or "", r=rot, t=termo,
                         tema=_nn(r.tema) or "Outros", cand=cand, vol=vol, aum=aum, h=h,
                         dur=float(dur_raw or 0), ativa=ativa))
        if cand != "Nenhum":
            rn = _norm(rot)
            if rn == LULA:
                hora[(d, h)][0] += aum
            elif rn == FLAVIO or rn == "bolsonaro":
                hora[(d, h)][1] += aum
        if _norm(rot) not in ("", "other", "outro", "outros") and dur_raw is not None:
            h24[(d, h, rot)] += aum
    # Evolução por hora: soma do Aumento (%) dos rótulos "lula" e "flávio bolsonaro"/"bolsonaro",
    # uma série de 24h por dia presente nos dados (igual ao eixo "início" do Looker)
    serie = [dict(d=d, h=h, lula=round(hora[(d, h)][0], 1), flavio=round(hora[(d, h)][1], 1))
             for d in sorted(dias) for h in range(24)]
    # Interesse 24h: 10 rótulos de maior soma de Aumento no recorte inteiro (todos os dias)
    tot = defaultdict(float)
    for (d, h, rot), v in h24.items():
        tot[rot] += v
    top = {r for r, _ in sorted(tot.items(), key=lambda x: -x[1])[:10]}
    v24 = [dict(d=d, h=h, r=rot, v=round(v, 1)) for (d, h, rot), v in sorted(h24.items()) if rot in top]
    return rows, serie, v24


def cidades(acao, terr, dia):
    idx = defaultdict(dict)
    for r in terr.itertuples(index=False):
        if _nn(r.indice) is not None:
            idx[(r.uf, r.cidade)][r.macrotema] = round(float(r.indice), 2)
    out = []
    for r in acao.itertuples(index=False):
        xy = coord(r.uf, r.cidade)
        x, y = P_FOCO(*xy) if xy else (None, None)
        dif = _nn(r.diferenca_busca_voto)
        out.append(dict(d=dia, c=r.cidade, uf=r.uf, cod_tse=_nn(r.cod_tse), recorte=_nn(r.recorte) or "",
                        seg=_nn(r.segmento) or "", porte=_nn(r.porte) or "", idx=idx.get((r.uf, r.cidade), {}),
                        tp=_nn(r.tema_principal) or "", ts=_nn(r.tema_subindo) or "",
                        tv=round(float(_nn(r.variacao_tema_subindo) or 0), 1), sinal=_nn(r.sinal_busca) or "",
                        pri=_nn(r.prioridade_acao) or "4 · Monitorar", voto=_nn(r.voto_lula_1t),
                        busca=_nn(r.share_busca_lula), dif=None if dif is None else round(float(dif), 3),
                        x=None if x is None else round(x), y=None if y is None else round(y)))
    return out


def pautas(df, dia):
    out = []
    for r in df.itertuples(index=False):
        out.append(dict(d=dia, base=r.termo_base, alvo=_nn(r.alvo) or "Tema", mac=_nn(r.macrotema) or "",
                        q=r.consulta, v=float(_nn(r.valor_num) or 0), nova=_b(r.nova), emalta=_b(r.tambem_em_alta),
                        expl=_b(r.explosao)))
    return out


# ---------------- radar (filtrado no servidor) ----------------
RADAR_CAMPOS = {"local": "local", "uf": "uf", "alvo": "alvo", "porte": "porte", "seg": "segmento", "mac": "macrotema"}


def preparar_radar(df):
    df = df.copy()
    df["macrotema"] = df["macrotema"].replace({"Aposentadoria": "Aposentadoria e renda"}).fillna("")
    df["alvo"] = df["cidade_alvo"].map(lambda v: "Sim" if _b(v) else "Não")
    for c in ("local", "uf", "segmento", "porte", "termo"):
        df[c] = df[c].fillna("").astype(str)
    df["_busca"] = (df["local"] + " " + df["termo"]).str.lower()
    return df


def filtrar_radar(df, filtros, pf_uf=None, q=None, limite=100):
    base = df
    if pf_uf:
        base = base[base["uf"] == pf_uf]
    if q:
        base = base[base["_busca"].str.contains(q.lower(), regex=False)]
    ativos = {k: v for k, v in filtros.items() if v and k in RADAR_CAMPOS}

    def aplica(d, pular=None):
        for k, v in ativos.items():
            if k != pular:
                d = d[d[RADAR_CAMPOS[k]] == v]
        return d

    sel = aplica(base)
    opts = {}
    for k, col in RADAR_CAMPOS.items():
        vals = aplica(base, pular=k)[col].dropna().unique().tolist()
        opts[k] = sorted((v for v in vals if v not in ("", "—")), key=lambda s: _norm(s))
    top = sel.nlargest(limite, "indice")
    rows = [dict(local=r.local, uf=r.uf, termo=r.termo, mac=r.macrotema, seg=r.segmento, porte=r.porte,
                 alvo=r.alvo, idx=round(float(r.indice), 2), dl=_nn(r.variacao_pct)) for r in top.itertuples(index=False)]
    return {"rows": rows, "opts": opts, "total": int(len(sel))}
