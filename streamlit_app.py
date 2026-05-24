"""CompStat Rio — interface web para gerar Relatórios Analíticos de Área.

Roda com:

    .venv/bin/streamlit run streamlit_app.py
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from streamlit.components.v1 import html as st_html

from relint_gen import config, filters
from relint_gen.analytics import bingo as bingo_mod
from relint_gen.analytics import indicadores as ind_mod
from relint_gen.analytics import optimizer as opt_mod
from relint_gen.analytics import temporal as temp_mod


st.set_page_config(
    page_title="CompStat Rio — Inteligência Criminal",
    page_icon="🛡️",
    layout="wide",
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


# --- sidebar ----------------------------------------------------------------
with st.sidebar:
    st.markdown("### Área de Análise")
    areas = filters.list_areas()
    area_sel = st.selectbox("Selecione a área FM", options=areas, index=7)

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


# --- carregamento dos dados -------------------------------------------------
@st.cache_data(show_spinner=False)
def _carregar_contexto(nome: str):
    ctx = filters.filter_by_area(nome)
    indic = ind_mod.indicadores(ctx.ocorrencias, ctx.nome)
    temporal = temp_mod.heatmap_temporal(ctx.ocorrencias)
    bingos = bingo_mod.detectar_bingos(
        ctx.poligono, ctx.ocorrencias, ctx.denuncias, ctx.fatores,
    )
    alocacao = opt_mod.sugestao_para_area(ctx.nome)
    return ctx, indic, temporal, bingos, alocacao


with st.spinner("Carregando dados e cruzando camadas..."):
    ctx, indic, temporal, bingos, alocacao = _carregar_contexto(area_sel)


# --- métricas no topo -------------------------------------------------------
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Ocorrências", f"{indic.total:,}".replace(",", "."))
c2.metric("Denúncias DD", f"{len(ctx.denuncias):,}".replace(",", "."))
c3.metric("Fatores urbanos", f"{len(ctx.fatores):,}".replace(",", "."))
c4.metric("Câmeras", f"{len(ctx.cameras):,}".replace(",", "."))
c5.metric("Trechos críticos", len(bingos), help="Coincidências multi-camada detectadas")

st.markdown("&nbsp;")


# --- abas -------------------------------------------------------------------
aba1, aba2, aba3, aba4, aba5 = st.tabs(
    ["🎯 Painel de Coincidências", "🗺️ Mapa", "🔥 Análise Temporal",
     "🏗️ Fatores Urbanos", "📄 Gerar Relatório"]
)


with aba1:
    st.markdown("### Coincidências detectadas (lógica do bingo)")
    st.caption(
        "Cada linha é um segmento onde 2+ camadas se sobrepõem. Quanto mais "
        "camadas (mancha criminal · fator urbano · denúncia DD) coincidem, "
        "maior a prioridade."
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
            f"**{alocacao.agentes} agentes** (de 600 totais nas 8 áreas FM) — "
            f"{alocacao.pct_risco}% do risco total. "
            f"Modalidade sugerida: _{alocacao.modalidade_sugerida}_"
        )
    else:
        st.warning("Sem dados para sugerir alocação.")


with aba2:
    st.markdown("### Sobreposição de camadas no território")
    centro = ctx.poligono.centroid
    m = folium.Map(location=[centro.y, centro.x], zoom_start=14, tiles="OpenStreetMap")

    # Polígono da área FM
    folium.GeoJson(
        ctx.poligono.__geo_interface__,
        name="Área FM",
        style_function=lambda _: {
            "color": "#1F3A5F", "weight": 2, "fillOpacity": 0.05,
        },
    ).add_to(m)

    # Ocorrências (sample para não pesar)
    oc_sample = ctx.ocorrencias.sample(min(800, len(ctx.ocorrencias))) \
        if len(ctx.ocorrencias) else ctx.ocorrencias
    for _, row in oc_sample.iterrows():
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=2, color="#c0392b", fill=True, fillOpacity=0.4, weight=0,
        ).add_to(m)

    # Câmeras
    for _, row in ctx.cameras.iterrows():
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=3, color="#27ae60", fill=True, fillOpacity=0.9, weight=0,
            tooltip="Câmera CIVITAS",
        ).add_to(m)

    # Bingos (top 8)
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
        "🟠 trechos críticos (clique para ver coincidências)."
    )


with aba3:
    st.markdown("### Heatmap: ocorrências por dia da semana × hora")
    st.caption(temporal.descricao)
    if temporal.total == 0:
        st.warning("Sem dados temporais suficientes.")
    else:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        arr = np.array(temporal.heatmap)
        fig, ax = plt.subplots(figsize=(11, 3.6))
        im = ax.imshow(arr, aspect="auto", cmap="Reds")
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
        "Cada fator vem com o **órgão municipal responsável** pela resolução."
    )
    if ctx.fatores.empty or "tipo_ocorrencia_descricao" not in ctx.fatores.columns:
        st.info("Nenhum fator urbano georreferenciado no perímetro.")
    else:
        agg = (
            ctx.fatores.groupby(["tipo_ocorrencia_descricao", "orgao_responsavel"])
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

    if st.button("⚡ Gerar relatório", type="primary", use_container_width=True):
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
