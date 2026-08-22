"""
Constrói o dataset consolidado a partir dos arquivos PORDATA em data/raw.

Correções em relação ao notebook acadêmico original:
- não cria dados simulados quando um arquivo está ausente;
- valida a presença dos 25 municípios;
- calcula taxa de natalidade a partir de nascimentos / população;
- calcula alunos do ensino superior por 1.000 habitantes;
- não usa "Poder de Compra", pois esse indicador não existe nos arquivos-fonte fornecidos.
"""
from pathlib import Path
import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
OUT = Path(__file__).resolve().parents[1] / "data" / "processed" / "pordata_municipios_2024.csv"

REGIOES = {
    "Braga": "Norte", "Bragança": "Norte", "Guimarães": "Norte", "Porto": "Norte",
    "Viana do Castelo": "Norte", "Vila Nova de Gaia": "Norte", "Vila Real": "Norte",
    "Aveiro": "Centro", "Castelo Branco": "Centro", "Coimbra": "Centro", "Guarda": "Centro",
    "Leiria": "Centro", "Viseu": "Centro",
    "Cascais": "Lisboa", "Lisboa": "Lisboa", "Setúbal": "Lisboa", "Sintra": "Lisboa", "Almada": "Lisboa",
    "Beja": "Alentejo", "Évora": "Alentejo", "Portalegre": "Alentejo", "Santarém": "Alentejo",
    "Faro": "Algarve", "Ponta Delgada": "Açores", "Funchal": "Madeira",
}

def norm(x):
    return str(x).strip().lower() if pd.notna(x) else ""

def find_value(df, text, col):
    labels = df.iloc[:, 0].map(norm)
    hit = df[labels.str.contains(text, regex=False)]
    if hit.empty:
        return None
    value = hit.iloc[-1, col]
    return float(value) if pd.notna(value) and value != "-" else None

def extract_file(path):
    df = pd.read_excel(path, header=None)
    municipio = str(df.iloc[4, 0]).strip()

    pop11 = find_value(df, "população residente", 1)
    pop24 = find_value(df, "população residente", 5)
    sup24 = find_value(df, "superfície em km2", 5)
    nascimentos24 = find_value(df, "nascimentos (4)", 5)

    labels = df.iloc[:, 0].map(norm)
    alunos = df[labels.str.startswith("alunos do ensino superior")]
    alunos24 = float(alunos.iloc[0, 5]) if not alunos.empty and pd.notna(alunos.iloc[0, 5]) else None

    return {
        "Municipio": municipio,
        "Regiao": REGIOES.get(municipio),
        "Populacao": pop24,
        "Densidade": pop24 / sup24,
        "Jovens": find_value(df, "jovens (%)", 5),
        "Idosos": find_value(df, "idosos (%)", 5),
        "IdadeAtiva": find_value(df, "população em idade activa", 5),
        "Desemprego": find_value(df, "desempregados inscritos nos centros de emprego em %", 5),
        "Residuos": find_value(df, "resíduos urbanos recolhidos selectivamente", 5),
        "Energia": find_value(df, "consumo de energia eléctrica por habitante", 5),
        "VariacaoPop": ((pop24 - pop11) / pop11) * 100,
        "Natalidade": (nascimentos24 / pop24) * 1000,
        "EnsinoSuperior_por1000": (alunos24 / pop24) * 1000,
    }

def main():
    files = sorted(RAW_DIR.glob("*.xlsx"))
    if len(files) != 25:
        raise RuntimeError(f"Esperados 25 arquivos .xlsx; encontrados {len(files)}.")

    data = pd.DataFrame(extract_file(path) for path in files).sort_values("Municipio")
    if data.isna().any().any():
        raise RuntimeError("Há valores ausentes no dataset consolidado. Revise os arquivos-fonte.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(OUT, index=False, encoding="utf-8-sig")
    print(f"Dataset salvo em: {OUT}")
    print(f"{len(data)} municípios × {len(data.columns)} colunas")

if __name__ == "__main__":
    main()
