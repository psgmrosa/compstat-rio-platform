"""Extrai a estrutura de um RELINT existente em forma de JSON.

Útil para (a) ver como o renderer mapeia o conteúdo e (b) alimentar few-shot
no prompt do Claude. Roda assim:

    python -m scripts.extract_template --in relints/Cópia\\ de\\ RI_017_*.docx
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from docx import Document

from relint_gen import config

# Cabeçalhos fixos no template do CompStat (variantes encontradas nos arquivos).
HEADER_LINES = {
    "RELATÓRIO DE INTELIGÊNCIA DE ÁREA – COMPSTAT – DADOS PÚBLICOS",
    "RELATÓRIO DE INTELIGÊNCIA DE ÁREA",
    "Subsídio para Reunião de CompStat",
}
HEADER_PREFIXES = ("RELATÓRIO DE INTELIGÊNCIA",)
BULLET_PREFIX = ("•", "●", "*")
SEPARADOR_FATOR = re.compile(r"\s+—\s+|\s+–\s+|\s+-\s+")


def _iter_paragraphs_in_order(doc) -> list[str]:
    """Devolve o texto de todos os parágrafos do .docx em ordem do documento,
    incluindo os que estão dentro de células de tabela.

    O conteúdo dos RELINTs é distribuído entre parágrafos top-level e tabelas,
    então caminhamos pela árvore XML para preservar a ordem.
    """
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    out: list[str] = []
    for p in doc.element.body.iter(f"{ns}p"):
        text = "".join(t.text or "" for t in p.iter(f"{ns}t"))
        text = text.strip()
        if text:
            out.append(text)
    return out


def parse_relint_docx(path: Path) -> dict:
    doc = Document(str(path))
    paragraphs = _iter_paragraphs_in_order(doc)

    # 1. pula cabeçalhos fixos (linhas exatas + prefixos conhecidos)
    body = [
        p for p in paragraphs
        if p not in HEADER_LINES and not p.startswith(HEADER_PREFIXES)
        and p != "Subsídio para Reunião de CompStat"
    ]
    if not body:
        raise ValueError(f"{path}: nenhum conteúdo após cabeçalhos.")

    # 2. primeira linha = nome da área, segunda = intro
    area_nome = body[0]
    intro = body[1] if len(body) > 1 else ""
    body = body[2:]

    # 3. separa em blocos delimitados por linhas curtas em CAIXA ALTA (títulos)
    subareas: list[dict] = []
    current: dict | None = None
    conclusao_lines: list[str] = []
    in_conclusao = False

    for line in body:
        is_heading = line == line.upper() and len(line.split()) <= 12

        if is_heading and line.startswith("CONCLUS"):
            if current:
                subareas.append(current)
                current = None
            in_conclusao = True
            continue

        if in_conclusao:
            conclusao_lines.append(line)
            continue

        if is_heading:
            if current:
                subareas.append(current)
            current = {"nome": line, "descricao": "", "fatores": [], "dinamica": ""}
            continue

        if current is None:
            # texto antes do primeiro heading — anexa à intro
            intro = (intro + "\n" + line).strip()
            continue

        # bullet?
        if line.startswith(BULLET_PREFIX):
            bullet = line.lstrip("•●* ").strip().rstrip(";")
            partes = SEPARADOR_FATOR.split(bullet, maxsplit=1)
            if len(partes) == 2:
                current["fatores"].append(
                    {"categoria": partes[0].strip(), "descricao": partes[1].strip()}
                )
            else:
                current["fatores"].append({"categoria": bullet, "descricao": ""})
        elif line.startswith("Também foram identificados"):
            continue  # rótulo do bloco de fatores
        else:
            # parágrafo livre — primeiro = descrição, último = dinâmica
            if not current["descricao"]:
                current["descricao"] = line
            else:
                current["dinamica"] = line

    if current:
        subareas.append(current)

    # 4. processa conclusão
    conclusao = _parse_conclusao(conclusao_lines)

    return {
        "area_nome": area_nome,
        "intro": intro,
        "subareas": subareas,
        "conclusao": conclusao,
        "_meta": {"source": path.name},
    }


def _parse_conclusao(lines: list[str]) -> dict:
    sintese_parts: list[str] = []
    recomendacoes: list[dict] = []
    timing = ""
    em_recs = False

    for line in lines:
        if line.lower().startswith("observa-se necessidade"):
            em_recs = True
            continue
        if line.startswith(BULLET_PREFIX):
            bullet = line.lstrip("•●* ").strip().rstrip(";")
            partes = SEPARADOR_FATOR.split(bullet, maxsplit=1)
            if len(partes) == 2:
                recomendacoes.append(
                    {"categoria": partes[0].strip(), "descricao": partes[1].strip()}
                )
            else:
                recomendacoes.append({"categoria": bullet, "descricao": ""})
        elif em_recs:
            timing = (timing + "\n" + line).strip()
        else:
            sintese_parts.append(line)

    return {
        "sintese": "\n".join(sintese_parts).strip(),
        "recomendacoes": recomendacoes,
        "timing": timing,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Extrai estrutura de um RELINT.")
    parser.add_argument(
        "--in", dest="input", type=Path,
        default=config.RELINTS_DIR / "Cópia de RI_017_2026_Presidente_Vargas_Campo_Santana.docx",
        help="Caminho do .docx de origem.",
    )
    parser.add_argument(
        "--out", dest="output", type=Path,
        help="Caminho do JSON de saída (default: stdout).",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Processa todos os RELINTs em relints/ e salva em templates/.",
    )
    args = parser.parse_args()

    if args.all:
        config.TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        for docx_path in sorted(config.RELINTS_DIR.glob("*.docx")):
            parsed = parse_relint_docx(docx_path)
            out = config.TEMPLATES_DIR / (docx_path.stem + ".json")
            out.write_text(json.dumps(parsed, ensure_ascii=False, indent=2))
            print(f"✓ {docx_path.name} → {out.relative_to(config.ROOT)}")
        return 0

    parsed = parse_relint_docx(args.input)
    rendered = json.dumps(parsed, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
        print(f"✓ {args.input.name} → {args.output}")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
