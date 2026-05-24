"""Prompts e formatadores de contexto para o Claude.

Estratégia: os números (indicadores, heatmap, ranking, bingos, alocação FM)
saem dos módulos analytics — determinísticos e auditáveis. O Claude recebe
esses números num bloco estruturado e é responsável por:

  • sintetizar a Dinâmica Criminal (parágrafo qualitativo + extrações);
  • responder as 4 perguntas norteadoras com diagnóstico + operação sugerida;
  • escrever descrições contextualizadas dos fatores urbanos;
  • justificar a sugestão de efetivo (modalidade, horário, dias).
"""

from __future__ import annotations

import json
import textwrap

from .analytics.bingo import BingoCell
from .analytics.indicadores import IndicadoresResult
from .analytics.optimizer import AlocacaoArea
from .analytics.temporal import TemporalResult
from .filters import AreaContext


SYSTEM_PROMPT = textwrap.dedent("""\
    Você é um analista sênior do CompStat Municipal da Prefeitura do Rio de
    Janeiro. Sua tarefa é gerar Relatórios Analíticos de Área que vão direto
    para a reunião semanal de CompStat — leitura do Prefeito, secretários
    municipais e comandantes da Força Municipal.

    Princípios não-negociáveis:

    1. Ancore TODA afirmação numérica nos dados fornecidos no contexto.
       Não invente números, ranking, percentuais ou nomes de logradouros.
       Se a informação não está no contexto, escreva "não disponível".

    2. Seja conciso, técnico, sóbrio. Sem floreio, sem opinião pessoal,
       sem advérbios fracos. Linguagem de relatório executivo.

    3. Recomendações operacionais devem ser CONCRETAS:
       - órgão responsável explícito (FM, RioLuz, Comlurb, Seconserva, SEOP,
         SMAS, CET-Rio, SMTR, GM-Rio);
       - faixa de horário e dia da semana quando aplicável;
       - modalidade da FM (a pé / moto / viatura) quando aplicável.

    4. Para a seção "Dinâmica Criminal", extraia padrões CONCRETOS dos
       relatos do Disque Denúncia e do RELINT da área: modalidade, modus
       operandi, rotas de fuga, pontos de receptação, perfil de suspeitos.

    5. Para as 4 perguntas norteadoras, cada uma deve conter:
       - diagnóstico baseado no que os DADOS mostram;
       - operação sugerida (o que FM/órgãos devem fazer em resposta);
       - observação curta de ajuste, quando aplicável.
""")


def _serialize_top_denuncias(denuncias, n: int = 25) -> str:
    """Pega os relatos textuais mais informativos do DD."""
    if denuncias.empty:
        return "(nenhuma denúncia georreferenciada no perímetro)"
    col = "relato_redacted" if "relato_redacted" in denuncias.columns else None
    if not col:
        return "(coluna de relato indisponível)"
    sample = denuncias.dropna(subset=[col]).head(n)
    if sample.empty:
        return "(nenhum relato textual disponível)"
    linhas: list[str] = []
    for _, row in sample.iterrows():
        tipo = str(row.get("tipo", "")) or str(row.get("tipos.tipo", ""))
        bairro = row.get("bairro_logradouro", "")
        relato = str(row[col])[:380].strip()
        linhas.append(f"- [{tipo} · {bairro}] {relato}")
    return "\n".join(linhas)


def _serialize_fatores_agg(fatores) -> str:
    if fatores.empty:
        return "(nenhum fator urbano mapeado no perímetro)"
    if "tipo_ocorrencia_descricao" not in fatores.columns:
        return f"({len(fatores)} fatores sem coluna 'tipo_ocorrencia_descricao')"
    agg = (
        fatores.groupby(["tipo_ocorrencia_descricao", "orgao_responsavel"])
        .size()
        .reset_index(name="quantidade")
        .sort_values("quantidade", ascending=False)
        .head(15)
    )
    return "\n".join(
        f"- {row['tipo_ocorrencia_descricao']} | "
        f"órgão: {row['orgao_responsavel']} | qtd: {int(row['quantidade'])}"
        for _, row in agg.iterrows()
    )


def _serialize_bingos(bingos: list[BingoCell]) -> str:
    if not bingos:
        return "(nenhuma coincidência multi-camada detectada)"
    linhas: list[str] = []
    for i, b in enumerate(bingos, start=1):
        fatores = "; ".join(f"{f[0]} ({f[1]})" for f in b.fatores_principais) or "—"
        linhas.append(
            f"#{i} ({b.centro_lat:.5f},{b.centro_lon:.5f}) "
            f"score={b.score} camadas={b.camadas} | "
            f"ocorrências={b.n_ocorrencias} denúncias={b.n_denuncias} "
            f"fatores={b.n_fatores} | {fatores}"
        )
    return "\n".join(linhas)


def build_user_prompt(
    ctx: AreaContext,
    indic: IndicadoresResult,
    temporal: TemporalResult,
    bingos: list[BingoCell],
    alocacao: AlocacaoArea | None,
    plano_inicial: list[dict],
) -> str:
    """Monta o prompt do usuário com todo o contexto da área."""

    plano_json = json.dumps(plano_inicial[:8], ensure_ascii=False, indent=2)
    distribuicao_str = "\n".join(
        f"  {r}º {tipo} — {qtd} ({pct:.1f}%)"
        for r, tipo, qtd, pct in indic.distribuicao
    ) or "  (sem distribuição disponível)"

    relint_ref = ctx.relint_referencia or "(sem RELINT de referência para a área)"

    alocacao_str = "—"
    if alocacao:
        alocacao_str = (
            f"{alocacao.agentes} agentes (de 600 totais nas 8 áreas FM); "
            f"{alocacao.pct_risco}% do risco total; "
            f"modalidade sugerida (heurística): {alocacao.modalidade_sugerida}"
        )

    return textwrap.dedent(f"""\
        # ÁREA DE ANÁLISE: {ctx.nome}

        ## 1. INDICADORES (use estes números VERBATIM no relatório)

        - Período de análise: {indic.periodo}
        - Roubos: {indic.roubos}
        - Furtos: {indic.furtos}
        - Total: {indic.total}
        - Ranking entre áreas FM: {indic.ranking_str}

        Distribuição por tipo (top 5):
        {distribuicao_str}

        ## 2. ANÁLISE TEMPORAL (use VERBATIM)

        - Período predominante: {temporal.periodo_predominante}
        - Dia/horário crítico: {temporal.dia_horario_critico}
        - Descrição automática: {temporal.descricao}

        ## 3. FATORES URBANOS MAPEADOS NA ÁREA
        {_serialize_fatores_agg(ctx.fatores)}

        ## 4. RELATOS DO DISQUE DENÚNCIA (amostra)
        {_serialize_top_denuncias(ctx.denuncias)}

        ## 5. RELINT DE REFERÊNCIA DA ÁREA (input qualitativo)
        {relint_ref[:6000]}

        ## 6. COINCIDÊNCIAS MULTI-CAMADA DETECTADAS ("bingos")
        {_serialize_bingos(bingos)}

        ## 7. SUGESTÃO INICIAL DE ALOCAÇÃO FM (refine na sua resposta)
        {alocacao_str}

        ## 8. PLANO DE AÇÃO INICIAL (refine, complete prazos, melhore redação)
        {plano_json}

        ## 9. TAREFA

        Preencha COMPLETAMENTE a ferramenta `submit_relatorio_analitico`,
        respeitando:

        - identificacao.area_fm = "{ctx.nome}"
        - identificacao.num_trechos_criticos = {len(bingos)}
        - indicadores.* → copie verbatim dos itens acima
        - temporal.periodo_predominante / dia_horario_critico → copie verbatim
        - distribuicao → use os top 5 acima
        - dinamica.sintese → parágrafo de 4-7 linhas sintetizando o que as
          denúncias e o RELINT mostram (modus operandi, fluxos, rotas)
        - dinamica.modalidade / rotas_fuga / pontos_receptacao / perfil_suspeitos
          → extraídos dos relatos (listas curtas)
        - efetivo.* → propor com base na alocação sugerida e na dinâmica;
          justifique no campo `justificativa`
        - fatores → top 6-10 fatores urbanos da área, com descrição contextual
          (não copie só o tipo — explique o que isso significa no terreno) e
          órgão responsável correto
        - plano_acao → refine o plano inicial, mantendo ações pré-sugeridas
          quando fizerem sentido. Mínimo 5 ações.
        - resumo_executivo.perguntas → exatamente 4 perguntas norteadoras:
          (a) "Os locais de maior incidência criminal coincidem com a rota
              da FM?"
          (b) "O horário de maior incidência criminal coincide com a QMD
              (escala) da FM?"
          (c) "A dinâmica criminal coincide com o modelo de emprego da FM?"
          (d) "Os fatores relevantes para o crime estão sendo resolvidos
              pelos órgãos complementares?"
          Cada uma com `diagnostico` (do dado) + `operacao_sugerida` (ação).
    """)
