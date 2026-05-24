"""Renderiza o Relatório Analítico de Área em PDF.

Layout casa visualmente com o anexo do briefing CompStat (págs. 11-16):
cabeçalho azul, tabelas estilizadas, cover com mapa, seções na ordem
oficial. Usa reportlab platypus (alto nível) para garantir paginação
correta com tabelas longas.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .template import RelatorioAnalitico


# --- paleta (mesma cor do anexo do briefing) -------------------------------
COR_HEADER = colors.HexColor("#1F3A5F")        # azul escuro do briefing
COR_HEADER_LIGHT = colors.HexColor("#E5EBF3")  # azul claro fundo
COR_HIGHLIGHT = colors.HexColor("#1F3A5F")     # destaque
COR_TEXTO = colors.HexColor("#1A1A1A")
COR_RISCO_ALTO = colors.HexColor("#B22222")
COR_RISCO_MED = colors.HexColor("#E67E22")
COR_RISCO_BAIXO = colors.HexColor("#27AE60")
COR_LINHA = colors.HexColor("#BDC3C7")
COR_LINHA_LIGHT = colors.HexColor("#ECF0F1")
COR_BG_ZEBRA = colors.HexColor("#F7F9FB")


# --- estilos de parágrafo ---------------------------------------------------

def _make_styles() -> dict[str, ParagraphStyle]:
    return {
        "TitleHero": ParagraphStyle(
            "TitleHero", fontName="Helvetica-Bold", fontSize=22,
            leading=26, alignment=TA_CENTER, textColor=colors.white,
            spaceAfter=2,
        ),
        "TitleHeroSub": ParagraphStyle(
            "TitleHeroSub", fontName="Helvetica-Oblique", fontSize=11,
            leading=14, alignment=TA_CENTER, textColor=colors.white,
        ),
        "SectionHeader": ParagraphStyle(
            "SectionHeader", fontName="Helvetica-Bold", fontSize=13,
            leading=16, alignment=TA_LEFT, textColor=COR_HEADER,
            spaceBefore=10, spaceAfter=6,
        ),
        "SubHeader": ParagraphStyle(
            "SubHeader", fontName="Helvetica-Bold", fontSize=11,
            leading=14, alignment=TA_LEFT, textColor=COR_HEADER,
            spaceBefore=8, spaceAfter=4,
        ),
        "Body": ParagraphStyle(
            "Body", fontName="Helvetica", fontSize=10, leading=13,
            alignment=TA_JUSTIFY, textColor=COR_TEXTO,
            spaceAfter=4,
        ),
        "BodySmall": ParagraphStyle(
            "BodySmall", fontName="Helvetica", fontSize=9, leading=12,
            alignment=TA_JUSTIFY, textColor=COR_TEXTO,
        ),
        "Caption": ParagraphStyle(
            "Caption", fontName="Helvetica-Oblique", fontSize=8,
            leading=10, alignment=TA_LEFT, textColor=colors.HexColor("#666"),
            spaceAfter=2,
        ),
        "CellHeader": ParagraphStyle(
            "CellHeader", fontName="Helvetica-Bold", fontSize=9,
            leading=11, alignment=TA_CENTER, textColor=colors.white,
        ),
        "CellLabel": ParagraphStyle(
            "CellLabel", fontName="Helvetica-Bold", fontSize=9,
            leading=11, alignment=TA_LEFT, textColor=colors.white,
        ),
        "Cell": ParagraphStyle(
            "Cell", fontName="Helvetica", fontSize=9, leading=11,
            alignment=TA_LEFT, textColor=COR_TEXTO,
        ),
        "CellCenter": ParagraphStyle(
            "CellCenter", fontName="Helvetica", fontSize=9, leading=11,
            alignment=TA_CENTER, textColor=COR_TEXTO,
        ),
        "CellBold": ParagraphStyle(
            "CellBold", fontName="Helvetica-Bold", fontSize=9, leading=11,
            alignment=TA_LEFT, textColor=COR_HEADER,
        ),
    }


# --- helpers de layout ------------------------------------------------------

def _header_footer(canvas, doc) -> None:
    """Linha de cabeçalho e rodapé em todas as páginas (exceto cover)."""
    canvas.saveState()
    largura, altura = A4
    # cabeçalho
    canvas.setFillColor(COR_HEADER_LIGHT)
    canvas.rect(0, altura - 1.2 * cm, largura, 1.2 * cm, fill=1, stroke=0)
    canvas.setFillColor(COR_HEADER)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(1.5 * cm, altura - 0.75 * cm,
                      "CompStat Municipal · Prefeitura do Rio de Janeiro")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(largura - 1.5 * cm, altura - 0.75 * cm,
                           "Relatório Analítico de Área")
    # rodapé
    canvas.setFillColor(colors.HexColor("#888"))
    canvas.setFont("Helvetica", 8)
    canvas.drawString(1.5 * cm, 0.8 * cm,
                      "Subsídio para Reunião de CompStat")
    canvas.drawRightString(largura - 1.5 * cm, 0.8 * cm,
                           f"pág. {doc.page}")
    canvas.setStrokeColor(COR_LINHA)
    canvas.setLineWidth(0.5)
    canvas.line(1.5 * cm, 1.1 * cm, largura - 1.5 * cm, 1.1 * cm)
    canvas.restoreState()


def _cover_canvas(canvas, doc) -> None:
    """Cabeçalho colorido na cover."""
    canvas.saveState()
    largura, altura = A4
    canvas.setFillColor(COR_HEADER)
    canvas.rect(0, altura - 3.8 * cm, largura, 3.8 * cm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 24)
    canvas.drawCentredString(largura / 2, altura - 1.8 * cm,
                             "RELATÓRIO ANALÍTICO DE ÁREA")
    canvas.setFont("Helvetica-Oblique", 12)
    canvas.drawCentredString(largura / 2, altura - 2.7 * cm,
                             "Subsídio para Reunião de CompStat")
    canvas.setFont("Helvetica", 9)
    canvas.drawCentredString(largura / 2, altura - 3.3 * cm,
                             "CompStat Municipal · Prefeitura do Rio de Janeiro")
    # rodapé na cover
    canvas.setFillColor(colors.HexColor("#888"))
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(largura - 1.5 * cm, 0.8 * cm, f"pág. {doc.page}")
    canvas.restoreState()


def _header_callback(rel: RelatorioAnalitico):
    def _cb(canvas, doc):
        if doc.page == 1:
            _cover_canvas(canvas, doc)
        else:
            _header_footer(canvas, doc)
    return _cb


# --- estilos de tabela ------------------------------------------------------

def _style_header_row(start_col: int = 0, end_col: int = -1):
    return [
        ("BACKGROUND", (start_col, 0), (end_col, 0), COR_HEADER),
        ("TEXTCOLOR", (start_col, 0), (end_col, 0), colors.white),
        ("FONTNAME", (start_col, 0), (end_col, 0), "Helvetica-Bold"),
        ("FONTSIZE", (start_col, 0), (end_col, 0), 9),
        ("ALIGN", (start_col, 0), (end_col, 0), "CENTER"),
        ("VALIGN", (start_col, 0), (end_col, 0), "MIDDLE"),
        ("BOTTOMPADDING", (start_col, 0), (end_col, 0), 6),
        ("TOPPADDING", (start_col, 0), (end_col, 0), 6),
    ]


def _style_grid():
    return [
        ("GRID", (0, 0), (-1, -1), 0.4, COR_LINHA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
    ]


def _zebra(start_row: int, n_rows: int):
    """Zebra striping (linhas alternadas) a partir de start_row."""
    out = []
    for i in range(start_row, start_row + n_rows):
        if (i - start_row) % 2 == 1:
            out.append(("BACKGROUND", (0, i), (-1, i), COR_BG_ZEBRA))
    return out


# --- seções -----------------------------------------------------------------

def _build_cover(rel: RelatorioAnalitico, styles) -> list:
    flow = [Spacer(1, 3.5 * cm)]

    # Tabela área + período
    periodo = rel.indicadores.periodo or "—"
    data = [
        [
            Paragraph("<b>Área de análise</b>", styles["CellHeader"]),
            Paragraph("<b>Período de análise</b>", styles["CellHeader"]),
        ],
        [
            Paragraph(f"<b>{rel.identificacao.area_fm}</b>", styles["Cell"]),
            Paragraph(
                f"<b>Dados criminais:</b> {periodo}<br/>"
                f"<b>Fatores ambientais e dinâmica do crime:</b> "
                "atualização contínua",
                styles["Cell"],
            ),
        ],
    ]
    table = Table(data, colWidths=[9 * cm, 9 * cm])
    table.setStyle(TableStyle(_style_header_row() + _style_grid()))
    flow.append(table)
    flow.append(Spacer(1, 0.6 * cm))

    # Subtítulo do mapa
    n_oc = rel.indicadores.total
    subtitulo = (
        f"<b>Mapa de segmentos quentes na área:</b> "
        f"{rel.identificacao.area_fm} "
        f"<i>(total de ocorrências: {n_oc:,}, {periodo})</i>"
    ).replace(",", ".")
    flow.append(Paragraph(subtitulo, styles["BodySmall"]))
    flow.append(Spacer(1, 0.2 * cm))

    # Mapa
    if rel.metadados.get("mapa_png"):
        try:
            img = Image(rel.metadados["mapa_png"], width=18 * cm, height=12 * cm)
            img.hAlign = "CENTER"
            flow.append(img)
        except Exception:
            flow.append(Paragraph("(mapa não disponível)", styles["Caption"]))

    return flow


def _build_resumo_executivo(rel: RelatorioAnalitico, styles) -> list:
    flow = [Paragraph("RESUMO EXECUTIVO", styles["SectionHeader"])]
    flow.append(Paragraph(
        "Síntese gerada automaticamente pela plataforma, respondendo às "
        "quatro perguntas norteadoras da reunião de CompStat. Diagnósticos "
        "ancorados nos dados de ocorrências, Disque Denúncia, RELINTs e "
        "fatores urbanos georreferenciados.",
        styles["Body"],
    ))

    perguntas = rel.resumo_executivo.perguntas or []
    if not perguntas:
        flow.append(Paragraph("(sem perguntas norteadoras)", styles["Caption"]))
        return flow

    data = [[
        Paragraph("Perguntas norteadoras", styles["CellHeader"]),
        Paragraph("Diagnóstico com base nos dados", styles["CellHeader"]),
        Paragraph("Operação FM / órgãos complementares", styles["CellHeader"]),
        Paragraph("Observações / sugestão de ajuste (COMPSTAT)",
                  styles["CellHeader"]),
    ]]
    for q in perguntas:
        data.append([
            Paragraph(f"<b>{q.pergunta}</b>", styles["Cell"]),
            Paragraph(q.diagnostico, styles["Cell"]),
            Paragraph(q.operacao_sugerida, styles["Cell"]),
            Paragraph(q.observacao or "—", styles["Cell"]),
        ])
    table = Table(data, colWidths=[4.5 * cm, 5.5 * cm, 4.5 * cm, 3.5 * cm],
                  repeatRows=1)
    style = _style_header_row() + _style_grid() + _zebra(1, len(perguntas))
    table.setStyle(TableStyle(style))
    flow.append(table)
    return flow


def _build_secao_1(rel: RelatorioAnalitico, styles) -> list:
    flow = [Paragraph("1. OCORRÊNCIAS CRIMINAIS", styles["SectionHeader"])]

    # 1a. Identificação da área (tabela 2 colunas duplas)
    flow.append(Paragraph("Identificação da área", styles["SubHeader"]))
    ident = rel.identificacao
    pares = [
        ("Área FM", ident.area_fm,
         "Nº de trechos críticos", str(ident.num_trechos_criticos)),
        ("AISP", ident.aisp or "—", "Base FM", ident.base_fm or "—"),
        ("Bairros", ident.bairros or "—",
         "Subprefeitura", ident.subprefeitura or "—"),
        ("DP", ident.dp or "—", "BPM", ident.bpm or "—"),
        ("Área sob influência de ORCRIM",
         ident.influencia_orcrim or "—", "", ""),
    ]
    data = []
    for l1, v1, l2, v2 in pares:
        data.append([
            Paragraph(l1, styles["CellLabel"]),
            Paragraph(v1, styles["Cell"]),
            Paragraph(l2, styles["CellLabel"]),
            Paragraph(v2, styles["Cell"]),
        ])
    t = Table(data, colWidths=[4.2 * cm, 5.0 * cm, 4.2 * cm, 4.6 * cm])
    style_t = [
        ("BACKGROUND", (0, 0), (0, -1), COR_HEADER),
        ("BACKGROUND", (2, 0), (2, -1), COR_HEADER),
        ("GRID", (0, 0), (-1, -1), 0.4, COR_LINHA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        # span para a última linha (ORCRIM ocupa 3 colunas à direita)
        ("SPAN", (1, -1), (3, -1)),
    ]
    t.setStyle(TableStyle(style_t))
    flow.append(t)
    flow.append(Spacer(1, 0.3 * cm))

    # 1b. Indicadores do período (6 colunas)
    flow.append(Paragraph("Indicadores do período", styles["SubHeader"]))
    ind = rel.indicadores
    data = [
        [
            Paragraph("Período", styles["CellHeader"]),
            Paragraph("Roubos", styles["CellHeader"]),
            Paragraph("Furtos", styles["CellHeader"]),
            Paragraph("Total", styles["CellHeader"]),
            Paragraph("Ranking (% áreas FM)", styles["CellHeader"]),
            Paragraph("Variação", styles["CellHeader"]),
        ],
        [
            Paragraph(ind.periodo, styles["CellCenter"]),
            Paragraph(f"{ind.roubos:,}".replace(",", "."), styles["CellCenter"]),
            Paragraph(f"{ind.furtos:,}".replace(",", "."), styles["CellCenter"]),
            Paragraph(f"{ind.total:,}".replace(",", "."), styles["CellCenter"]),
            Paragraph(ind.ranking_areas_fm, styles["CellCenter"]),
            Paragraph(ind.variacao_periodo_anterior or "N/A",
                      styles["CellCenter"]),
        ],
    ]
    t = Table(data, colWidths=[3.6 * cm, 1.9 * cm, 1.9 * cm,
                                2.0 * cm, 4.4 * cm, 4.2 * cm])
    t.setStyle(TableStyle(_style_header_row() + _style_grid()))
    flow.append(t)
    flow.append(Spacer(1, 0.3 * cm))

    # 1c. Distribuição por tipo
    if rel.distribuicao:
        flow.append(
            Paragraph("Distribuição de ocorrências por tipo",
                      styles["SubHeader"])
        )
        data = [[
            Paragraph("Ranking", styles["CellHeader"]),
            Paragraph("Tipo de ocorrência", styles["CellHeader"]),
            Paragraph("Quantidade", styles["CellHeader"]),
            Paragraph("% do total", styles["CellHeader"]),
        ]]
        for d in rel.distribuicao:
            data.append([
                Paragraph(f"{d.ranking}º", styles["CellCenter"]),
                Paragraph(d.tipo, styles["Cell"]),
                Paragraph(f"{d.quantidade:,}".replace(",", "."),
                          styles["CellCenter"]),
                Paragraph(f"{d.pct:.1f}%", styles["CellCenter"]),
            ])
        t = Table(data, colWidths=[2.0 * cm, 9.6 * cm, 3.2 * cm, 3.2 * cm],
                  repeatRows=1)
        t.setStyle(TableStyle(_style_header_row() + _style_grid()
                              + _zebra(1, len(rel.distribuicao))))
        flow.append(t)
        flow.append(Spacer(1, 0.3 * cm))

    # 1d. Análise temporal — heatmap PNG + tabela resumo
    flow.append(Paragraph("Análise temporal", styles["SubHeader"]))
    flow.append(Paragraph(
        "Distribuição de ocorrências por dia da semana × hora do dia.",
        styles["Caption"],
    ))
    if rel.heatmap_image:
        try:
            img = Image(rel.heatmap_image, width=18 * cm, height=6.5 * cm)
            img.hAlign = "CENTER"
            flow.append(img)
        except Exception:
            pass
    data = [
        [Paragraph("Período Predominante", styles["CellLabel"]),
         Paragraph(rel.temporal.periodo_predominante, styles["Cell"]),
         Paragraph("Dia / Horário Crítico", styles["CellLabel"]),
         Paragraph(rel.temporal.dia_horario_critico, styles["Cell"])],
        [Paragraph("Descrição", styles["CellLabel"]),
         Paragraph(rel.temporal.descricao or "—", styles["Cell"]),
         "", ""],
    ]
    t = Table(data, colWidths=[4.0 * cm, 5.2 * cm, 4.0 * cm, 4.8 * cm])
    style = [
        ("BACKGROUND", (0, 0), (0, -1), COR_HEADER),
        ("BACKGROUND", (2, 0), (2, 0), COR_HEADER),
        ("GRID", (0, 0), (-1, -1), 0.4, COR_LINHA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("SPAN", (1, 1), (3, 1)),
    ]
    t.setStyle(TableStyle(style))
    flow.append(t)
    return flow


def _build_secao_2(rel: RelatorioAnalitico, styles) -> list:
    flow = [Paragraph("2. DINÂMICA CRIMINAL", styles["SectionHeader"])]
    flow.append(Paragraph(
        f"<i>Fonte: {rel.dinamica.fonte}</i>", styles["Caption"],
    ))

    # Tabela vertical com 1 coluna de label + 1 de conteúdo
    data = [
        [Paragraph("Síntese da dinâmica", styles["CellLabel"]),
         Paragraph(rel.dinamica.sintese, styles["Cell"])],
    ]
    if rel.dinamica.modalidade:
        data.append([
            Paragraph("Modalidade", styles["CellLabel"]),
            Paragraph(", ".join(rel.dinamica.modalidade), styles["Cell"]),
        ])
    if rel.dinamica.rotas_fuga:
        data.append([
            Paragraph("Rotas de fuga e escoamento", styles["CellLabel"]),
            Paragraph("; ".join(rel.dinamica.rotas_fuga), styles["Cell"]),
        ])
    if rel.dinamica.pontos_receptacao:
        data.append([
            Paragraph("Pontos de receptação", styles["CellLabel"]),
            Paragraph("; ".join(rel.dinamica.pontos_receptacao), styles["Cell"]),
        ])
    if rel.dinamica.perfil_suspeitos:
        data.append([
            Paragraph("Perfil de suspeitos", styles["CellLabel"]),
            Paragraph(rel.dinamica.perfil_suspeitos, styles["Cell"]),
        ])

    t = Table(data, colWidths=[4.5 * cm, 13.5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), COR_HEADER),
        ("GRID", (0, 0), (-1, -1), 0.4, COR_LINHA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    flow.append(t)
    return flow


def _build_secao_3(rel: RelatorioAnalitico, styles) -> list:
    flow = [Paragraph("3. EFETIVO EMPREGADO — FORÇA MUNICIPAL",
                      styles["SectionHeader"])]
    e = rel.efetivo
    data = [[
        Paragraph("Campo", styles["CellHeader"]),
        Paragraph("Situação Atual", styles["CellHeader"]),
        Paragraph("Sugestão de Alteração", styles["CellHeader"]),
        Paragraph("Justificativa", styles["CellHeader"]),
    ]]
    linhas = [
        ("Nº de Agentes por Turno", e.agentes_por_turno,
         e.sugestao_agentes, e.justificativa),
        ("Locais de Cobertura", e.locais_cobertura, e.sugestao_locais, ""),
        ("Horário de Cobertura", e.horario_cobertura, e.sugestao_horario, ""),
        ("Dias de Cobertura", e.dias_cobertura, e.sugestao_dias, ""),
        ("Modalidade de Emprego", e.modalidade_emprego,
         e.sugestao_modalidade, ""),
    ]
    for campo, atual, sugestao, just in linhas:
        data.append([
            Paragraph(f"<b>{campo}</b>", styles["Cell"]),
            Paragraph(atual or "—", styles["Cell"]),
            Paragraph(sugestao or "—", styles["Cell"]),
            Paragraph(just or "—", styles["BodySmall"]),
        ])
    t = Table(data, colWidths=[4.0 * cm, 4.0 * cm, 5.5 * cm, 4.5 * cm],
              repeatRows=1)
    t.setStyle(TableStyle(_style_header_row() + _style_grid()
                          + _zebra(1, len(linhas))))
    flow.append(t)
    return flow


def _build_secao_4(rel: RelatorioAnalitico, styles) -> list:
    flow = [Paragraph("4. FATORES DE INCIDÊNCIA CRIMINAL",
                      styles["SectionHeader"])]
    flow.append(Paragraph(
        "Fatores urbanos mapeados no perímetro, com o órgão municipal "
        "responsável pela resolução.", styles["Caption"],
    ))

    if not rel.fatores:
        flow.append(Paragraph("Nenhum fator urbano relevante mapeado.",
                              styles["Body"]))
    else:
        data = [[
            Paragraph("Fator identificado", styles["CellHeader"]),
            Paragraph("Descrição", styles["CellHeader"]),
            Paragraph("Responsável", styles["CellHeader"]),
        ]]
        for f in rel.fatores:
            data.append([
                Paragraph(f"<b>{f.fator}</b>", styles["Cell"]),
                Paragraph(f.descricao, styles["Cell"]),
                Paragraph(f"<b>{f.responsavel}</b>", styles["CellCenter"]),
            ])
        t = Table(data, colWidths=[4.5 * cm, 10.5 * cm, 3.0 * cm],
                  repeatRows=1)
        t.setStyle(TableStyle(_style_header_row() + _style_grid()
                              + _zebra(1, len(rel.fatores))))
        flow.append(t)

    # Câmeras
    flow.append(Spacer(1, 0.4 * cm))
    flow.append(Paragraph("Câmeras identificadas na área", styles["SubHeader"]))
    data = [
        [Paragraph("Quantidade e descrição", styles["CellLabel"]),
         Paragraph(
             f"<b>Total: {rel.cameras_total} câmeras</b> "
             f"({rel.cameras_descricao or 'CIVITAS/COR'})",
             styles["Cell"])],
    ]
    t = Table(data, colWidths=[4.5 * cm, 13.5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), COR_HEADER),
        ("GRID", (0, 0), (-1, -1), 0.4, COR_LINHA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    flow.append(t)
    return flow


def _build_secao_5(rel: RelatorioAnalitico, styles) -> list:
    flow = [Paragraph("5. PLANO DE AÇÃO E RESPONSABILIZAÇÃO",
                      styles["SectionHeader"])]
    flow.append(Paragraph(
        "<i>Pré-populado pela IA a partir das coincidências (mancha × "
        "fator × dinâmica). Esta seção deve ser revisada e formalizada "
        "durante a reunião de CompStat.</i>", styles["Caption"],
    ))

    if not rel.plano_acao:
        flow.append(Paragraph("Sem ações sugeridas no momento.", styles["Body"]))
        return flow

    data = [[
        Paragraph("Ação acordada", styles["CellHeader"]),
        Paragraph("Responsável", styles["CellHeader"]),
        Paragraph("Prazo", styles["CellHeader"]),
        Paragraph("Status", styles["CellHeader"]),
    ]]
    for a in rel.plano_acao:
        data.append([
            Paragraph(a.acao, styles["Cell"]),
            Paragraph(f"<b>{a.responsavel}</b>", styles["CellCenter"]),
            Paragraph(a.prazo or "—", styles["CellCenter"]),
            Paragraph(a.status or "—", styles["CellCenter"]),
        ])
    t = Table(data, colWidths=[8.5 * cm, 3.5 * cm, 3.0 * cm, 3.0 * cm],
              repeatRows=1)
    t.setStyle(TableStyle(_style_header_row() + _style_grid()
                          + _zebra(1, len(rel.plano_acao))))
    flow.append(t)
    return flow


# --- entrypoint -------------------------------------------------------------

def render_relatorio_pdf(rel: RelatorioAnalitico, output_path: Path) -> Path:
    """Renderiza o Relatório Analítico em PDF e devolve o path."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    styles = _make_styles()
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        title=f"Relatório Analítico - {rel.identificacao.area_fm}",
        author="CompStat Rio · Plataforma de Inteligência Criminal",
    )

    story: list = []
    story.extend(_build_cover(rel, styles))
    story.append(PageBreak())
    story.extend(_build_resumo_executivo(rel, styles))
    story.append(PageBreak())
    story.extend(_build_secao_1(rel, styles))
    story.append(PageBreak())
    story.extend(_build_secao_2(rel, styles))
    story.append(Spacer(1, 0.3 * cm))
    story.extend(_build_secao_3(rel, styles))
    story.append(PageBreak())
    story.extend(_build_secao_4(rel, styles))
    story.append(Spacer(1, 0.3 * cm))
    story.extend(_build_secao_5(rel, styles))

    doc.build(story, onFirstPage=_header_callback(rel),
              onLaterPages=_header_callback(rel))
    return output_path
