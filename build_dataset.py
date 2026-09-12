"""
Constrói o dataset consolidado a partir dos 25 arquivos Excel
da PORDATA armazenados na raiz do repositório.

Saída:
    pordata_municipios_2024.csv
"""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT
OUT = ROOT / "pordata_municipios_2024.csv"


REGIOES = {
    "Braga": "Norte",
    "Bragança": "Norte",
    "Guimarães": "Norte",
    "Porto": "Norte",
    "Viana do Castelo": "Norte",
    "Vila Nova de Gaia": "Norte",
    "Vila Real": "Norte",
    "Aveiro": "Centro",
    "Castelo Branco": "Centro",
    "Coimbra": "Centro",
    "Guarda": "Centro",
    "Leiria": "Centro",
    "Viseu": "Centro",
    "Cascais": "Lisboa",
    "Lisboa": "Lisboa",
    "Setúbal": "Lisboa",
    "Sintra": "Lisboa",
    "Almada": "Lisboa",
    "Beja": "Alentejo",
    "Évora": "Alentejo",
    "Portalegre": "Alentejo",
    "Santarém": "Alentejo",
    "Faro": "Algarve",
    "Ponta Delgada": "Açores",
    "Funchal": "Madeira",
}


def norm(value):
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def numeric_value(value):
    if pd.isna(value) or value == "-":
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def find_value(df, text, column):
    """
    Busca um indicador textual e retorna a última ocorrência
    numérica válida, mantendo o comportamento adequado para
    os demais indicadores PORDATA.
    """

    labels = df.iloc[:, 0].map(norm)

    matches = df[
        labels.str.contains(
            text,
            regex=False,
        )
    ]

    if matches.empty:
        return None

    for _, row in matches.iloc[::-1].iterrows():
        value = numeric_value(row.iloc[column])

        if value is not None:
            return value

    return None


def find_population(df, column):
    """
    Localiza a população residente total.

    Os arquivos PORDATA podem conter várias linhas cujo texto
    inclui 'população residente'. Para evitar selecionar
    subgrupos ou indicadores derivados, a função percorre as
    ocorrências na ordem original e retorna o primeiro valor
    positivo válido.
    """

    labels = df.iloc[:, 0].map(norm)

    matches = df[
        labels.str.contains(
            "população residente",
            regex=False,
        )
    ]

    if matches.empty:
        return None

    for _, row in matches.iterrows():
        value = numeric_value(row.iloc[column])

        if value is not None and value > 0:
            return value

    return None


def find_students(df, column):
    """
    Obtém o número de alunos do ensino superior.
    """

    labels = df.iloc[:, 0].map(norm)

    matches = df[
        labels.str.startswith(
            "alunos do ensino superior"
        )
    ]

    if matches.empty:
        return None

    for _, row in matches.iterrows():
        value = numeric_value(row.iloc[column])

        if value is not None:
            return value

    return None


def extract_file(path):
    """
    Extrai os indicadores de um município.
    """

    df = pd.read_excel(
        path,
        header=None,
    )

    municipio = str(
        df.iloc[4, 0]
    ).strip()

    if municipio not in REGIOES:
        raise ValueError(
            f"Município não reconhecido em "
            f"{path.name}: {municipio}"
        )

    pop11 = find_population(
        df,
        1,
    )

    pop24 = find_population(
        df,
        5,
    )

    superficie24 = find_value(
        df,
        "superfície em km2",
        5,
    )

    nascimentos24 = find_value(
        df,
        "nascimentos (4)",
        5,
    )

    alunos24 = find_students(
        df,
        5,
    )

    required = {
        "População 2011": pop11,
        "População 2024": pop24,
        "Superfície": superficie24,
        "Nascimentos": nascimentos24,
        "Ensino Superior": alunos24,
    }

    missing = [
        name
        for name, value in required.items()
        if value is None
    ]

    if missing:
        raise ValueError(
            f"{municipio}: indicadores não encontrados: "
            + ", ".join(missing)
        )

    if pop11 <= 0:
        raise ValueError(
            f"{municipio}: população de 2011 inválida."
        )

    if pop24 <= 0:
        raise ValueError(
            f"{municipio}: população de 2024 inválida."
        )

    if superficie24 <= 0:
        raise ValueError(
            f"{municipio}: superfície inválida."
        )

    record = {
        "Municipio": municipio,
        "Regiao": REGIOES[municipio],
        "Populacao": pop24,
        "Densidade": pop24 / superficie24,
        "Jovens": find_value(
            df,
            "jovens (%)",
            5,
        ),
        "Idosos": find_value(
            df,
            "idosos (%)",
            5,
        ),
        "IdadeAtiva": find_value(
            df,
            "população em idade activa",
            5,
        ),
        "Desemprego": find_value(
            df,
            (
                "desempregados inscritos "
                "nos centros de emprego em %"
            ),
            5,
        ),
        "Residuos": find_value(
            df,
            (
                "resíduos urbanos "
                "recolhidos selectivamente"
            ),
            5,
        ),
        "Energia": find_value(
            df,
            (
                "consumo de energia "
                "eléctrica por habitante"
            ),
            5,
        ),
        "VariacaoPop": (
            (pop24 - pop11)
            / pop11
        )
        * 100,
        "Natalidade": (
            nascimentos24
            / pop24
        )
        * 1000,
        "EnsinoSuperior_por1000": (
            alunos24
            / pop24
        )
        * 1000,
    }

    missing_record = [
        key
        for key, value in record.items()
        if value is None
    ]

    if missing_record:
        raise ValueError(
            f"{municipio}: valores ausentes em: "
            + ", ".join(missing_record)
        )

    return record


def main():
    files = sorted(
        RAW_DIR.glob("*.xlsx")
    )

    if len(files) != 25:
        raise RuntimeError(
            "Esperados 25 arquivos .xlsx "
            f"na raiz; encontrados {len(files)}."
        )

    records = [
        extract_file(path)
        for path in files
    ]

    data = pd.DataFrame(
        records
    )

    data = (
        data
        .sort_values("Municipio")
        .reset_index(drop=True)
    )

    if len(data) != 25:
        raise RuntimeError(
            f"Esperados 25 municípios; "
            f"obtidos {len(data)}."
        )

    if data["Municipio"].duplicated().any():
        duplicates = (
            data.loc[
                data["Municipio"].duplicated(),
                "Municipio",
            ]
            .tolist()
        )

        raise RuntimeError(
            "Municípios duplicados: "
            + ", ".join(duplicates)
        )

    if data.isna().any().any():
        columns = (
            data.columns[
                data.isna().any()
            ]
            .tolist()
        )

        raise RuntimeError(
            "Valores ausentes nas colunas: "
            + ", ".join(columns)
        )

    data.to_csv(
        OUT,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        f"Dataset salvo em: {OUT}"
    )

    print(
        f"{len(data)} municípios × "
        f"{len(data.columns)} colunas"
    )

    print(
        "Construção do dataset concluída com sucesso."
    )


if __name__ == "__main__":
    main()
