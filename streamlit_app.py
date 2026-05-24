"""CompStat Rio — interface web para gerar Relatórios Analíticos de Área.

Roda com:

    .venv/bin/streamlit run streamlit_app.py
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import folium
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from streamlit.components.v1 import html as st_html

from relint_gen import config, filters
from relint_gen.analytics import bingo as bingo_mod
from relint_gen.analytics import indicadores as ind_mod
from relint_gen.analytics import optimizer as opt_mod
from relint_gen.analytics import temporal as temp_mod

matplotlib.use("Agg")


st.set_page_config(
    page_title="CompStat Rio — Inteligência Criminal",
    page_icon="🛡️",
    layout="wide",
)


# --- session state ----------------------------------------------------------
if "view" not in st.session_state:
    st.session_state.view = "🏠 Visão Geral"
if "area_sel" not in st.session_state:
    st.session_state.area_sel = (
        "Presidente Vargas - Campo de Santana - Central do Brasil - Cinelândia"
    )


# --- header -----------------------------------------------------------------
st.markdown(
    """
    <div style="background:#1F3A5F;padding:16px 20px;border-radius:6px;
                margin-bottom:18px;color:white">
      <div style="font-size:22px;font-weight:700">🛡️ CompStat Rio</div>
      <div style="font-size:14px;opacity:.85">
        Plataforma de Inteligência Criminal · Geração automatizada do
        <b>Relatório Analítico de Área</b> · Subsídio para a reunião semanal
        do CompStat Municipal — Prefeitura do Rio de Janeiro
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# --- helpers de carregamento (cached) ---------------------------------------

@st.cache_data(show_spinner="Cruzando camadas das 8 áreas FM...")
def carregar_visao_geral() -> list[dict]:
    """Carrega resumo de todas as 8 áreas (cached — roda 1x por sessão)."""
    areas = filters.list_areas()
    alocacoes = opt_mod.alocar_efetivo()
    aloc_by_name = {a.nome: a for a in alocacoes}

    resumos: list[dict] = []
    for nome in areas:
        ctx = filters.filter_by_area(nome, com_referencia=False)
        indic = ind_mod.indicadores(ctx.ocorrencias, ctx.nome)
        bingos = bingo_mod.detectar_bingos(
            ctx.poligono, ctx.ocorrencias, ctx.denuncias, ctx.fatores,
        )

        top_fator = "—"
        if (not ctx.fatores.empty
                and "tipo_ocorrencia_descricao" in ctx.fatores.columns):
            vc = ctx.fatores["tipo_ocorrencia_descricao"].value_counts()
            if len(vc):
                top_fator = str(vc.index[0])

        top_tipo = indic.distribuicao[0][1] if indic.distribuicao else "—"

        aloc = aloc_by_name.get(nome)
        resumos.append({
            "nome": nome,
            "agentes": aloc.agentes if aloc else 0,
            "pct_risco": aloc.pct_risco if aloc else 0.0,
            "modalidade": aloc.modalidade_sugerida if aloc else "—",
            "ocorrencias": indic.total,
            "roubos": indic.roubos,
            "furtos": indic.furtos,
            "denuncias": len(ctx.denuncias),
            "fatores": len(ctx.fatores),
            "cameras": len(ctx.cameras),
            "bingos": len(bingos),
            "top_fator": top_fator,
            "top_tipo": top_tipo,
            "poligono_geojson": ctx.poligono.__geo_interface__,
            "centro": (ctx.poligono.centroid.x, ctx.poligono.centroid.y),
            "ranking": indic.ranking_str,
        })
    return resumos


@st.cache_data(show_spinner="Carregando área...")
def carregar_area_detalhe(nome: str):
    ctx = filters.filter_by_area(nome)
    indic = ind_mod.indicadores(ctx.ocorrencias, ctx.nome)
    temporal = temp_mod.heatmap_temporal(ctx.ocorrencias)
    bingos = bingo_mod.detectar_bingos(
        ctx.poligono, ctx.ocorrencias, ctx.denuncias, ctx.fatores,
    )
    alocacao = opt_mod.sugestao_para_area(ctx.nome)
    return ctx, indic, temporal, bingos, alocacao


def nome_curto(nome: str, *, max_chars: int = 35) -> str:
    """Versão compacta do nome da área para gráficos/legendas."""
    n = nome
    if " - " in n:
        n = n.split(" - ")[0]
    if ":" in n:
        n = n.split(":")[0]
    return n[:max_chars]


# --- sidebar ----------------------------------------------------------------
with st.sidebar:
    st.markdown("### Navegação")
    view = st.radio(
        "Visão",
        ["🏠 Visão Geral", "🔍 Detalhe da Área"],
        key="view",
        label_visibility="collapsed",
    )

    if view == "🔍 Detalhe da Área":
        st.markdown("---")
        st.markdown("### Área de Análise")
        st.selectbox(
            "Selecione a área FM",
            options=filters.list_areas(),
            key="area_sel",
        )

    st.markdown("---")
    st.markdown("### Modo de geração")
    has_api = bool(os.environ.get("ANTHROPIC_API_KEY"))
    if has_api:
        modo = st.radio(
            "Pipeline",
            ["Claude (Opus 4.7) — completo", "Offline — só analytics"],
            index=0,
        )
    else:
        st.warning("ANTHROPIC_API_KEY não configurada — apenas modo offline.")
        modo = "Offline — só analytics"
    usar_llm = modo.startswith("Claude")

    st.markdown("---")
    st.markdown("### Sobre")
    st.caption(
        "5 fontes cruzadas automaticamente: ocorrências, Disque Denúncia, "
        "RELINTs, fatores urbanos e polígonos FM. A IA sintetiza a dinâmica "
        "criminal e responde as 4 perguntas norteadoras."
    )


# ============================================================================
#  HOMEPAGE — VISÃO GERAL
# ============================================================================

def render_visao_geral():
    resumos = carregar_visao_geral()

    total_oc = sum(r["ocorrencias"] for r in resumos)
    total_dn = sum(r["denuncias"] for r in resumos)
    total_ft = sum(r["fatores"] for r in resumos)
    total_ag = sum(r["agentes"] for r in resumos)
    total_bg = sum(r["bingos"] for r in resumos)

    st.markdown("### Visão geral · 8 áreas FM da Prefeitura do Rio")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Áreas FM", len(resumos))
    c2.metric("Agentes FM alocados", f"{total_ag} / 600")
    c3.metric("Ocorrências", f"{total_oc:,}".replace(",", "."))
    c4.metric("Denúncias DD", f"{total_dn:,}".replace(",", "."))
    c5.metric("Fatores urbanos", f"{total_ft:,}".replace(",", "."))
    c6.metric("Trechos críticos", total_bg)

    st.markdown("&nbsp;")

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("#### 👮 Distribuição dos 600 agentes pelas áreas FM")
        st.caption(
            "Alocação proporcional ao score de risco (densidade de "
            "ocorrências), respeitando piso mínimo por área."
        )

        sorted_resumos = sorted(resumos, key=lambda r: -r["agentes"])
        labels = [nome_curto(r["nome"]) for r in sorted_resumos]
        agentes = [r["agentes"] for r in sorted_resumos]
        risk = [r["pct_risco"] for r in sorted_resumos]

        max_risk = max(risk) or 1.0
        cmap = plt.get_cmap("Reds")
        cores = [cmap(0.35 + 0.55 * (r / max_risk)) for r in risk]

        fig, ax = plt.subplots(figsize=(9, 4.8))
        bars = ax.barh(labels, agentes, color=cores, edgecolor="white")
        ax.invert_yaxis()
        for bar, a, r in zip(bars, agentes, risk):
            ax.text(bar.get_width() + 2,
                    bar.get_y() + bar.get_height() / 2,
                    f"{a} agentes  ·  {r:.1f}% risco",
                    va="center", fontsize=9, color="#1F3A5F")
        ax.set_xlabel("Agentes")
        ax.set_xlim(0, max(agentes) * 1.4 if agentes else 1)
        ax.set_title(f"Total alocado: {sum(agentes)} de 600",
                     fontsize=11, fontweight="bold", color="#1F3A5F")
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        ax.tick_params(left=False, bottom=False)
        fig.tight_layout()
        st.pyplot(fig, clear_figure=True)

    with col_right:
        st.markdown("#### 🗺️ Mapa: 8 áreas FM coloridas por risco")
        centro_lat = float(np.mean([r["centro"][1] for r in resumos]))
        centro_lon = float(np.mean([r["centro"][0] for r in resumos]))
        m = folium.Map(location=[centro_lat, centro_lon], zoom_start=11,
                       tiles="cartodbpositron")

        max_risk = max((r["pct_risco"] for r in resumos), default=1.0) or 1.0
        for r in resumos:
            ratio = r["pct_risco"] / max_risk
            r_ch = 255
            g_ch = int(220 - 180 * ratio)
            b_ch = int(220 - 180 * ratio)
            cor = f"#{r_ch:02X}{g_ch:02X}{b_ch:02X}"
            folium.GeoJson(
                r["poligono_geojson"],
                name=r["nome"],
                style_function=lambda _, c=cor: {
                    "color": "#1F3A5F", "weight": 2,
                    "fillColor": c, "fillOpacity": 0.6,
                },
                tooltip=folium.Tooltip(
                    f"<b>{nome_curto(r['nome'], max_chars=60)}</b><br>"
                    f"{r['agentes']} agentes · {r['pct_risco']:.1f}% risco<br>"
                    f"{r['ocorrencias']:,} ocorrências · "
                    f"{r['bingos']} trechos críticos"
                    .replace(",", "."),
                ),
            ).add_to(m)

        st_html(m._repr_html_(), height=480, scrolling=False)
        st.caption("Cor: branco (baixo) → vermelho (alto risco).")

    st.markdown("---")

    st.markdown("### 📋 Resumo por área")
    st.caption(
        "Clique em **Ver detalhes** para abrir o painel completo com mapa, "
        "heatmap temporal, coincidências e geração do .docx."
    )

    cards = sorted(resumos, key=lambda r: -r["agentes"])

    for inicio in range(0, len(cards), 4):
        cols = st.columns(4, gap="small")
        for col, r in zip(cols, cards[inicio:inicio + 4]):
            with col:
                _render_card(r)


def _render_card(r: dict) -> None:
    pct = r["pct_risco"]
    if pct >= 20:
        cor_borda = "#B22222"
        label_risco = "ALTO"
    elif pct >= 10:
        cor_borda = "#E67E22"
        label_risco = "MÉDIO"
    else:
        cor_borda = "#27AE60"
        label_risco = "BAIXO"

    st.markdown(
        f"""
        <div style="border:2px solid {cor_borda};border-radius:8px;
                    padding:14px 14px 10px;margin-bottom:8px;
                    min-height:240px;background:#FFFFFF">
          <div style="display:flex;justify-content:space-between;
                      align-items:flex-start;margin-bottom:8px">
            <div style="font-weight:700;color:#1F3A5F;font-size:13px;
                        line-height:1.2">
              {nome_curto(r['nome'], max_chars=42)}
            </div>
            <span style="background:{cor_borda};color:white;font-size:10px;
                         padding:2px 7px;border-radius:10px;
                         font-weight:600;white-space:nowrap">
              {label_risco}
            </span>
          </div>

          <div style="font-size:30px;font-weight:700;color:{cor_borda};
                      line-height:1">
            {r['agentes']}<span style="font-size:13px;color:#888;
                                       font-weight:400"> /600 agentes</span>
          </div>
          <div style="font-size:11px;color:#666;margin-bottom:10px">
            {r['pct_risco']:.1f}% do risco · {r['ranking']}
          </div>

          <div style="font-size:12px;color:#333;line-height:1.6">
            <b>{f"{r['ocorrencias']:,}".replace(",", ".")}</b> ocorrências  ·  <b>{r['bingos']}</b> trechos críticos<br>
            <b>{r['fatores']}</b> fatores  ·  <b>{r['cameras']}</b> câmeras<br>
            <span style="color:#888">Top tipo:</span> {r['top_tipo']}<br>
            <span style="color:#888">Top fator:</span> {r['top_fator'][:36]}
          </div>

          <div style="font-size:10px;color:#666;font-style:italic;
                      margin-top:8px;border-top:1px solid #EEE;padding-top:6px">
            {r['modalidade'][:80]}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Ver detalhes →", key=f"btn_{r['nome']}",
                 use_container_width=True):
        st.session_state.area_sel = r["nome"]
        st.session_state.view = "🔍 Detalhe da Área"
        st.rerun()


# ============================================================================
#  DETALHE DA ÁREA
# ============================================================================

def render_detalhe(area_sel: str, usar_llm: bool) -> None:
    ctx, indic, temporal, bingos, alocacao = carregar_area_detalhe(area_sel)

    st.markdown(f"### {area_sel}")
    st.caption(indic.ranking_str)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Ocorrências", f"{indic.total:,}".replace(",", "."))
    c2.metric("Denúncias DD", f"{len(ctx.denuncias):,}".replace(",", "."))
    c3.metric("Fatores urbanos", f"{len(ctx.fatores):,}".replace(",", "."))
    c4.metric("Câmeras", f"{len(ctx.cameras):,}".replace(",", "."))
    c5.metric("Trechos críticos", len(bingos),
              help="Coincidências multi-camada detectadas")

    st.markdown("&nbsp;")

    aba1, aba2, aba3, aba4, aba5 = st.tabs([
        "🎯 Painel de Coincidências",
        "🗺️ Mapa",
        "🔥 Análise Temporal",
        "🏗️ Fatores Urbanos",
        "📄 Gerar Relatório",
    ])

    with aba1:
        st.markdown("### Coincidências detectadas (lógica do bingo)")
        st.caption(
            "Cada linha é um segmento onde 2+ camadas se sobrepõem. Quanto "
            "mais camadas (mancha criminal · fator urbano · denúncia DD) "
            "coincidem, maior a prioridade."
        )
        if not bingos:
            st.info("Nenhuma coincidência multi-camada detectada no perímetro.")
        else:
            df = pd.DataFrame([
                {
                    "#": i + 1,
                    "Score": b.score,
                    "Camadas": "🔴" * (b.n_ocorrencias >= 5)
                               + "🟠" * (b.n_denuncias >= 2)
                               + "🟡" * (b.n_fatores >= 1),
                    "Ocorrências": b.n_ocorrencias,
                    "Denúncias": b.n_denuncias,
                    "Fatores": b.n_fatores,
                    "Lat/Long": f"{b.centro_lat:.5f}, {b.centro_lon:.5f}",
                    "Fatores principais": "; ".join(
                        f"{f[0]} ({f[1]})" for f in b.fatores_principais
                    ) or "—",
                }
                for i, b in enumerate(bingos)
            ])
            st.dataframe(df, hide_index=True, use_container_width=True)

        st.markdown("### Alocação sugerida para esta área")
        if alocacao:
            st.success(
                f"**{alocacao.agentes} agentes** (de 600 totais nas 8 áreas "
                f"FM) — {alocacao.pct_risco}% do risco total. "
                f"Modalidade sugerida: _{alocacao.modalidade_sugerida}_"
            )
        else:
            st.warning("Sem dados para sugerir alocação.")

    with aba2:
        st.markdown("### Sobreposição de camadas no território")
        centro = ctx.poligono.centroid
        m = folium.Map(location=[centro.y, centro.x], zoom_start=14,
                       tiles="OpenStreetMap")

        folium.GeoJson(
            ctx.poligono.__geo_interface__,
            name="Área FM",
            style_function=lambda _: {
                "color": "#1F3A5F", "weight": 2, "fillOpacity": 0.05,
            },
        ).add_to(m)

        oc_sample = (ctx.ocorrencias.sample(min(800, len(ctx.ocorrencias)))
                     if len(ctx.ocorrencias) else ctx.ocorrencias)
        for _, row in oc_sample.iterrows():
            folium.CircleMarker(
                location=[row.geometry.y, row.geometry.x],
                radius=2, color="#c0392b", fill=True, fillOpacity=0.4, weight=0,
            ).add_to(m)

        for _, row in ctx.cameras.iterrows():
            folium.CircleMarker(
                location=[row.geometry.y, row.geometry.x],
                radius=3, color="#27ae60", fill=True, fillOpacity=0.9, weight=0,
                tooltip="Câmera CIVITAS",
            ).add_to(m)

        for i, b in enumerate(bingos, start=1):
            folium.CircleMarker(
                location=[b.centro_lat, b.centro_lon],
                radius=8 + b.camadas * 3,
                color="#e67e22", weight=2, fill=True, fillOpacity=0.6,
                popup=folium.Popup(
                    f"<b>Trecho crítico #{i}</b><br>"
                    f"Score: {b.score}<br>"
                    f"Ocorrências: {b.n_ocorrencias}<br>"
                    f"Denúncias: {b.n_denuncias}<br>"
                    f"Fatores: {b.n_fatores}<br>"
                    f"<i>{'; '.join(f[0] for f in b.fatores_principais) or '—'}</i>",
                    max_width=320,
                ),
            ).add_to(m)

        folium.LayerControl().add_to(m)
        st_html(m._repr_html_(), height=560, scrolling=False)
        st.caption(
            "🟦 polígono FM · 🔴 ocorrências (amostra) · 🟢 câmeras · "
            "🟠 trechos críticos (clique para detalhes)."
        )

    with aba3:
        st.markdown("### Heatmap: ocorrências por dia da semana × hora")
        st.caption(temporal.descricao)
        if temporal.total == 0:
            st.warning("Sem dados temporais suficientes.")
        else:
            arr = np.array(temporal.heatmap)
            fig, ax = plt.subplots(figsize=(11, 3.6))
            ax.imshow(arr, aspect="auto", cmap="Reds")
            ax.set_xticks(range(24))
            ax.set_xticklabels([f"{h:02d}" for h in range(24)], fontsize=8)
            ax.set_yticks(range(7))
            ax.set_yticklabels(temp_mod.DIAS_PT, fontsize=9)
            ax.set_xlabel("Hora do dia")
            for d in range(7):
                for h in range(24):
                    v = arr[d, h]
                    if v > 0:
                        ax.text(h, d, int(v), ha="center", va="center",
                                color="black" if v < arr.max() * 0.6 else "white",
                                fontsize=7)
            fig.tight_layout()
            st.pyplot(fig, clear_figure=True)

        c1, c2 = st.columns(2)
        c1.info(f"**Período predominante**\n\n{temporal.periodo_predominante}")
        c2.warning(f"**Dia/horário crítico**\n\n{temporal.dia_horario_critico}")

    with aba4:
        st.markdown("### Fatores urbanos mapeados no perímetro")
        st.caption(
            "Cada fator vem com o **órgão municipal responsável** pela "
            "resolução."
        )
        if (ctx.fatores.empty
                or "tipo_ocorrencia_descricao" not in ctx.fatores.columns):
            st.info("Nenhum fator urbano georreferenciado no perímetro.")
        else:
            agg = (
                ctx.fatores.groupby(
                    ["tipo_ocorrencia_descricao", "orgao_responsavel"]
                )
                .size().reset_index(name="quantidade")
                .sort_values("quantidade", ascending=False)
            )
            agg.columns = ["Fator", "Órgão responsável", "Qtd"]
            st.dataframe(agg, hide_index=True, use_container_width=True)

    with aba5:
        st.markdown("### Gerar Relatório Analítico de Área (.docx)")
        st.caption(
            "Os números (indicadores, ranking, heatmap) saem dos analytics. "
            "O Claude sintetiza a dinâmica criminal, responde as 4 perguntas "
            "norteadoras e refina o plano de ação. Saída no formato do Anexo "
            "do Briefing CompStat."
        )

        if st.button("⚡ Gerar relatório", type="primary",
                     use_container_width=True):
            from relint_gen import pipeline

            status = st.empty()
            try:
                with st.spinner(
                    "Sintetizando dinâmica criminal e respondendo perguntas..."
                    if usar_llm else "Gerando relatório offline..."
                ):
                    t0 = time.perf_counter()
                    out = pipeline.gerar_relatorio(
                        area_sel, output_dir=Path("output"),
                        usar_llm=usar_llm, salvar_debug=True,
                    )
                    elapsed = time.perf_counter() - t0
                status.success(f"✓ Relatório gerado em {elapsed:.1f}s · {out.name}")

                with open(out, "rb") as fp:
                    st.download_button(
                        "📥 Baixar relatório (.docx)",
                        data=fp.read(),
                        file_name=out.name,
                        mime=(
                            "application/vnd.openxmlformats-officedocument."
                            "wordprocessingml.document"
                        ),
                        use_container_width=True,
                    )
            except Exception as exc:
                status.error(f"Erro: {exc}")

        st.markdown("---")
        st.markdown("#### O que vai no relatório")
        st.markdown(
            """
            - **Identificação da área** (AISP, DP, BPM, base FM, ORCRIM)
            - **Resumo Executivo** com as 4 perguntas norteadoras respondidas pela IA
            - **Indicadores** (roubos, furtos, ranking entre áreas FM)
            - **Análise temporal** (heatmap dia × hora)
            - **Dinâmica criminal** (síntese qualitativa do Disque Denúncia + RELINT)
            - **Efetivo FM** (sugestão de agentes, modalidade, horário)
            - **Fatores urbanos** (tabela com órgão responsável)
            - **Plano de Ação** (pré-populado a partir das coincidências)
            """
        )


# ============================================================================
#  ROUTER
# ============================================================================

if view == "🏠 Visão Geral":
    render_visao_geral()
else:
    render_detalhe(st.session_state.area_sel, usar_llm)
