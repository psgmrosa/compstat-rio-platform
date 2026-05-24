# 🛡️ CompStat Rio — Plataforma de Inteligência Criminal

> Geração automática do **Relatório Analítico de Área** do CompStat Municipal
> da Prefeitura do Rio de Janeiro, cruzando 5 fontes em silos com IA.

**Hackathon Anthropic 2026 — Claude Impact Lab Rio · Tema: Segurança Pública**

---

## 👥 Equipe

- **Nome:** _a preencher_
- **Membros:** _a preencher_
- **Tema:** Segurança Pública (CompStat Rio)

---

## 📋 Resumo

O CompStat Municipal opera sobre 22 áreas prioritárias da cidade, combinando
o policiamento da Força Municipal (600 agentes) com a resolução de fatores
urbanos pelos órgãos da Prefeitura (Comlurb, RioLuz, SEOP, Seconserva, SMAS,
CET-Rio, SMTR, GM-Rio). Hoje, cada **Relatório Analítico de Área** que
subsidia a reunião semanal é montado **à mão** — horas de compilação
manual cruzando ocorrências georreferenciadas, Disque Denúncia, RELINTs da
FM e fatores urbanos.

Esta plataforma faz isso automaticamente:

1. **Carrega e cruza** as 5 fontes oficiais (ocorrências, Disque Denúncia,
   RELINTs, fatores urbanos, polígonos FM) por área.
2. **Detecta coincidências de alto risco** (lógica do "bingo"): quando
   mancha criminal, fator urbano e dinâmica criminal se sobrepõem num
   mesmo segmento, gera score de prioridade.
3. **Sintetiza qualitativamente** a dinâmica criminal a partir dos relatos
   do Disque Denúncia e dos RELINTs usando o Claude Opus 4.7.
4. **Responde automaticamente** as 4 perguntas norteadoras da reunião:
   - Locais de maior incidência coincidem com a rota da FM?
   - Horário de maior incidência coincide com a QMD da FM?
   - Dinâmica criminal coincide com o modelo de emprego da FM?
   - Os fatores estão sendo resolvidos pelos órgãos responsáveis?
5. **Gera o Relatório Analítico em PDF ou DOCX** no formato do anexo do
   briefing CompStat — cover com mapa de segmentos quentes (heatmap KDE
   das ocorrências + câmeras + trechos críticos numerados), Resumo
   Executivo, indicadores e plano de ação pronto para a reunião.

Resultado: o que hoje leva **horas por área × 22 áreas/semana** passa a
levar **minutos**, com análise auditável, padronizada e ancorada nos dados.

---

## 🏗️ Arquitetura — como o Claude foi usado

```
┌────────────────────────────────────────────────────────────────────────┐
│  5 fontes (CSV/XLSX/SHP/DOCX)                                          │
│  ocorrências · Disque Denúncia · RELINTs · fatores urbanos · áreas FM  │
└──────────────────────────────┬─────────────────────────────────────────┘
                               │
            ┌──────────────────┼───────────────────┐
            ▼                  ▼                   ▼
   ╔════════════════╗ ╔═════════════════╗ ╔══════════════════╗
   ║  data_loaders  ║ ║   filters       ║ ║ analytics        ║
   ║  (pandas +     ║ ║  (sjoin por     ║ ║ • indicadores    ║
   ║   geopandas)   ║ ║   polígono FM)  ║ ║ • temporal H7×24 ║
   ╚════════════════╝ ╚═════════════════╝ ║ • bingo detector ║
                                          ║ • optimizer 600  ║
                                          ╚══════════════════╝
                                                    │
                                                    ▼
                              ╔═══════════════════════════════════════════╗
                              ║  Claude Opus 4.7 (1M context)             ║
                              ║  ─────────────────────────────────────    ║
                              ║  • tool_use forçado contra schema JSON    ║
                              ║    (RELATORIO_TOOL_SCHEMA)                ║
                              ║  • system prompt com prompt caching       ║
                              ║  • saída estruturada, validável           ║
                              ║                                           ║
                              ║  Responsabilidades:                       ║
                              ║   1. Síntese qualitativa da Dinâmica      ║
                              ║      Criminal (denúncias + RELINT)        ║
                              ║   2. 4 perguntas norteadoras com          ║
                              ║      diagnóstico + operação sugerida      ║
                              ║   3. Descrições contextualizadas dos      ║
                              ║      fatores urbanos                      ║
                              ║   4. Refinamento do Plano de Ação         ║
                              ╚═══════════════════════════════════════════╝
                                                    │
                                                    ▼
                              ╔═══════════════════════════════════════════╗
                              ║  pdf_renderer / template.render_relatorio ║
                              ║  → PDF (reportlab) ou DOCX (python-docx)  ║
                              ║    no formato do Anexo do Briefing        ║
                              ║    (cover com mapa, tabelas, plano)       ║
                              ╚═══════════════════════════════════════════╝
```

### Decisão de design — separação determinístico × qualitativo

**Tudo que é número (indicadores, ranking, heatmap, score do bingo,
alocação de 600 agentes) sai dos analytics Python — auditável, reproduzível,
sem alucinação.**

**O Claude é responsável apenas pelo que só ele faz bem: ler texto livre
do Disque Denúncia + RELINTs e sintetizar padrões qualitativos
(modus operandi, rotas de fuga, perfil), além de redigir as 4 respostas
às perguntas norteadoras.**

Essa separação resolve o critério de **Engenharia** (saída defensável)
e **Impacto Real** (a Prefeitura confia nos números porque eles vêm
dos dados, não da IA).

### Uso específico das features da API Anthropic

| Feature | Onde | Por quê |
|---|---|---|
| **Opus 4.7 (1M ctx)** | `llm.py` | Caber RELINTs + amostras de denúncias + fatores em um único call. |
| **Tool use forçado** | `template.RELATORIO_TOOL_SCHEMA` | Saída JSON estruturada validável contra schema; zero parsing frágil. |
| **Prompt caching** | `system` prompt + 5 fontes serializadas | Geração múltipla (22 áreas) reaproveita cache → custo e latência caem. |
| **System prompt detalhado** | `prompts.SYSTEM_PROMPT` | Princípios não-negociáveis (ancorar em dados, recomendações concretas com órgão). |

---

## 🎰 Lógica do "bingo" — coincidência de alto risco

Cada célula do grid (~110m × 110m) recebe um score quando 2+ camadas
coincidem:

| Camada | Sinal |
|---|---|
| 🔴 **Mancha Criminal** | ≥ 5 ocorrências de furto/roubo |
| 🟠 **Dinâmica Criminal** | ≥ 2 denúncias do Disque Denúncia |
| 🟡 **Fator Urbano** | ≥ 1 fator mapeado (iluminação, vegetação, PSR…) |

`score = 0.5 × n_ocorrencias_norm + 0.3 × n_denuncias_norm + 0.2 × n_fatores_norm`

Cada bingo vira sugestão de **ação no Plano** com o **órgão responsável**
extraído do mapeamento de fatores (RioLuz para iluminação, Comlurb para
vegetação/lixo, SEOP para comércio irregular, etc.).

---

## 📂 Estrutura do repositório

```
.
├── streamlit_app.py             # UI principal (4 abas + gerar relatório)
├── relint_gen/
│   ├── config.py                # paths + nomes oficiais das 8 áreas FM
│   ├── data_loaders.py          # 5 fontes (encoding/sep corretos)
│   ├── filters.py               # filter_by_area() → AreaContext
│   ├── template.py              # dataclasses + render_relatorio() + tool schema
│   ├── prompts.py               # system prompt + serialização do contexto
│   ├── llm.py                   # Anthropic SDK + tool_use + prompt caching
│   ├── pipeline.py              # orquestrador end-to-end
│   └── analytics/
│       ├── temporal.py          # heatmap 7×24 + PNG
│       ├── indicadores.py       # contagens, ranking entre áreas FM
│       ├── bingo.py             # detector de coincidências multi-camada
│       └── optimizer.py         # alocação dos 600 agentes nas áreas
├── scripts/
│   ├── generate_relint.py       # CLI: gera para 1 área ou todas
│   ├── extract_template.py      # parser dos RELINTs (input qualitativo)
│   └── test_loaders.py          # smoke test dos parsers
├── dados/                       # fontes oficiais (CSV/XLSX)
├── relints/                     # 8 RELINTs da FM (entrada qualitativa)
├── sh_area_forca/               # shapefile dos 8 polígonos FM
├── templates/                   # JSONs com a estrutura dos RELINTs extraídos
└── output/                      # .docx gerados + heatmap PNG + payloads
```

---

## 🚀 Quick start

```bash
# 1. Setup
python3 -m venv .venv
.venv/bin/pip install -e .

# 2. Configurar a chave do Claude
cp .env.example .env
# editar .env e preencher ANTHROPIC_API_KEY

# 3. Gerar relatório PDF (default) para uma área
.venv/bin/python -m scripts.generate_relint \
    --area "Presidente Vargas - Campo de Santana - Central do Brasil - Cinelândia"

# Outros formatos
.venv/bin/python -m scripts.generate_relint --area "Jardim de Alah" --format docx
.venv/bin/python -m scripts.generate_relint --area "Jardim de Alah" --format ambos

# 4. Gerar para todas as 8 áreas
.venv/bin/python -m scripts.generate_relint --all --format pdf

# 5. Subir a UI (homepage com agentes + detalhe por área)
.venv/bin/streamlit run streamlit_app.py
```

Modo offline (sem Claude, só analytics — útil pra desenvolver):

```bash
.venv/bin/python -m scripts.generate_relint --area "Jardim de Alah" --offline
```

### Formatos de saída

| Formato | Quando usar |
|---|---|
| **PDF** (default) | Apresentação na reunião CompStat; visual idêntico ao anexo do briefing — cover com mapa, cabeçalhos azuis, tabelas estilizadas. |
| **DOCX** | Quando o analista precisa **editar** antes da reunião (ex.: ajustar texto do diagnóstico). |
| **Ambos** | Gera os dois numa só execução. |

---

## 🎯 Critério de Impacto Real — por que a Prefeitura usaria HOJE

| Necessidade do CompStat | Como esta plataforma resolve |
|---|---|
| Reduzir tempo do relatório de **horas para minutos** | Pipeline gera relatório completo em ~30s (modo offline) ou ~1min (com Claude). |
| Cobrir **22 áreas** por ciclo, não só uma seleção | `--all` gera todos em batch; UI permite seleção rápida. |
| Decisões baseadas em **dados cruzados**, não percepção | Bingo detector cruza 3 camadas no nível de segmento (~110m). |
| Padronização das análises e plano de ação | Template tabular fixo + Claude com tool_use → estrutura idêntica entre áreas. |
| **Rastreabilidade** das recomendações | Cada bingo cita lat/long, número de ocorrências, denúncias e fatores. |

---

## 🛠️ Stack

- **Python 3.11+**
- `anthropic` — Claude Opus 4.7 com tool_use
- `pandas` + `geopandas` + `shapely` — pipeline geoespacial
- `python-docx` — geração do .docx
- `matplotlib` — PNG do heatmap embedado
- `streamlit` + `folium` — interface web

---

## 🔗 Links

- **Repositório:** https://github.com/psgmrosa/compstat-rio-platform
- **Briefing técnico:** `Briefing_Hackathon_Desenvolvedores_CompStat-2.pdf`
- **Repo de referência (dados):** https://github.com/CompStat-Rio/claude_impact_lab_compstat_rio
- **Demo (vídeo 60s):** _a publicar antes das 16:15_
- **Aplicação web (Streamlit):** rode local com `streamlit run streamlit_app.py`

---

## ⚖️ Licença e dados

Dados e recursos referenciados estão sujeitos aos termos de uso e
licenciamento de suas respectivas fontes (Prefeitura do Rio de Janeiro,
Disque Denúncia, ISP/RJ, CIVITAS/COR). Este código é apresentado como
protótipo para o Hackathon Anthropic 2026.
