import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPt(n: number): string {
  return n.toLocaleString("pt-BR");
}

/**
 * Encurta o nome de uma área FM para legenda/card.
 * Espelha relint_gen.nome_curto() do streamlit_app.
 */
export function nomeCurto(nome: string, maxChars = 42): string {
  let n = nome;
  if (n.includes(" - ")) n = n.split(" - ")[0];
  if (n.includes(":")) n = n.split(":")[0];
  return n.length > maxChars ? n.slice(0, maxChars) + "…" : n;
}
