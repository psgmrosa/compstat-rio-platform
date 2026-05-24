import { AllocationChart } from "@/components/AllocationChart";
import { AreaCard } from "@/components/AreaCard";
import { Header } from "@/components/Header";
import { KpiGroup } from "@/components/KpiGroup";
import { RiskMapLoader } from "@/components/RiskMapLoader";
import { fetchVisaoGeral } from "@/lib/api";

export default async function HomePage() {
  const data = await fetchVisaoGeral();
  const { totais, areas } = data;

  const cards = [...areas].sort((a, b) => b.agentes - a.agentes);

  return (
    <div className="min-h-screen bg-bg">
      <Header />

      <main className="mx-auto max-w-[1400px] px-6 py-8">
        {/* Hero — título + subtítulo */}
        <section className="mb-6">
          <div className="text-[11px] font-semibold uppercase tracking-[0.1em] text-rio-700">
            Ciclo CompStat · 8 áreas FM
          </div>
          <h1 className="mt-1 text-[28px] font-semibold leading-tight tracking-tight text-rio-ink">
            Visão geral da operação
          </h1>
          <p className="mt-1 max-w-2xl text-[14px] text-muted">
            Cruzamento determinístico das 5 fontes oficiais. Os números abaixo
            saem dos analytics; o Claude entra só para sintetizar a dinâmica
            criminal no relatório por área.
          </p>
        </section>

        {/* Item 2 — KPIs agrupados em 3 cards (Cobertura · Demanda · Risco) */}
        <section className="mb-8 grid grid-cols-1 gap-4 md:grid-cols-3">
          <KpiGroup
            title="Cobertura"
            variant="cover"
            metrics={[
              { label: "Áreas FM monitoradas", value: totais.areas },
              {
                label: "Agentes alocados",
                value: `${totais.agentes_alocados}/${totais.agentes_totais}`,
                sub: "Força Municipal",
              },
            ]}
          />
          <KpiGroup
            title="Demanda"
            variant="demand"
            metrics={[
              {
                label: "Ocorrências (roubo + furto)",
                value: totais.ocorrencias,
              },
              { label: "Denúncias Disque Denúncia", value: totais.denuncias },
            ]}
          />
          <KpiGroup
            title="Sinal de risco"
            variant="risk"
            metrics={[
              { label: "Fatores urbanos mapeados", value: totais.fatores },
              {
                label: "Trechos críticos (bingo)",
                value: totais.bingos,
                sub: "2+ camadas coincidentes",
              },
            ]}
          />
        </section>

        {/* Item 4 — gráfico interativo + mapa, lado a lado */}
        <section className="mb-8 grid grid-cols-1 gap-4 lg:grid-cols-5">
          <div className="lg:col-span-3">
            <AllocationChart areas={areas} />
          </div>
          <div className="lg:col-span-2">
            <RiskMapLoader areas={areas} />
          </div>
        </section>

        {/* Item 3 — cards de área redesenhados */}
        <section className="mb-12">
          <header className="mb-3 flex items-baseline justify-between">
            <h2 className="text-[15px] font-semibold text-rio-800">
              Áreas FM ordenadas por alocação
            </h2>
            <span className="text-[12px] text-muted">
              {areas.length} áreas · clique para abrir detalhe
            </span>
          </header>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {cards.map((area) => (
              <AreaCard key={area.nome} area={area} />
            ))}
          </div>
        </section>

        <footer className="border-t border-border pt-6 text-[11px] text-muted">
          Fontes: ocorrências criminais · Disque Denúncia · RELINTs FM ·
          fatores urbanos · polígonos das áreas FM. Plataforma desenvolvida
          para o Hackathon Anthropic 2026 · Claude Impact Lab Rio.
        </footer>
      </main>
    </div>
  );
}
