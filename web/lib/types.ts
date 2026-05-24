export type GeoJsonGeometry = {
  type: string;
  coordinates: unknown;
};

export type AreaResumo = {
  nome: string;
  agentes: number;
  pct_risco: number;
  modalidade: string;
  ocorrencias: number;
  roubos: number;
  furtos: number;
  denuncias: number;
  fatores: number;
  cameras: number;
  bingos: number;
  top_fator: string;
  top_tipo: string;
  ranking: string;
  centro: [number, number]; // [lon, lat]
  poligono_geojson: GeoJsonGeometry;
};

export type TotaisVisaoGeral = {
  areas: number;
  agentes_alocados: number;
  agentes_totais: number;
  ocorrencias: number;
  denuncias: number;
  fatores: number;
  bingos: number;
};

export type VisaoGeralResponse = {
  totais: TotaisVisaoGeral;
  areas: AreaResumo[];
};

export type RiskLevel = "high" | "med" | "low";

export const riskLevel = (pct: number): RiskLevel =>
  pct >= 20 ? "high" : pct >= 10 ? "med" : "low";

export const riskLabel: Record<RiskLevel, string> = {
  high: "ALTO",
  med: "MÉDIO",
  low: "BAIXO",
};
