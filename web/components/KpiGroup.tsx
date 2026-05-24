import { cn, formatPt } from "@/lib/utils";

type Metric = {
  label: string;
  value: number | string;
  sub?: string;
};

type Variant = "cover" | "demand" | "risk";

const variantStyles: Record<
  Variant,
  { wrap: string; accent: string; chip: string; title: string }
> = {
  cover: {
    wrap: "border-rio-100 bg-white",
    accent: "from-rio-800 to-rio-600",
    chip: "bg-rio-100 text-rio-800",
    title: "text-rio-800",
  },
  demand: {
    wrap: "border-rio-100 bg-white",
    accent: "from-rio-700 to-risk-med",
    chip: "bg-orange-50 text-risk-med",
    title: "text-risk-med",
  },
  risk: {
    wrap: "border-rio-100 bg-white",
    accent: "from-risk-med to-risk-high",
    chip: "bg-red-50 text-risk-high",
    title: "text-risk-high",
  },
};

export function KpiGroup({
  title,
  variant,
  metrics,
}: {
  title: string;
  variant: Variant;
  metrics: [Metric, Metric];
}) {
  const v = variantStyles[variant];
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-2xl border p-5 shadow-card",
        v.wrap,
      )}
    >
      <div
        className={cn(
          "absolute inset-x-0 top-0 h-1 bg-gradient-to-r",
          v.accent,
        )}
      />
      <div className="mb-4 flex items-center justify-between">
        <div
          className={cn(
            "text-[11px] font-semibold uppercase tracking-[0.08em]",
            v.title,
          )}
        >
          {title}
        </div>
        <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-semibold", v.chip)}>
          {variant === "cover"
            ? "Operação"
            : variant === "demand"
              ? "Volume"
              : "Sinal"}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {metrics.map((m) => (
          <div key={m.label}>
            <div className="text-kpi tabular font-semibold text-rio-ink">
              {typeof m.value === "number" ? formatPt(m.value) : m.value}
            </div>
            <div className="mt-1 text-[12px] font-medium text-rio-ink/70">
              {m.label}
            </div>
            {m.sub && (
              <div className="mt-0.5 text-[11px] text-muted">{m.sub}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
