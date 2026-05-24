"""Paths e constantes do projeto."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DADOS = ROOT / "dados"
RELINTS_DIR = ROOT / "relints"
SHAPE_DIR = ROOT / "sh_area_forca"
TEMPLATES_DIR = ROOT / "templates"
OUTPUT_DIR = ROOT / "output"

OCORRENCIAS_CSV = DADOS / "df_ocorrencias_tratado - Extração 1 .csv"
DENUNCIAS_CSV = DADOS / "disk_denuncia.csv"
FATORES_CSV = DADOS / "fatores_urbanos.csv"
CAMERAS_CSV = DADOS / "cameras_areas_fm.csv"
DOMINIO_CSV = DADOS / "outros dados" / "dominio_territorial - Extração 1.csv"
CPSR_XLSX = DADOS / "outros dados" / "CPSR_2020_2022_2024.xlsx"
DICIONARIO_XLSX = DADOS / "Dicionário de dados.xlsx"
SHAPE_FM = SHAPE_DIR / "areas_forca_municipal.shp"

CRS_WGS84 = "EPSG:4326"
CRS_METRIC_RJ = "EPSG:31983"  # SIRGAS 2000 / UTM zone 23S — Rio


# Mapa fid → nome canônico da área FM (a partir do shapefile).
# Usado como fonte da verdade para nomes de área.
AREAS_FM_OFICIAIS: dict[int, str] = {
    2: "Rodoviária - Terminal Gentileza - Estação Leopoldina",
    9: "Metrô Botafogo - Rua São Clemente - Rua Voluntários da Pátria",
    10: "Jardim de Alah",
    11: "Campo Grande: Estação de Trem - Calçadão",
    12: "Rio Sul",
    14: "Praia de Botafogo - Rua Marquês de Abrantes",
    19: "Estações São Francisco Xavier - Afonso Pena",
    20: "Presidente Vargas - Campo de Santana - Central do Brasil - Cinelândia",
}

# Mapa nome da área → arquivo RELINT de referência (usado como style guide pra Claude).
RELINT_REFERENCIA: dict[str, str] = {
    "Rodoviária - Terminal Gentileza - Estação Leopoldina":
        "Cópia de RI_010_2026_Rodoviaria_Terminal_Gentileza.docx",
    "Metrô Botafogo - Rua São Clemente - Rua Voluntários da Pátria":
        "Cópia de RI_011_2026_Metro_Botafogo_Sao_Clemente.docx",
    "Jardim de Alah":
        "Cópia de RI_012_2026_Jardim_de_Alah.docx",
    "Campo Grande: Estação de Trem - Calçadão":
        "Cópia de RI_013_2026_Campo_Grande_Estacao_Calcadao.docx",
    "Rio Sul":
        "Cópia de RI_014_2026_Rio_Sul.docx",
    "Praia de Botafogo - Rua Marquês de Abrantes":
        "Cópia de RI_015_2026_Praia_Botafogo_Marques_Abrantes.docx",
    "Estações São Francisco Xavier - Afonso Pena":
        "Cópia de RI_016_2026_Estacoes_SFX_Afonso_Pena.docx",
    "Presidente Vargas - Campo de Santana - Central do Brasil - Cinelândia":
        "Cópia de RI_017_2026_Presidente_Vargas_Campo_Santana.docx",
}
