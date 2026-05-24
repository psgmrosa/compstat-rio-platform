"""Detector de coincidências ("bingo") — o núcleo analítico da plataforma.

Cruza 3 camadas num mesmo segmento (grid):
  🔴 Mancha criminal (densidade de roubo/furto)
  🟡 Fator urbano (iluminação, vegetação, PSR, comércio irregular, etc.)
  🟠 Dinâmica criminal (densidade de denúncias do Disque Denúncia)

Quanto mais camadas se sobrepõem, maior o score e a prioridade da ação.
A saída alimenta o "Plano de Ação" do Relatório Analítico.
"""

from __future__ import annotations

from dataclasses import dataclass

import geopandas as gpd
import numpy as np
from shapely.geometry import box
from shapely.geometry.base import BaseGeometry

from .. import config


# Tamanho do grid em graus — ~110m a -22.9 lat (suficiente pra street segments).
GRID_SIZE_DEG = 0.001


@dataclass
class BingoCell:
    centro_lon: float
    centro_lat: float
    n_ocorrencias: int
    n_denuncias: int
    n_fatores: int
    fatores_principais: list[tuple[str, str]]  # [(fator, responsavel), ...]
    score: float                                # 0..1

    @property
    def camadas(self) -> int:
        return sum([
            self.n_ocorrencias >= 5,
            self.n_denuncias >= 2,
            self.n_fatores >= 1,
        ])


def _grid_index(geom_point) -> tuple[int, int]:
    return (int(geom_point.x / GRID_SIZE_DEG), int(geom_point.y / GRID_SIZE_DEG))


def detectar_bingos(
    poligono: BaseGeometry,
    ocorrencias: gpd.GeoDataFrame,
    denuncias: gpd.GeoDataFrame,
    fatores: gpd.GeoDataFrame,
    *,
    top_n: int = 8,
) -> list[BingoCell]:
    """Identifica células com sobreposição de camadas, ranqueadas por score."""
    cells: dict[tuple[int, int], dict] = {}

    def _bump(gdf, key: str, payload_col: tuple[str, str] | None = None):
        for _, row in gdf.iterrows():
            geom = row.geometry
            if geom is None or geom.is_empty:
                continue
            cx, cy = _grid_index(geom)
            cell = cells.setdefault(
                (cx, cy),
                {"n_ocorrencias": 0, "n_denuncias": 0, "n_fatores": 0,
                 "fatores": [], "x": cx, "y": cy},
            )
            cell[key] += 1
            if payload_col:
                fator = str(row.get(payload_col[0], "")).strip()
                orgao = str(row.get(payload_col[1], "")).strip()
                if fator:
                    cell["fatores"].append((fator, orgao))

    _bump(ocorrencias, "n_ocorrencias")
    _bump(denuncias, "n_denuncias")
    _bump(fatores, "n_fatores",
          payload_col=("tipo_ocorrencia_descricao", "orgao_responsavel"))

    if not cells:
        return []

    # Normaliza pra calcular score
    max_oc = max(c["n_ocorrencias"] for c in cells.values()) or 1
    max_dn = max(c["n_denuncias"] for c in cells.values()) or 1
    max_ft = max(c["n_fatores"] for c in cells.values()) or 1

    out: list[BingoCell] = []
    for c in cells.values():
        s = (
            0.5 * (c["n_ocorrencias"] / max_oc)
            + 0.3 * (c["n_denuncias"] / max_dn)
            + 0.2 * (c["n_fatores"] / max_ft)
        )
        out.append(BingoCell(
            centro_lon=(c["x"] + 0.5) * GRID_SIZE_DEG,
            centro_lat=(c["y"] + 0.5) * GRID_SIZE_DEG,
            n_ocorrencias=c["n_ocorrencias"],
            n_denuncias=c["n_denuncias"],
            n_fatores=c["n_fatores"],
            fatores_principais=c["fatores"][:5],
            score=round(s, 3),
        ))

    # Filtra: ao menos 2 camadas ativas
    out = [b for b in out if b.camadas >= 2]
    out.sort(key=lambda b: (-b.camadas, -b.score))
    return out[:top_n]


def bingos_para_plano_acao(bingos: list[BingoCell]) -> list[dict]:
    """Converte bingos em sugestões iniciais do Plano de Ação.

    Cada bingo vira uma ou mais ações, agrupadas por órgão responsável.
    O Claude refina/contextualiza depois.
    """
    plano: list[dict] = []
    for i, b in enumerate(bingos, start=1):
        if not b.fatores_principais:
            plano.append({
                "acao": (
                    f"FM — patrulhamento dirigido no ponto crítico "
                    f"({b.centro_lat:.5f}, {b.centro_lon:.5f}): "
                    f"{b.n_ocorrencias} ocorrências, {b.n_denuncias} denúncias."
                ),
                "responsavel": "Força Municipal",
                "prazo": "Ciclo CompStat atual",
                "status": "Sugerida",
            })
            continue
        # Uma ação por órgão único
        orgaos_vistos: set[str] = set()
        for fator, orgao in b.fatores_principais:
            orgao = orgao or "Órgão a definir"
            if orgao in orgaos_vistos:
                continue
            orgaos_vistos.add(orgao)
            plano.append({
                "acao": (
                    f"{orgao} — atuar sobre '{fator}' em ({b.centro_lat:.5f}, "
                    f"{b.centro_lon:.5f}). Coincide com "
                    f"{b.n_ocorrencias} ocorrências e {b.n_denuncias} denúncias."
                ),
                "responsavel": orgao,
                "prazo": "Ciclo CompStat atual",
                "status": "Sugerida",
            })
        plano.append({
            "acao": (
                f"FM — reforço de patrulhamento dirigido a este ponto "
                f"(score {b.score}, {b.camadas} camadas coincidentes)."
            ),
            "responsavel": "Força Municipal",
            "prazo": "Ciclo CompStat atual",
            "status": "Sugerida",
        })
    return plano
