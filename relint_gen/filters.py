"""Filtro espacial: dada uma área FM, devolve todas as fontes recortadas para ela."""

from __future__ import annotations

from dataclasses import dataclass, field

import geopandas as gpd
from shapely.geometry.base import BaseGeometry

from . import config, data_loaders


@dataclass
class AreaContext:
    """Tudo que o gerador de RELINT precisa de uma área FM."""

    nome: str
    fid: int
    poligono: BaseGeometry
    ocorrencias: gpd.GeoDataFrame
    denuncias: gpd.GeoDataFrame
    fatores: gpd.GeoDataFrame
    cameras: gpd.GeoDataFrame
    dominios: gpd.GeoDataFrame
    relint_referencia: str | None = field(default=None)

    def resumo(self) -> dict[str, int]:
        return {
            "ocorrencias": len(self.ocorrencias),
            "denuncias": len(self.denuncias),
            "fatores": len(self.fatores),
            "cameras": len(self.cameras),
            "dominios_intersectados": len(self.dominios),
        }


def _get_area_row(area_nome: str) -> gpd.GeoSeries:
    areas = data_loaders.load_areas_fm()
    match = areas[areas["nome_area"].str.strip() == area_nome.strip()]
    if match.empty:
        nomes = sorted(areas["nome_area"].unique())
        raise ValueError(
            f"Área {area_nome!r} não encontrada no shapefile. Áreas disponíveis:\n"
            + "\n".join(f"  - {n}" for n in nomes)
        )
    return match.iloc[0]


def _clip(gdf: gpd.GeoDataFrame, polygon: BaseGeometry) -> gpd.GeoDataFrame:
    """Pontos dentro do polígono (ou interseção com geometrias maiores)."""
    if gdf.empty:
        return gdf
    return gdf[gdf.geometry.intersects(polygon)].copy()


def filter_by_area(area_nome: str, *, com_referencia: bool = True) -> AreaContext:
    """Recorta todas as fontes para a área FM informada."""
    row = _get_area_row(area_nome)
    polygon = row.geometry

    ctx = AreaContext(
        nome=row["nome_area"],
        fid=int(row["fid"]) if "fid" in row else -1,
        poligono=polygon,
        ocorrencias=_clip(data_loaders.load_ocorrencias(), polygon),
        denuncias=_clip(data_loaders.load_denuncias(), polygon),
        fatores=_clip(data_loaders.load_fatores_urbanos(), polygon),
        cameras=_clip(data_loaders.load_cameras(), polygon),
        dominios=_clip(data_loaders.load_dominio_territorial(), polygon),
    )

    if com_referencia:
        ctx.relint_referencia = data_loaders.load_relint_referencia(area_nome)

    return ctx


def list_areas() -> list[str]:
    """Nomes oficiais das áreas disponíveis."""
    return list(config.AREAS_FM_OFICIAIS.values())
