"""Indicadores quantitativos — contagens, ranking entre áreas FM, distribuição."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import geopandas as gpd
import pandas as pd

from .. import data_loaders


@dataclass
class IndicadoresResult:
    periodo: str
    roubos: int
    furtos: int
    total: int
    ranking_str: str
    distribuicao: list[tuple[int, str, int, float]]   # (rank, tipo, qtd, pct)


def _detect_periodo(ocorrencias: gpd.GeoDataFrame) -> str:
    if ocorrencias.empty or "ano" not in ocorrencias.columns:
        return "Indisponível"
    anos = ocorrencias["ano"].dropna().astype(int)
    if anos.empty:
        return "Indisponível"
    return f"01/01/{anos.min()} a 31/12/{anos.max()}"


def _ocorrencias_por_area() -> dict[str, int]:
    """Mapeia nome da área FM → contagem total de ocorrências.

    Cache de classe para acelerar geração múltipla (ranking entre áreas).
    """
    areas = data_loaders.load_areas_fm()
    ocs = data_loaders.load_ocorrencias()
    # spatial join pra contar uma vez todas as ocorrências por área
    joined = gpd.sjoin(ocs[["geometry"]], areas[["nome_area", "geometry"]],
                       how="inner", predicate="intersects")
    return joined.groupby("nome_area").size().to_dict()


@lru_cache(maxsize=1)
def _ranking_global() -> list[tuple[str, int]]:
    contagem = _ocorrencias_por_area()
    return sorted(contagem.items(), key=lambda x: -x[1])


def indicadores(ocorrencias_filtradas: gpd.GeoDataFrame,
                area_nome: str) -> IndicadoresResult:
    """Calcula indicadores do período para uma área."""
    df = ocorrencias_filtradas
    periodo = _detect_periodo(df)

    # Roubo (delito 15) vs furto (delito ~14). Usamos `desc_delito` quando disponível.
    if "desc_delito" in df.columns:
        s = df["desc_delito"].fillna("").str.lower()
        roubos = int(s.str.contains("roubo").sum())
        furtos = int(s.str.contains("furto").sum())
    else:
        roubos = int(len(df))
        furtos = 0
    total = int(len(df))

    # Distribuição por tipo (top 5)
    distribuicao: list[tuple[int, str, int, float]] = []
    if "desc_delito" in df.columns and total > 0:
        top = (df["desc_delito"].fillna("Não classificado").value_counts().head(5))
        for i, (tipo, qtd) in enumerate(top.items(), start=1):
            distribuicao.append((i, str(tipo), int(qtd), 100 * qtd / total))

    # Ranking global
    ranking = _ranking_global()
    ranking_str = "—"
    total_global = sum(v for _, v in ranking) or 1
    for i, (nome, qtd) in enumerate(ranking, start=1):
        if nome.strip() == area_nome.strip():
            pct = 100 * qtd / total_global
            ranking_str = f"{i}º lugar ({pct:.1f}% do total das áreas FM)"
            break

    return IndicadoresResult(
        periodo=periodo, roubos=roubos, furtos=furtos, total=total,
        ranking_str=ranking_str, distribuicao=distribuicao,
    )
