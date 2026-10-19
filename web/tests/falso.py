"""BigQuery simulado: devolve DataFrames com as mesmas colunas das consultas reais.

Uso local, sem credencial:  python -m tests.falso   (abre em http://127.0.0.1:8080)
"""
import random

import pandas as pd

random.seed(7)
CIDADES = [("SP", "Mauá", "RM São Paulo", "2. Disputa voto a voto", "grande (200 mil+)"),
           ("MG", "Sabará", "Minas Gerais", "2. Disputa voto a voto", "média (50 a 200 mil)"),
           ("MG", "Juiz de Fora", "Minas Gerais", "2. Disputa voto a voto", "grande (200 mil+)"),
           ("MG", "Montes Claros", "Minas Gerais", "2. Disputa voto a voto", "grande (200 mil+)"),
           ("MG", "Ipatinga", "Minas Gerais", "1. Mobilizar base", "grande (200 mil+)"),
           ("PR", "Maringá", "Interior PR", "4. Contenção", "grande (200 mil+)"),
           ("PR", "Londrina", "Interior PR", "4. Contenção", "grande (200 mil+)"),
           ("SC", "Chapecó", "Interior SC", "4. Contenção", "grande (200 mil+)"),
           ("GO", "Anápolis", "Goiás", "3. Reduzir diferença", "grande (200 mil+)"),
           ("PR", "Munhoz de Mello", "Interior PR", "4. Contenção", "pequena (<50 mil)")]
TEMAS = ["Saúde", "Educação", "Aposentadoria e renda"]


def em_alta():
    base = [("Debate", "Eleição", "Os dois", "debate band, debate lula e flavio", 100000),
            ("Panelaço", "Eleição", "Flávio / Bolsonaro", "panelaço, entrevista flávio bolsonaro", 100000),
            ("Lula", "Eleição", "Lula", "lula hoje, comício lula", 50000),
            ("Pagamento INSS outubro", "Aposentadoria e renda", "Nenhum", "inss calendário", 100000),
            ("Comando Vermelho", "Outros", "Nenhum", "comando vermelho, operação rio", 200000)]
    rows = []
    for rot, tema, cand, termos, vol in base:
        for uf in random.sample(["SP", "RJ", "MG", "BA", "PR", "RS", "PE"], 3):
            h = random.randint(0, 23)
            rows.append(dict(rotulo=rot, uf=uf, uf_iso="BR-" + uf, termos_txt=termos, tema=tema,
                             candidato_mencionado=cand, situacao=random.choice(["Em alta agora", "Encerrada"]),
                             inicio_ts=pd.Timestamp("2026-10-19 12:00", tz="UTC"), volume=float(vol),
                             aumento=float(random.choice([200, 500, 1000])), duracao_h=float(random.randint(1, 12)),
                             hora=h, dia_ref="2026-10-19", leitura_ref="19/10/2026 15:00"))
    return pd.DataFrame(rows)


def cidade_acao():
    rows = []
    for uf, c, rec, seg, porte in CIDADES:
        voto = {"1": .62, "2": .5, "3": .4, "4": .3}[seg[0]]
        dif = round(random.uniform(-.2, .15), 3)
        rows.append(dict(data_coleta="2026-10-19", uf=uf, cidade=c, cod_tse=str(random.randint(10000, 99999)),
                         recorte=rec, segmento=seg, porte=porte, tema_principal=random.choice(TEMAS),
                         tema_subindo=random.choice(TEMAS), sinal_busca="Flávio ocupa a conversa" if dif <= -.1 else
                         ("Lula ocupa a conversa" if dif >= .1 else "Busca alinhada ao voto"),
                         prioridade_acao="1 · Responder na disputa" if seg[0] == "2" and dif <= -.1 else
                         ("2 · Ampliar na disputa" if seg[0] == "2" else "4 · Monitorar"),
                         indice_tema_principal=random.uniform(50, 300), variacao_tema_subindo=random.uniform(-5, 40),
                         share_busca_lula=voto + dif, voto_lula_1t=voto, diferenca_busca_voto=dif))
    return pd.DataFrame(rows)


def territorio():
    return pd.DataFrame([dict(uf=uf, cidade=c, cod_tse="1", macrotema=t, indice=random.uniform(20, 300))
                         for uf, c, *_ in CIDADES for t in TEMAS])


def pautas():
    rows = []
    for base, alvo, mac, qs in [("lula", "Lula", "Candidatos", ["filho do lula bateu na mulher", "lula debate band"]),
                                ("flávio bolsonaro", "Flávio / Bolsonaro", "Candidatos", ["flavio bolsonaro miliciano"]),
                                ("inss", "Tema", "Aposentadoria e renda", ["inss pente fino"]),
                                ("creche", "Tema", "Educação", ["creche do vorcaro"])]:
        for q in qs:
            v = random.choice([5000.0, 9000.0, 300.0])
            rows.append(dict(data_coleta="2026-10-19", termo_base=base, alvo=alvo, macrotema=mac, consulta=q,
                             valor="Breakout" if v >= 5000 else f"+{int(v)}%", valor_num=v, explosao=v >= 5000,
                             nova=random.random() < .5, tambem_em_alta=random.random() < .3))
    return pd.DataFrame(rows)


def radar():
    rows = []
    termos = [("lula", "Candidatos"), ("bolsonaro", "Candidatos"), ("inss", "Aposentadoria"), ("ubs", "Saúde"),
              ("lulinha", "ATQ_LULA"), ("flavio miliciano", "ATQ_FLAVIO_PUSH")]
    for uf, c, rec, seg, porte in CIDADES + [("SP", "Santos", "", "", ""), ("BA", "Salvador", "", "", "")]:
        for t, m in termos:
            rows.append(dict(dia="2026-10-19", local=c, uf=uf, termo=t, macrotema=m, segmento=seg, porte=porte,
                             cidade_alvo=bool(seg), indice=random.uniform(10, 5000),
                             variacao_pct=None if random.random() < .2 else round(random.uniform(-30, 80), 1)))
    return pd.DataFrame(rows)


FONTES = dict(em_alta=em_alta, cidade_acao=cidade_acao, territorio=territorio, pautas=pautas, radar=radar)


def consultar(nome):
    return FONTES[nome]()


if __name__ == "__main__":
    import uvicorn
    from app import main
    main.consultar = consultar
    uvicorn.run(main.app, host="127.0.0.1", port=8080)
