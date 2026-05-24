export function Header() {
  return (
    <header className="border-b border-border bg-rio-900 text-white">
      <div className="mx-auto flex max-w-[1400px] items-center justify-between px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="grid h-9 w-9 place-items-center rounded-lg bg-white/10 text-lg font-bold">
            CR
          </div>
          <div>
            <div className="text-[15px] font-semibold leading-tight">
              CompStat Rio
            </div>
            <div className="text-[12px] leading-tight text-white/70">
              Plataforma de Inteligência Criminal · Prefeitura do Rio
            </div>
          </div>
        </div>

        <nav className="hidden items-center gap-1 md:flex">
          <a
            href="#"
            className="rounded-md bg-white/10 px-3 py-1.5 text-sm font-medium"
          >
            Visão Geral
          </a>
          <a
            href="#"
            className="rounded-md px-3 py-1.5 text-sm text-white/75 transition hover:bg-white/5 hover:text-white"
          >
            Áreas
          </a>
          <a
            href="#"
            className="rounded-md px-3 py-1.5 text-sm text-white/75 transition hover:bg-white/5 hover:text-white"
          >
            Relatórios
          </a>
        </nav>

        <div className="hidden items-center gap-2 md:flex">
          <span className="rounded-full bg-risk-low/20 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-risk-low">
            Dados atualizados
          </span>
        </div>
      </div>
    </header>
  );
}
