"""FastAPI app — expõe os analytics do CompStat Rio para o frontend Next.js.

Rodar localmente:

    .venv/bin/uvicorn backend.main:app --reload --port 8000
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from relint_gen import filters
from relint_gen.analytics import bingo as bingo_mod
from relint_gen.analytics import indicadores as ind_mod
from relint_gen.analytics import optimizer as opt_mod

from .schemas import AreaResumo, TotaisVisaoGeral, VisaoGeralResponse


app = FastAPI(
    title="CompStat Rio API",
    version="0.1.0",
    description=(
        "Analytics determinísticos do CompStat Municipal — cruzamento das 5 "
        "fontes oficiais por área FM."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def _build_visao_geral() -> VisaoGeralResponse:
    """Cruza camadas das 8 áreas FM. Cache de processo — roda 1× por boot."""
    areas = filters.list_areas()
    alocacoes = opt_mod.alocar_efetivo()
    aloc_by_name = {a.nome: a for a in alocacoes}

    resumos: list[AreaResumo] = []
    for nome in areas:
        ctx = filters.filter_by_area(nome, com_referencia=False)
        indic = ind_mod.indicadores(ctx.ocorrencias, ctx.nome)
        bingos = bingo_mod.detectar_bingos(
            ctx.poligono, ctx.ocorrencias, ctx.denuncias, ctx.fatores,
        )

        top_fator = "—"
        if (not ctx.fatores.empty
                and "tipo_ocorrencia_descricao" in ctx.fatores.columns):
            vc = ctx.fatores["tipo_ocorrencia_descricao"].value_counts()
            if len(vc):
                top_fator = str(vc.index[0])

        top_tipo = indic.distribuicao[0][1] if indic.distribuicao else "—"
        aloc = aloc_by_name.get(nome)

        resumos.append(AreaResumo(
            nome=nome,
            agentes=aloc.agentes if aloc else 0,
            pct_risco=aloc.pct_risco if aloc else 0.0,
            modalidade=aloc.modalidade_sugerida if aloc else "—",
            ocorrencias=indic.total,
            roubos=indic.roubos,
            furtos=indic.furtos,
            denuncias=len(ctx.denuncias),
            fatores=len(ctx.fatores),
            cameras=len(ctx.cameras),
            bingos=len(bingos),
            top_fator=top_fator,
            top_tipo=top_tipo,
            ranking=indic.ranking_str,
            centro=(ctx.poligono.centroid.x, ctx.poligono.centroid.y),
            poligono_geojson=ctx.poligono.__geo_interface__,
        ))

    totais = TotaisVisaoGeral(
        areas=len(resumos),
        agentes_alocados=sum(r.agentes for r in resumos),
        ocorrencias=sum(r.ocorrencias for r in resumos),
        denuncias=sum(r.denuncias for r in resumos),
        fatores=sum(r.fatores for r in resumos),
        bingos=sum(r.bingos for r in resumos),
    )
    return VisaoGeralResponse(totais=totais, areas=resumos)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/visao-geral", response_model=VisaoGeralResponse)
def visao_geral() -> VisaoGeralResponse:
    """Resumo consolidado das 8 áreas FM (totais + por-área).

    Resposta cacheada em memória — primeira chamada cruza ~50k pontos,
    chamadas seguintes são instantâneas.
    """
    return _build_visao_geral()
