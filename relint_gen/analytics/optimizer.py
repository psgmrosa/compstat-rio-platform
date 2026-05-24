"""Otimizador de alocação da Força Municipal (600 agentes / 22 áreas).

Distribui o efetivo entre as áreas proporcionalmente ao score de risco
(densidade de ocorrências), respeitando um piso mínimo por área.
"""

from __future__ import annotations

from dataclasses import dataclass

from .. import data_loaders


EFETIVO_TOTAL = 600
PISO_POR_AREA = 15           # mínimo razoável por área FM
MAX_POR_AREA = 80            # cap pra evitar concentração excessiva


@dataclass
class AlocacaoArea:
    nome: str
    agentes: int
    pct_risco: float
    modalidade_sugerida: str


def _modalidade_por_dinamica(modalidades_observadas: list[str]) -> str:
    """Heurística: cobre a modalidade dominante na dinâmica criminal."""
    mods = " ".join(modalidades_observadas).lower()
    if "moto" in mods:
        return "Moto (resposta rápida) + cobertura a pé em pontos quentes"
    if "veículo" in mods or "carro" in mods or "veicular" in mods:
        return "Viatura motorizada com pontos de bloqueio"
    if "armado" in mods or "arma" in mods:
        return "Viatura + reforço tático"
    return "A pé (presença ostensiva em ponto fixo de alto fluxo)"


def alocar_efetivo(modalidades_por_area: dict[str, list[str]] | None = None
                   ) -> list[AlocacaoArea]:
    """Aloca os 600 agentes entre as 8 áreas FM por score de risco.

    Args:
        modalidades_por_area: opcional. Dict nome_area → lista de modalidades
            observadas (vem da síntese da Dinâmica Criminal). Se ausente,
            usa heurística por densidade.
    """
    from .indicadores import _ranking_global

    ranking = _ranking_global()
    if not ranking:
        return []

    total_oc = sum(v for _, v in ranking)
    n_areas = len(ranking)
    # Distribui o piso e aloca o restante por risco.
    restante = EFETIVO_TOTAL - PISO_POR_AREA * n_areas
    restante = max(restante, 0)

    out: list[AlocacaoArea] = []
    for nome, qtd in ranking:
        pct = qtd / total_oc if total_oc else 1.0 / n_areas
        agentes = PISO_POR_AREA + int(round(pct * restante))
        agentes = min(agentes, MAX_POR_AREA)
        mods = (modalidades_por_area or {}).get(nome, [])
        out.append(AlocacaoArea(
            nome=nome, agentes=agentes, pct_risco=round(pct * 100, 1),
            modalidade_sugerida=_modalidade_por_dinamica(mods),
        ))

    # Ajuste fino se sobrar/faltar por arredondamento
    delta = EFETIVO_TOTAL - sum(a.agentes for a in out)
    if delta != 0 and out:
        out[0].agentes += delta

    return out


def sugestao_para_area(area_nome: str,
                       alocacoes: list[AlocacaoArea] | None = None
                       ) -> AlocacaoArea | None:
    """Devolve a alocação sugerida para uma área específica."""
    alocacoes = alocacoes or alocar_efetivo()
    for a in alocacoes:
        if a.nome.strip() == area_nome.strip():
            return a
    return None
