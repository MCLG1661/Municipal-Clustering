"""
Constrói o dataset consolidado a partir dos arquivos PORDATA
armazenados na raiz do repositório.

O script:
- valida a presença dos 25 arquivos municipais;
- extrai os indicadores necessários;
- calcula variáveis derivadas;
- valida valores ausentes;
- gera pordata_municipios_2024.csv na raiz do projeto.
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
    """
    Normaliza valores textuais para facilitar buscas.
    """

    if pd.isna(value):
        return ""

    return str(value).strip().lower()


def find_value(df, text, column):
    """
    Localiza uma linha pela descrição textual e retorna
    o valor da coluna correspondente.
    """

    labels = df.iloc[:, 0].map(norm)

    hit = df[
        labels.str.contains(
            text,
            regex=False,
        )
    ]

    if hit.empty:
        return None

    value = hit.iloc[-1, column]

    if pd.isna(value) or value == "-":
        return None

    try:
        return float(value)

    except (TypeError, ValueError):
        return None


def extract_file(path):
    """
    Extrai os indicadores necessários de um arquivo
    municipal da PORDATA.
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

    pop11 = find_value(
        df,
        "população residente",
        1,
    )

    pop24 = find_value(
        df,
        "população residente",
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

    labels = df.iloc[:, 0].map(
        norm
    )

    alunos = df[
        labels.str.startswith(
            "alunos do ensino superior"
        )
    ]

    if (
        alunos.empty
        or pd.isna(
            alunos.iloc[0, 5]
        )
    ):
        alunos24 = None

    else:
        try:
            alunos24 = float(
                alunos.iloc[0, 5]
            )

        except (TypeError, ValueError):
            alunos24 = None

    required_values = {
        "População 2011": pop11,
        "População 2024": pop24,
        "Superfície": superficie24,
        "Nascimentos": nascimentos24,
        "Ensino Superior": alunos24,
    }

    missing = [
        name
        for name, value
        in required_values.items()
        if value is None
    ]

    if missing:
        raise ValueError(
            f"{municipio}: indicadores obrigatórios "
            f"não encontrados: {', '.join(missing)}"
        )

    if pop11 == 0:
        raise ValueError(
            f"{municipio}: população de 2011 igual a zero."
        )

    if pop24 == 0:
        raise ValueError(
            f"{municipio}: população de 2024 igual a zero."
        )

    if superficie24 == 0:
        raise ValueError(
            f"{municipio}: superfície igual a zero."
        )

    return {
        "Municipio": municipio,

        "Regiao":
        REGIOES[municipio],

        "Populacao":
        pop24,

        "Densidade":
        pop24
        / superficie24,

        "Jovens":
        find_value(
            df,
            "jovens (%)",
            5,
        ),

        "Idosos":
        find_value(
            df,
            "idosos (%)",
            5,
        ),

        "IdadeAtiva":
        find_value(
            df,
            "população em idade activa",
            5,
        ),

        "Desemprego":
        find_value(
            df,
            (
                "desempregados inscritos "
                "nos centros de emprego em %"
            ),
            5,
        ),

        "Residuos":
        find_value(
            df,
            (
                "resíduos urbanos "
                "recolhidos selectivamente"
            ),
            5,
        ),

        "Energia":
        find_value(
            df,
            (
                "consumo de energia "
                "eléctrica por habitante"
            ),
            5,
        ),

        "VariacaoPop":
        (
            (
                pop24
                - pop11
            )
            / pop11
        )
        * 100,

        "Natalidade":
        (
            nascimentos24
            / pop24
        )
        * 1000,

        "EnsinoSuperior_por1000":
        (
            alunos24
            / pop24
        )
        * 1000,
    }


def main():
    """
    Executa a consolidação dos arquivos municipais.
    """

    files = sorted(
        RAW_DIR.glob(
            "*.xlsx"
        )
    )

    if len(files) != 25:
        raise RuntimeError(
            "Esperados 25 arquivos .xlsx "
            f"na raiz do projeto; encontrados "
            f"{len(files)}."
        )

    data = pd.DataFrame(
        extract_file(path)
        for path in files
    )

    data = data.sort_values(
        "Municipio"
    ).reset_index(
        drop=True
    )

    if len(data) != 25:
        raise RuntimeError(
            f"Esperados 25 municípios; "
            f"obtidos {len(data)}."
        )

    duplicated = (
        data[
            "Municipio"
        ]
        .duplicated()
    )

    if duplicated.any():
        duplicates = (
            data.loc[
                duplicated,
                "Municipio",
            ]
            .tolist()
        )

        raise RuntimeError(
            "Municípios duplicados: "
            + ", ".join(
                duplicates
            )
        )

    if data.isna().any().any():

        columns = (
            data.columns[
                data.isna().any()
            ]
            .tolist()
        )

        raise RuntimeError(
            "Há valores ausentes nas colunas: "
            + ", ".join(
                columns
            )
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
        "Construção do dataset "
        "concluída com sucesso."
    )


if __name__ == "__main__":
    main()
