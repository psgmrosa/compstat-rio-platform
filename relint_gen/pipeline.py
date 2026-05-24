"""Orquestrador end-to-end.

Fluxo:

    1. filter_by_area(area_nome)           → AreaContext (geo-recortes)
    2. analytics.indicadores(...)          → IndicadoresResult
    3. analytics.temporal.heatmap_temporal → TemporalResult + PNG
    4. analytics.bingo.detectar_bingos     → list[BingoCell]
    5. analytics.optimizer.sugestao_area   → AlocacaoArea
    6. prompts.build_user_prompt           → string contextualizada
    7. llm.generate_relatorio_payload      → dict (tool_use do Claude)
    8. template.relatorio_from_dict        → RelatorioAnalitico
    9. template.render_relatorio           → .docx final
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from . import config, filters, llm, prompts, template
from .analytics import bingo as bingo_mod
from .analytics import indicadores as ind_mod
from .analytics import optimizer as opt_mod
from .analytics import temporal as temp_mod


def gerar_relatorio(
    area_nome: str,
    *,
    output_dir: Path | None = None,
    usar_llm: bool = True,
    salvar_debug: bool = False,
) -> Path:
    """Gera o Relatório Analítico para uma área FM e devolve o path do .docx."""
    output_dir = Path(output_dir or config.OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Recorte geográfico
    ctx = filters.filter_by_area(area_nome)

    # 2-5. Analytics
    indic = ind_mod.indicadores(ctx.ocorrencias, ctx.nome)
    temporal = temp_mod.heatmap_temporal(ctx.ocorrencias)
    bingos = bingo_mod.detectar_bingos(
        ctx.poligono, ctx.ocorrencias, ctx.denuncias, ctx.fatores,
    )
    plano_inicial = bingo_mod.bingos_para_plano_acao(bingos)
    alocacao = opt_mod.sugestao_para_area(ctx.nome)

    # PNG do heatmap (embedado no .docx)
    safe_name = "".join(c if c.isalnum() else "_" for c in ctx.nome)[:80]
    heatmap_png = output_dir / f"heatmap_{safe_name}.png"
    temp_mod.heatmap_png(temporal.heatmap, str(heatmap_png),
                         titulo=f"Ocorrências — {ctx.nome}")

    # 6-7. Claude
    if usar_llm:
        user_prompt = prompts.build_user_prompt(
            ctx, indic, temporal, bingos, alocacao, plano_inicial,
        )
        payload = llm.generate_relatorio_payload(
            prompts.SYSTEM_PROMPT, user_prompt,
        )
    else:
        payload = _payload_offline(ctx, indic, temporal, bingos,
                                   alocacao, plano_inicial)

    if salvar_debug:
        (output_dir / f"payload_{safe_name}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2)
        )

    # 8. Merge com analytics (números do data, texto da LLM)
    payload["indicadores"].update({
        "periodo": indic.periodo,
        "roubos": indic.roubos,
        "furtos": indic.furtos,
        "total": indic.total,
        "ranking_areas_fm": indic.ranking_str,
    })
    payload["distribuicao"] = [
        {"ranking": r, "tipo": tipo, "quantidade": qtd, "pct": round(pct, 2)}
        for r, tipo, qtd, pct in indic.distribuicao
    ] or payload.get("distribuicao", [])
    payload["temporal"].update({
        "periodo_predominante": temporal.periodo_predominante,
        "dia_horario_critico": temporal.dia_horario_critico,
    })

    rel = template.relatorio_from_dict(
        payload,
        heatmap=temporal.heatmap,
        heatmap_image=str(heatmap_png) if heatmap_png.exists() else None,
        cameras_total=len(ctx.cameras),
    )

    # 9. Render
    out_path = output_dir / f"RelatorioAnalitico_{safe_name}.docx"
    template.render_relatorio(rel, out_path)
    return out_path


def _payload_offline(ctx, indic, temporal, bingos, alocacao, plano) -> dict:
    """Payload mínimo para validar o pipeline sem chamar a API."""
    return {
        "identificacao": {
            "area_fm": ctx.nome,
            "aisp": "—",
            "bairros": "—",
            "dp": "—",
            "bpm": "—",
            "base_fm": "—",
            "subprefeitura": "—",
            "num_trechos_criticos": len(bingos),
            "influencia_orcrim": (
                "Áreas adjacentes sob influência de ORCRIM mapeadas no domínio territorial."
                if not ctx.dominios.empty else "Nenhuma área sob influência mapeada."
            ),
        },
        "indicadores": {
            "periodo": indic.periodo,
            "roubos": indic.roubos,
            "furtos": indic.furtos,
            "total": indic.total,
            "ranking_areas_fm": indic.ranking_str,
            "variacao_periodo_anterior": "N/A",
        },
        "distribuicao": [
            {"ranking": r, "tipo": t, "quantidade": q, "pct": round(p, 2)}
            for r, t, q, p in indic.distribuicao
        ],
        "temporal": {
            "periodo_predominante": temporal.periodo_predominante,
            "dia_horario_critico": temporal.dia_horario_critico,
            "descricao": temporal.descricao,
        },
        "dinamica": {
            "sintese": (
                "[Síntese qualitativa não gerada — modo offline]. "
                f"Foram observadas {len(ctx.denuncias)} denúncias e "
                f"{len(ctx.fatores)} fatores urbanos no perímetro."
            ),
            "modalidade": [], "rotas_fuga": [],
            "pontos_receptacao": [], "perfil_suspeitos": "—",
        },
        "efetivo": {
            "agentes_por_turno": "—",
            "locais_cobertura": "—",
            "horario_cobertura": "—",
            "dias_cobertura": "—",
            "modalidade_emprego": "—",
            "sugestao_agentes": (
                f"{alocacao.agentes} agentes" if alocacao else "—"
            ),
            "sugestao_locais": "ver bingos no plano de ação",
            "sugestao_horario": temporal.periodo_predominante,
            "sugestao_dias": temporal.dia_horario_critico,
            "sugestao_modalidade": (
                alocacao.modalidade_sugerida if alocacao else "—"
            ),
            "justificativa": (
                f"Alocação baseada em {alocacao.pct_risco}% do risco total."
                if alocacao else "—"
            ),
        },
        "fatores": _fatores_top(ctx),
        "plano_acao": plano[:8] or [
            {"acao": "Sem coincidências relevantes detectadas no perímetro.",
             "responsavel": "—", "prazo": "—", "status": "—"}
        ],
        "resumo_executivo": {
            "perguntas": [
                {
                    "pergunta": "Os locais de maior incidência coincidem com a rota da FM?",
                    "diagnostico": f"{len(bingos)} trechos críticos detectados; ver mapa.",
                    "operacao_sugerida": "Direcionar patrulhamento aos pontos de score alto.",
                    "observacao": "",
                },
                {
                    "pergunta": "O horário de maior incidência coincide com a QMD da FM?",
                    "diagnostico": temporal.descricao,
                    "operacao_sugerida": (
                        f"Concentrar cobertura no bloco "
                        f"{temporal.periodo_predominante.lower()}."
                    ),
                    "observacao": "",
                },
                {
                    "pergunta": "A dinâmica criminal coincide com o modelo de emprego da FM?",
                    "diagnostico": "[Síntese qualitativa pendente — modo offline]",
                    "operacao_sugerida": (
                        alocacao.modalidade_sugerida if alocacao else "—"
                    ),
                    "observacao": "",
                },
                {
                    "pergunta": "Os fatores relevantes estão sendo resolvidos pelos órgãos?",
                    "diagnostico": f"{len(ctx.fatores)} fatores urbanos mapeados no perímetro.",
                    "operacao_sugerida": "Ver plano de ação e seção 4 (fatores por órgão).",
                    "observacao": "",
                },
            ],
        },
    }


def _fatores_top(ctx) -> list[dict]:
    if ctx.fatores.empty or "tipo_ocorrencia_descricao" not in ctx.fatores.columns:
        return []
    agg = (
        ctx.fatores.groupby(["tipo_ocorrencia_descricao", "orgao_responsavel"])
        .size().reset_index(name="quantidade")
        .sort_values("quantidade", ascending=False).head(8)
    )
    return [
        {
            "fator": str(row["tipo_ocorrencia_descricao"]),
            "descricao": (
                f"{int(row['quantidade'])} ocorrências do fator mapeadas no perímetro."
            ),
            "responsavel": str(row["orgao_responsavel"]) or "—",
        }
        for _, row in agg.iterrows()
    ]
