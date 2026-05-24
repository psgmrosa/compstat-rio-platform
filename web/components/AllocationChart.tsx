"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { AreaResumo } from "@/lib/types";
import { riskLevel } from "@/lib/types";
import { nomeCurto } from "@/lib/utils";

const riskFill = {
  high: "#B22222",
  med: "#E67E22",
  low: "#27AE60",
} as const;

type ChartRow = {
  nome: string;
  curto: string;
  agentes: number;
  pct_risco: number;
  ocorrencias: number;
  bingos: number;
  level: "high" | "med" | "low";
};

export function AllocationChart({ areas }: { areas: AreaResumo[] }) {
  const data: ChartRow[] = [...areas]
    .sort((a, b) => b.agentes - a.agentes)
    .map((a) => ({
      nome: a.nome,
      curto: nomeCurto(a.nome, 26),
      agentes: a.agentes,
      pct_risco: a.pct_risco,
      ocorrencias: a.ocorrencias,
      bingos: a.bingos,
      level: riskLevel(a.pct_risco),
    }));

  const totalAlocado = data.reduce((acc, r) => acc + r.agentes, 0);

  return (
    <section className="rounded-2xl border border-border bg-white p-6 shadow-card">
      <header className="mb-1 flex items-baseline justify-between">
        <h2 className="text-[15px] font-semibold text-rio-800">
          Distribuição dos 600 agentes
        </h2>
        <span className="tabular text-[12px] text-muted">
          alocado: <b className="text-rio-ink">{totalAlocado}</b> / 600
        </span>
      </header>
      <p className="mb-5 text-[12px] text-muted">
        Proporcional ao score de risco (densidade de ocorrências), com piso
        mínimo por área.
      </p>

      <div className="h-[340px] w-full">
        <ResponsiveContainer>
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 4, right: 32, bottom: 4, left: 8 }}
          >
            <CartesianGrid
              horizontal={false}
              stroke="#EEF1F6"
              strokeDasharray="3 3"
            />
            <XAxis
              type="number"
              tick={{ fontSize: 11, fill: "#5A6B7E" }}
              tickLine={false}
              axisLine={{ stroke: "#E5E9EF" }}
            />
            <YAxis
              type="category"
              dataKey="curto"
              width={150}
              tick={{ fontSize: 11, fill: "#0F1B2D" }}
              tickLine={false}
              axisLine={{ stroke: "#E5E9EF" }}
            />
            <Tooltip
              cursor={{ fill: "rgba(31, 58, 95, 0.04)" }}
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const row = payload[0].payload as ChartRow;
                return (
                  <div className="rounded-lg border border-border bg-white p-3 text-[12px] shadow-hover">
                    <div className="mb-1 font-semibold text-rio-800">
                      {row.curto}
                    </div>
                    <div className="grid grid-cols-2 gap-x-4 gap-y-0.5">
                      <span className="text-muted">Agentes</span>
                      <span className="tabular text-right font-semibold">
                        {row.agentes}
                      </span>
                      <span className="text-muted">Risco</span>
                      <span className="tabular text-right font-semibold">
                        {row.pct_risco.toFixed(1)}%
                      </span>
                      <span className="text-muted">Ocorrências</span>
                      <span className="tabular text-right">
                        {row.ocorrencias.toLocaleString("pt-BR")}
                      </span>
                      <span className="text-muted">Trechos críticos</span>
                      <span className="tabular text-right">{row.bingos}</span>
                    </div>
                  </div>
                );
              }}
            />
            <Bar
              dataKey="agentes"
              radius={[4, 4, 4, 4]}
              animationDuration={600}
            >
              {data.map((row) => (
                <Cell key={row.nome} fill={riskFill[row.level]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-4 text-[11px] text-muted">
        <Legend color="low" label="Baixo (< 10%)" />
        <Legend color="med" label="Médio (10–20%)" />
        <Legend color="high" label="Alto (≥ 20%)" />
      </div>
    </section>
  );
}

function Legend({
  color,
  label,
}: {
  color: keyof typeof riskFill;
  label: string;
}) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span
        className="inline-block h-2.5 w-2.5 rounded-sm"
        style={{ background: riskFill[color] }}
      />
      {label}
    </span>
  );
}
