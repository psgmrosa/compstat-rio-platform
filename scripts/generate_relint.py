"""CLI: gera o Relatório Analítico de Área para uma ou todas as áreas FM.

Exemplos:
    # Modo offline (sem chamar Claude) — usa payload determinístico
    python -m scripts.generate_relint --area "Jardim de Alah" --offline

    # Com Claude (precisa ANTHROPIC_API_KEY no .env)
    python -m scripts.generate_relint --area "Presidente Vargas - Campo de Santana - Central do Brasil - Cinelândia"

    # Todas as 8 áreas
    python -m scripts.generate_relint --all
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from relint_gen import config, filters, pipeline


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--area", help="Nome da área FM.")
    parser.add_argument(
        "--out-dir", type=Path, default=config.OUTPUT_DIR,
        help="Diretório de saída.",
    )
    parser.add_argument(
        "--offline", action="store_true",
        help="Não chama o Claude — usa payload determinístico (debug).",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Gera para todas as 8 áreas FM disponíveis.",
    )
    parser.add_argument(
        "--list", action="store_true", help="Lista áreas disponíveis e sai.",
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Salva o payload JSON do Claude ao lado do relatório.",
    )
    parser.add_argument(
        "--format", choices=["pdf", "docx", "ambos"], default="pdf",
        help="Formato de saída (default: pdf).",
    )
    args = parser.parse_args()

    if args.list:
        for a in filters.list_areas():
            print(a)
        return 0

    if args.all:
        ok, fail = [], []
        for a in filters.list_areas():
            try:
                out = pipeline.gerar_relatorio(
                    a, output_dir=args.out_dir,
                    usar_llm=not args.offline, salvar_debug=args.debug,
                    formato=args.format,
                )
                print(f"✓ {a} → {out}")
                ok.append(a)
            except Exception as exc:                  # noqa: BLE001
                print(f"✗ {a} → {exc}")
                fail.append((a, str(exc)))
        print(f"\n{len(ok)}/{len(ok) + len(fail)} relatórios gerados.")
        return 0 if not fail else 1

    if not args.area:
        parser.error("--area é obrigatório (ou use --all / --list).")

    out = pipeline.gerar_relatorio(
        args.area, output_dir=args.out_dir,
        usar_llm=not args.offline, salvar_debug=args.debug,
        formato=args.format,
    )
    print(f"✓ Relatório gerado: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
