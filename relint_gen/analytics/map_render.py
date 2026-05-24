"""Renderiza um PNG do mapa da área FM com camadas sobrepostas.

Visual baseado no anexo do briefing CompStat (pág. 11) — polígono FM,
heatmap KDE de ocorrências em vermelho, câmeras como pontos verdes e
trechos críticos (bingos) como círculos laranja numerados.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np
from shapely.geometry.base import BaseGeometry

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402


def _polygon_xy(polygon: BaseGeometry) -> tuple[list[float], list[float]]:
    """Extrai (xs, ys) do exterior de um Polygon ou MultiPolygon."""
    if polygon.geom_type == "Polygon":
        xs, ys = polygon.exterior.xy
        return list(xs), list(ys)
    # MultiPolygon: concatena com NaN como break (matplotlib quebra a linha)
    xs: list[float] = []
    ys: list[float] = []
    for poly in polygon.geoms:
        ex, ey = poly.exterior.xy
        xs.extend(ex)
        ys.extend(ey)
        xs.append(float("nan"))
        ys.append(float("nan"))
    return xs, ys


def render_area_map_png(
    poligono: BaseGeometry,
    ocorrencias,
    cameras,
    bingos: list,
    output_path: str | Path,
    *,
    titulo: str = "",
    subtitulo: str = "",
) -> str:
    """Renderiza o mapa da área e devolve o path do PNG."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(11, 8), dpi=130, facecolor="white")

    # Polígono da área FM
    xs, ys = _polygon_xy(poligono)
    ax.fill(xs, ys, color="#1F3A5F", alpha=0.06, zorder=1)
    ax.plot(xs, ys, color="#1F3A5F", linewidth=2.2, zorder=2,
            label="Polígono FM")

    # Heatmap KDE das ocorrências
    if len(ocorrencias) > 5:
        lons = ocorrencias.geometry.x.values
        lats = ocorrencias.geometry.y.values
        try:
            from scipy.stats import gaussian_kde

            lon_min, lon_max = lons.min(), lons.max()
            lat_min, lat_max = lats.min(), lats.max()
            xgrid, ygrid = np.mgrid[
                lon_min:lon_max:120j, lat_min:lat_max:120j
            ]
            positions = np.vstack([xgrid.ravel(), ygrid.ravel()])
            values = np.vstack([lons, lats])
            kernel = gaussian_kde(values, bw_method=0.20)
            density = np.reshape(kernel(positions).T, xgrid.shape)
            ax.contourf(
                xgrid, ygrid, density, levels=18,
                cmap="Reds", alpha=0.55, zorder=3,
            )
        except Exception:
            ax.scatter(lons, lats, c="#c0392b", s=4, alpha=0.30, zorder=3)
    elif len(ocorrencias) > 0:
        ax.scatter(ocorrencias.geometry.x, ocorrencias.geometry.y,
                   c="#c0392b", s=10, alpha=0.6, zorder=3)

    # Câmeras
    if len(cameras) > 0:
        ax.scatter(cameras.geometry.x, cameras.geometry.y,
                   c="#27ae60", s=14, alpha=0.85, zorder=5,
                   edgecolors="white", linewidths=0.4)

    # Bingos (numerados)
    if bingos:
        bx = [b.centro_lon for b in bingos]
        by = [b.centro_lat for b in bingos]
        bs = [120 + b.camadas * 60 for b in bingos]
        ax.scatter(bx, by, s=bs, color="#E67E22", alpha=0.65,
                   edgecolors="#5D2A00", linewidths=1.4, zorder=6)
        for i, (x, y) in enumerate(zip(bx, by), start=1):
            ax.annotate(str(i), (x, y), ha="center", va="center",
                        fontsize=9, fontweight="bold", color="white",
                        zorder=7)

    # Legenda manual
    handles = [
        Patch(facecolor="#1F3A5F", alpha=0.08, edgecolor="#1F3A5F",
              linewidth=2, label="Polígono FM"),
        Patch(facecolor="#c0392b", alpha=0.55, label="Densidade de ocorrências"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#27ae60",
               markersize=8, label="Câmeras (CIVITAS)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#E67E22",
               markeredgecolor="#5D2A00", markersize=12,
               label="Trechos críticos"),
    ]
    ax.legend(handles=handles, loc="lower right", framealpha=0.95,
              fontsize=9, edgecolor="#1F3A5F")

    # Limites com pequena margem
    margem = 0.003
    ax.set_xlim(min(xs) - margem, max(xs) + margem)
    ax.set_ylim(min(ys) - margem, max(ys) + margem)
    ax.set_aspect("equal")
    ax.set_axis_off()

    if titulo:
        fig.suptitle(titulo, fontsize=13, fontweight="bold", color="#1F3A5F",
                     y=0.97)
    if subtitulo:
        ax.set_title(subtitulo, fontsize=10, color="#444", pad=6)

    fig.tight_layout()
    fig.savefig(output_path, dpi=130, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(output_path)
