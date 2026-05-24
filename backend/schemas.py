"""Schemas Pydantic devolvidos pelo backend ao frontend Next.js."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class AreaResumo(BaseModel):
    nome: str
    agentes: int
    pct_risco: float
    modalidade: str
    ocorrencias: int
    roubos: int
    furtos: int
    denuncias: int
    fatores: int
    cameras: int
    bingos: int
    top_fator: str
    top_tipo: str
    ranking: str
    centro: tuple[float, float]      # [lon, lat]
    poligono_geojson: dict[str, Any]


class TotaisVisaoGeral(BaseModel):
    areas: int
    agentes_alocados: int
    agentes_totais: int = 600
    ocorrencias: int
    denuncias: int
    fatores: int
    bingos: int


class VisaoGeralResponse(BaseModel):
    totais: TotaisVisaoGeral
    areas: list[AreaResumo]
