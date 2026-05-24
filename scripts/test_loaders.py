"""Smoke test: carrega todos os datasets e mostra resumos.

    python -m scripts.test_loaders
"""

from __future__ import annotations

import sys
import time

from relint_gen import data_loaders, filters


def _timed(label: str, fn):
    t0 = time.perf_counter()
    result = fn()
    print(f"  {label}: {len(result):>7,} linhas   ({time.perf_counter() - t0:.2f}s)")
    return result


def main() -> int:
    print("# Carregando datasets")
    _timed("ocorrências        ", data_loaders.load_ocorrencias)
    _timed("denúncias          ", data_loaders.load_denuncias)
    _timed("fatores urbanos    ", data_loaders.load_fatores_urbanos)
    _timed("câmeras            ", data_loaders.load_cameras)
    _timed("áreas FM (polígonos)", data_loaders.load_areas_fm)
    _timed("domínio territorial", data_loaders.load_dominio_territorial)

    print("\n# Áreas disponíveis")
    for a in filters.list_areas():
        print(f"  - {a}")

    print("\n# Recortando 'Presidente Vargas - Campo de Santana - Central do Brasil - Cinelândia'")
    ctx = filters.filter_by_area(
        "Presidente Vargas - Campo de Santana - Central do Brasil - Cinelândia"
    )
    for k, v in ctx.resumo().items():
        print(f"  {k:<25} {v:>6,}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
