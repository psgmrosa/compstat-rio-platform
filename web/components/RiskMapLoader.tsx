"use client";

import dynamic from "next/dynamic";

import type { AreaResumo } from "@/lib/types";

const RiskMap = dynamic(
  () => import("./RiskMap").then((m) => m.RiskMap),
  {
    ssr: false,
    loading: () => (
      <section className="rounded-2xl border border-border bg-white p-6 shadow-card">
        <div className="h-[420px] animate-pulse rounded-xl bg-rio-50" />
      </section>
    ),
  },
);

export function RiskMapLoader({ areas }: { areas: AreaResumo[] }) {
  return <RiskMap areas={areas} />;
}
