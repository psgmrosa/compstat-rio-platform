import type { AreaResumo } from "@/lib/types";
import { riskLabel, riskLevel } from "@/lib/types";
import { cn, formatPt, nomeCurto } from "@/lib/utils";

const riskChipStyle = {
  high: "bg-risk-high text-white",
  med: "bg-risk-med text-white",
  low: "bg-risk-low text-white",
} as const;

const riskAccent = {
  high: "before:bg-risk-high",
  med: "before:bg-risk-med",
  low: "before:bg-risk-low",
} as const;

export function AreaCard({ area }: { area: AreaResumo }) {
  const level = riskLevel(area.pct_risco);
  return (
    <article
      className={cn(
        "group relative overflow-hidden rounded-2xl border border-border bg-white p-5 shadow-card transition hover:-translate-y-0.5 hover:shadow-hover",
        "before:absolute before:left-0 before:top-0 before:h-full before:w-1",
        riskAccent[level],
      )}
    >
      <header className="mb-4 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="truncate text-[14px] font-semibold leading-tight text-rio-800">
            {nomeCurto(area.nome, 38)}
          </h3>
          <p className="mt-0.5 text-[11px] text-muted">{area.ranking}</p>
        </div>
        <span
          className={cn(
            "shrink-0 rounded-full px-2.5 py-0.5 text-[10px] font-bold tracking-wide",
            riskChipStyle[level],
          )}
        >
          {riskLabel[level]}
        </span>
      </header>

      <div className="mb-5 flex items-baseline gap-1.5">
        <span className="text-hero tabular font-semibold text-rio-ink">
          {area.agentes}
        </span>
        <span className="text-[13px] font-medium text-muted">/600 agentes</span>
      </div>

      <dl className="mb-4 grid grid-cols-2 gap-3 text-[12px]">
        <div>
          <dt className="text-[10px] uppercase tracking-wide text-muted">
            Ocorrências
          </dt>
          <dd className="tabular text-[15px] font-semibold text-rio-ink">
            {formatPt(area.ocorrencias)}
          </dd>
        </div>
        <div>
          <dt className="text-[10px] uppercase tracking-wide text-muted">
            Trechos críticos
          </dt>
          <dd className="tabular text-[15px] font-semibold text-rio-ink">
            {area.bingos}
          </dd>
        </div>
        <div>
          <dt className="text-[10px] uppercase tracking-wide text-muted">
            Fatores urbanos
          </dt>
          <dd className="tabular text-[15px] font-semibold text-rio-ink">
            {formatPt(area.fatores)}
          </dd>
        </div>
        <div>
          <dt className="text-[10px] uppercase tracking-wide text-muted">
            Câmeras
          </dt>
          <dd className="tabular text-[15px] font-semibold text-rio-ink">
            {area.cameras}
          </dd>
        </div>
      </dl>

      <div className="mb-3 text-[11px] text-muted">
        <span className="text-rio-ink/70">{area.pct_risco.toFixed(1)}%</span>
        <span> do risco · top: </span>
        <span className="text-rio-ink/80">{area.top_tipo}</span>
      </div>

      <footer className="border-t border-border pt-3 text-[11px] italic leading-snug text-muted">
        {area.modalidade}
      </footer>
    </article>
  );
}
