"use client";

import { useEffect, useMemo, useRef } from "react";
import L from "leaflet";

import type { AreaResumo } from "@/lib/types";
import { nomeCurto } from "@/lib/utils";

function colorForRisk(pct: number, maxRisk: number): string {
  const ratio = maxRisk > 0 ? pct / maxRisk : 0;
  const r = 255;
  const g = Math.round(220 - 180 * ratio);
  const b = Math.round(220 - 180 * ratio);
  return `rgb(${r}, ${g}, ${b})`;
}

export function RiskMap({ areas }: { areas: AreaResumo[] }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<L.Map | null>(null);

  const { center, maxRisk } = useMemo(() => {
    if (areas.length === 0) return { center: [-22.9, -43.2] as [number, number], maxRisk: 1 };
    const lat = areas.reduce((s, a) => s + a.centro[1], 0) / areas.length;
    const lon = areas.reduce((s, a) => s + a.centro[0], 0) / areas.length;
    const max = Math.max(...areas.map((a) => a.pct_risco), 1);
    return { center: [lat, lon] as [number, number], maxRisk: max };
  }, [areas]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const m = L.map(containerRef.current, {
      zoomControl: true,
      attributionControl: false,
    }).setView(center, 11);

    L.tileLayer(
      "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
      { maxZoom: 19 },
    ).addTo(m);

    areas.forEach((a) => {
      const layer = L.geoJSON(a.poligono_geojson as GeoJSON.GeometryObject, {
        style: {
          color: "#1F3A5F",
          weight: 1.5,
          fillColor: colorForRisk(a.pct_risco, maxRisk),
          fillOpacity: 0.65,
        },
      }).addTo(m);

      layer.bindTooltip(
        `<div style="font-family:inherit;font-size:12px">
           <div style="font-weight:600;color:#1F3A5F;margin-bottom:2px">
             ${nomeCurto(a.nome, 60)}
           </div>
           <div><b>${a.agentes}</b> agentes · ${a.pct_risco.toFixed(1)}% risco</div>
           <div>${a.ocorrencias.toLocaleString("pt-BR")} ocorrências · ${a.bingos} trechos</div>
         </div>`,
        { sticky: true, direction: "top" },
      );
    });

    mapRef.current = m;
    return () => {
      m.remove();
      mapRef.current = null;
    };
    // O mapa é renderizado uma vez — `areas` muda no boot e fica estável.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <section className="rounded-2xl border border-border bg-white p-6 shadow-card">
      <header className="mb-1 flex items-baseline justify-between">
        <h2 className="text-[15px] font-semibold text-rio-800">
          Mapa de risco · 8 áreas FM
        </h2>
        <span className="text-[12px] text-muted">
          claro = baixo · escuro = alto
        </span>
      </header>
      <p className="mb-4 text-[12px] text-muted">
        Polígonos oficiais da Força Municipal coloridos pelo % de risco do
        ciclo atual.
      </p>
      <div
        ref={containerRef}
        className="h-[360px] w-full overflow-hidden rounded-xl border border-border"
      />
    </section>
  );
}
