"""Análise temporal — heatmap dia da semana × hora + identificação de picos."""

from __future__ import annotations

from dataclasses import dataclass

import geopandas as gpd
import numpy as np
import pandas as pd


DIAS_PT = ["Domingo", "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"]


@dataclass
class TemporalResult:
    heatmap: list[list[int]]              # 7 × 24
    periodo_predominante: str
    dia_horario_critico: str
    descricao: str
    total: int
    pico_hora: int
    pico_dia: int                          # 0=Dom


def _dow_from_string(s: str | float) -> int | None:
    if not isinstance(s, str):
        return None
    s = s.strip().lower()
    mapa = {
        "domingo": 0, "dom": 0,
        "segunda": 1, "seg": 1, "segunda-feira": 1,
        "terça": 2, "ter": 2, "terca": 2, "terça-feira": 2, "terca-feira": 2,
        "quarta": 3, "qua": 3, "quarta-feira": 3,
        "quinta": 4, "qui": 4, "quinta-feira": 4,
        "sexta": 5, "sex": 5, "sexta-feira": 5,
        "sábado": 6, "sab": 6, "sabado": 6,
    }
    return mapa.get(s)


def heatmap_temporal(ocorrencias: gpd.GeoDataFrame) -> TemporalResult:
    """Constrói o heatmap 7×24 a partir das ocorrências filtradas pela área."""
    if ocorrencias.empty:
        return TemporalResult(
            heatmap=[[0] * 24 for _ in range(7)],
            periodo_predominante="Sem dados suficientes",
            dia_horario_critico="N/A",
            descricao="Nenhuma ocorrência georreferenciada no perímetro.",
            total=0, pico_hora=0, pico_dia=0,
        )

    df = ocorrencias.copy()
    # `dia_semana` no schema vem como string em PT-BR.
    dia = df.get("dia_semana", pd.Series([None] * len(df))).map(_dow_from_string)
    hora = pd.to_numeric(df.get("hora"), errors="coerce")

    matriz = np.zeros((7, 24), dtype=int)
    for d, h in zip(dia, hora):
        if d is None or pd.isna(h):
            continue
        h_int = int(h)
        if 0 <= h_int < 24 and 0 <= d < 7:
            matriz[d][h_int] += 1

    total = int(matriz.sum())
    if total == 0:
        # fallback: pelo menos distribui por hora (sem dia da semana).
        hist_hora = hora.dropna().astype(int)
        for h in hist_hora:
            if 0 <= h < 24:
                matriz[1:, h] += 1  # distribui pelos dias úteis
        total = int(matriz.sum())

    # Picos
    soma_hora = matriz.sum(axis=0)
    soma_dia = matriz.sum(axis=1)
    pico_hora = int(np.argmax(soma_hora))
    pico_dia = int(np.argmax(soma_dia))

    # Período predominante (manhã 6-11, tarde 12-17, noite 18-23, madrugada 0-5)
    blocos = {
        "Madrugada (00h-05h)": int(soma_hora[0:6].sum()),
        "Manhã (06h-11h)": int(soma_hora[6:12].sum()),
        "Tarde (12h-17h)": int(soma_hora[12:18].sum()),
        "Noite (18h-23h)": int(soma_hora[18:24].sum()),
    }
    predominante = max(blocos, key=blocos.get)

    return TemporalResult(
        heatmap=matriz.tolist(),
        periodo_predominante=f"{predominante} — pico às {pico_hora:02d}h",
        dia_horario_critico=f"{DIAS_PT[pico_dia]}, {pico_hora:02d}h-{(pico_hora+1)%24:02d}h",
        descricao=(
            f"{total:,} ocorrências distribuídas; ".replace(",", ".")
            + f"pico no bloco {predominante.lower()}, "
            + f"com maior incidência às {DIAS_PT[pico_dia].lower()}s "
            + f"entre {pico_hora:02d}h e {(pico_hora+1)%24:02d}h."
        ),
        total=total,
        pico_hora=pico_hora,
        pico_dia=pico_dia,
    )


def heatmap_png(heatmap: list[list[int]], output_path: str,
                titulo: str = "Ocorrências por dia da semana × hora") -> str:
    """Gera PNG do heatmap pra embedar no .docx."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    arr = np.array(heatmap)
    fig, ax = plt.subplots(figsize=(11, 4))
    im = ax.imshow(arr, aspect="auto", cmap="Reds")
    ax.set_xticks(range(24))
    ax.set_xticklabels([f"{h:02d}" for h in range(24)], fontsize=8)
    ax.set_yticks(range(7))
    ax.set_yticklabels(DIAS_PT, fontsize=9)
    ax.set_xlabel("Hora do dia")
    ax.set_title(titulo, fontsize=11, fontweight="bold")
    fig.colorbar(im, ax=ax, shrink=0.7)
    for d in range(7):
        for h in range(24):
            v = arr[d, h]
            if v > 0:
                ax.text(h, d, str(int(v)), ha="center", va="center",
                        color="black" if v < arr.max() * 0.6 else "white",
                        fontsize=7)
    fig.tight_layout()
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return output_path
