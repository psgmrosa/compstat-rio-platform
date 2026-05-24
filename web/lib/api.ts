import type { VisaoGeralResponse } from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export async function fetchVisaoGeral(): Promise<VisaoGeralResponse> {
  const res = await fetch(`${API_BASE}/api/visao-geral`, {
    // SSR: o backend já tem cache; revalida a cada 60s.
    next: { revalidate: 60 },
  });
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${await res.text()}`);
  }
  return res.json();
}
