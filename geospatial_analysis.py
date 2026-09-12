from pathlib import Path
from urllib.request import urlretrieve
from zipfile import ZipFile
import sqlite3
import unicodedata

import folium
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import pandas as pd


ROOT = Path(__file__).resolve().parent

DATA = ROOT / "municipal_clusters.csv"
CACHE = ROOT / "data_caop2025"
IMAGES = ROOT / "images"
DOCS = ROOT / "docs"


CAOP_URLS = {
    "Continente": (
        "https://geo2.dgterritorio.gov.pt/caop/"
        "CAOP_Continente_2025-gpkg.zip"
    ),
    "Acores": (
        "https://geo2.dgterritorio.gov.pt/caop/"
        "CAOP_RAA_2025-gpkg.zip"
    ),
    "Madeira": (
        "https://geo2.dgterritorio.gov.pt/caop/"
        "CAOP_RAM_2025-gpkg.zip"
    ),
}


PALETTE = {
    0: "#66c2a5",
    1: "#a6d854",
    2: "#b3b3b3",
}


def normalize_name(value):
    """
    Normaliza nomes para facilitar o relacionamento
    entre municípios da PORDATA e da CAOP.
    """

    text = str(value).strip().casefold()

    text = unicodedata.normalize(
        "NFKD",
        text,
    )

    return "".join(
        char
        for char in text
        if not unicodedata.combining(char)
    )


def ensure_caop_downloads():
    """
    Faz download e extração dos GeoPackages oficiais
    da CAOP2025 caso ainda não estejam disponíveis.
    """

    CACHE.mkdir(
        parents=True,
        exist_ok=True,
    )

    geopackages = []

    for region, url in CAOP_URLS.items():

        region_dir = CACHE / region.lower()

        region_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        existing = list(
            region_dir.rglob("*.gpkg")
        )

        if existing:
            geopackages.extend(existing)
            continue

        zip_path = CACHE / f"{region}.zip"

        print(
            f"Baixando CAOP2025 — {region}..."
        )

        urlretrieve(
            url,
            zip_path,
        )

        print(
            f"Extraindo CAOP2025 — {region}..."
        )

        with ZipFile(zip_path) as archive:
            archive.extractall(
                region_dir
            )

        extracted = list(
            region_dir.rglob("*.gpkg")
        )

        if not extracted:
            raise FileNotFoundError(
                f"Nenhum GeoPackage encontrado "
                f"após extrair {region}."
            )

        geopackages.extend(
            extracted
        )

    return geopackages


def gpkg_layers(path):
    """
    Retorna as camadas vetoriais disponíveis
    dentro de um GeoPackage.
    """

    with sqlite3.connect(path) as connection:

        rows = connection.execute(
            """
            SELECT table_name
            FROM gpkg_contents
            WHERE data_type = 'features'
            """
        ).fetchall()

    return [
        row[0]
        for row in rows
    ]


def layer_columns(path, layer):
    """
    Retorna as colunas disponíveis
    em uma camada do GeoPackage.
    """

    with sqlite3.connect(path) as connection:

        rows = connection.execute(
            f'PRAGMA table_info("{layer}")'
        ).fetchall()

    return {
        row[1].lower(): row[1]
        for row in rows
    }


def find_municipality_layer(path):
    """
    Identifica automaticamente a camada municipal
    existente em cada GeoPackage da CAOP.
    """

    candidates = []

    for layer in gpkg_layers(path):

        columns = layer_columns(
            path,
            layer,
        )

        normalized_layer = normalize_name(
            layer
        )

        score = 0

        if "municip" in normalized_layer:
            score += 5

        if "concelh" in normalized_layer:
            score += 5

        if "municipio" in columns:
            score += 4

        if "concelho" in columns:
            score += 4

        if "dtmn" in columns:
            score += 3

        if score:
            candidates.append(
                (
                    score,
                    layer,
                    columns,
                )
            )

    if not candidates:
        raise ValueError(
            "Não foi possível identificar "
            f"uma camada municipal em {path.name}."
        )

    candidates.sort(
        reverse=True,
        key=lambda item: item[0],
    )

    return (
        candidates[0][1],
        candidates[0][2],
    )


def infer_name_column(columns):
    """
    Identifica a coluna que contém
    o nome do município.
    """

    possible_names = (
        "municipio",
        "concelho",
        "nome",
        "name",
    )

    for candidate in possible_names:

        if candidate in columns:
            return columns[candidate]

    raise ValueError(
        "Não foi possível identificar "
        "o campo com o nome do município."
    )


def load_caop():
    """
    Carrega os municípios de Portugal Continental,
    Açores e Madeira e converte as geometrias
    para EPSG:4326.
    """

    frames = []

    geopackages = ensure_caop_downloads()

    for gpkg in geopackages:

        layer, columns = find_municipality_layer(
            gpkg
        )

        name_column = infer_name_column(
            columns
        )

        print(
            f"Lendo {gpkg.name} "
            f"| camada: {layer}"
        )

        frame = gpd.read_file(
            gpkg,
            layer=layer,
        )

        frame = frame[
            [
                name_column,
                "geometry",
            ]
        ].copy()

        frame = frame.rename(
            columns={
                name_column:
                "Municipio_CAOP"
            }
        )

        frame["municipio_key"] = (
            frame[
                "Municipio_CAOP"
            ]
            .map(
                normalize_name
            )
        )

        if frame.crs is None:
            raise ValueError(
                f"CRS ausente em "
                f"{gpkg.name}."
            )

        frame = frame.to_crs(
            epsg=4326
        )

        frames.append(
            frame
        )

    ca_op = gpd.GeoDataFrame(
        pd.concat(
            frames,
            ignore_index=True,
        ),
        geometry="geometry",
        crs="EPSG:4326",
    )

    ca_op = (
        ca_op
        .drop_duplicates(
            subset=[
                "municipio_key"
            ]
        )
        .copy()
    )

    return ca_op


def join_clusters_with_geometry():
    """
    Relaciona o resultado do clustering
    às geometrias municipais.
    """

    if not DATA.exists():
        raise FileNotFoundError(
            "municipal_clusters.csv "
            "não encontrado.\n"
            "Execute primeiro:\n"
            "python cluster_analysis.py"
        )

    clusters = pd.read_csv(
        DATA
    )

    required_columns = {
        "Municipio",
        "Regiao",
        "Populacao",
        "Densidade",
        "Idosos",
        "Desemprego",
        "VariacaoPop",
        "EnsinoSuperior_por1000",
        "Cluster",
    }

    missing_columns = (
        required_columns
        .difference(
            clusters.columns
        )
    )

    if missing_columns:
        raise ValueError(
            "municipal_clusters.csv "
            "não contém as colunas necessárias: "
            + ", ".join(
                sorted(
                    missing_columns
                )
            )
        )

    clusters[
        "municipio_key"
    ] = (
        clusters[
            "Municipio"
        ]
        .map(
            normalize_name
        )
    )

    ca_op = load_caop()

    joined = ca_op.merge(
        clusters,
        on="municipio_key",
        how="inner",
        validate="one_to_one",
    )

    expected = len(
        clusters
    )

    found = len(
        joined
    )

    missing_names = sorted(
        set(
            clusters[
                "municipio_key"
            ]
        )
        -
        set(
            joined[
                "municipio_key"
            ]
        )
    )

    if (
        missing_names
        or found != expected
    ):
        raise ValueError(
            f"Join geoespacial incompleto: "
            f"{found}/{expected} municípios.\n"
            f"Não encontrados: "
            f"{missing_names}"
        )

    print(
        f"\nJoin concluído: "
        f"{found} municípios "
        f"com geometria."
    )

    return joined


def apply_bounds(ax, gdf, padding=0.08):
    """
    Ajusta o enquadramento de um GeoDataFrame
    adicionando margem proporcional.
    """

    if gdf.empty:
        return

    minx, miny, maxx, maxy = (
        gdf.total_bounds
    )

    width = maxx - minx
    height = maxy - miny

    if width == 0:
        width = 0.1

    if height == 0:
        height = 0.1

    ax.set_xlim(
        minx - width * padding,
        maxx + width * padding,
    )

    ax.set_ylim(
        miny - height * padding,
        maxy + height * padding,
    )


def plot_region(
    ax,
    gdf,
    title=None,
    show_labels=False,
):
    """
    Plota uma região usando cores explícitas
    por cluster.
    """

    if gdf.empty:
        ax.set_axis_off()
        return

    colors = [
        PALETTE.get(
            int(cluster),
            "#999999",
        )
        for cluster in gdf["Cluster"]
    ]

    gdf.plot(
        ax=ax,
        color=colors,
        edgecolor="white",
        linewidth=0.9,
    )

    apply_bounds(
        ax,
        gdf,
    )

    if title:
        ax.set_title(
            title,
            fontsize=12,
            fontweight="bold",
            pad=8,
        )

    if show_labels:

        for _, row in gdf.iterrows():

            point = (
                row.geometry
                .representative_point()
            )

            ax.annotate(
                row["Municipio"],
                xy=(
                    point.x,
                    point.y,
                ),
                xytext=(
                    3,
                    3,
                ),
                textcoords="offset points",
                fontsize=8,
            )

    ax.set_axis_off()


def save_static_map(gdf):
    """
    Gera mapa estático para apresentação no README.

    Layout:
    - Portugal Continental em destaque
    - Açores em inset
    - Madeira em inset
    - Legenda única para os clusters
    """

    IMAGES.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = (
        IMAGES
        / "clusters_geopandas.png"
    )

    mainland = gdf[
        ~gdf["Municipio"].isin(
            [
                "Funchal",
                "Ponta Delgada",
            ]
        )
    ].copy()

    azores = gdf[
        gdf["Municipio"]
        == "Ponta Delgada"
    ].copy()

    madeira = gdf[
        gdf["Municipio"]
        == "Funchal"
    ].copy()

    fig = plt.figure(
        figsize=(
            14,
            9,
        )
    )

    grid = fig.add_gridspec(
        nrows=2,
        ncols=4,
        width_ratios=[
            1,
            1,
            1,
            0.85,
        ],
        height_ratios=[
            1,
            1,
        ],
        wspace=0.05,
        hspace=0.20,
    )

    ax_main = fig.add_subplot(
        grid[
            :,
            :3,
        ]
    )

    ax_azores = fig.add_subplot(
        grid[
            0,
            3,
        ]
    )

    ax_madeira = fig.add_subplot(
        grid[
            1,
            3,
        ]
    )

    plot_region(
        ax_main,
        mainland,
    )

    plot_region(
        ax_azores,
        azores,
        title="Açores",
        show_labels=True,
    )

    plot_region(
        ax_madeira,
        madeira,
        title="Madeira",
        show_labels=True,
    )

    fig.suptitle(
        "Clusters de Desenvolvimento e Sustentabilidade",
        fontsize=18,
        fontweight="bold",
        y=0.97,
    )

    fig.text(
        0.5,
        0.925,
        "Análise de 25 Municípios Portugueses",
        ha="center",
        fontsize=12,
    )

    legend_elements = [
        Patch(
            facecolor=PALETTE[0],
            label="Cluster 0",
        ),
        Patch(
            facecolor=PALETTE[1],
            label="Cluster 1",
        ),
        Patch(
            facecolor=PALETTE[2],
            label="Cluster 2",
        ),
    ]

    fig.legend(
        handles=legend_elements,
        loc="lower center",
        ncol=3,
        frameon=False,
        fontsize=11,
        bbox_to_anchor=(
            0.5,
            0.02,
        ),
    )

    fig.text(
        0.5,
        0.005,
        "Fonte: PORDATA | Geometrias: CAOP2025 — Direção-Geral do Território",
        ha="center",
        fontsize=8,
    )

    fig.savefig(
        output,
        dpi=180,
        bbox_inches="tight",
        facecolor="white",
    )

    plt.close(
        fig
    )

    print(
        f"Mapa estático salvo em: "
        f"{output}"
    )


def popup_html(row):
    """
    Conteúdo exibido ao clicar
    em cada município no mapa Folium.
    """

    return f"""
    <div style="
        font-family: Arial;
        font-size: 13px;
        min-width: 230px;
    ">

        <h4 style="margin-bottom: 8px;">
            {row['Municipio']}
        </h4>

        <b>Cluster:</b>
        {int(row['Cluster'])}
        <br>

        <b>Região:</b>
        {row['Regiao']}
        <br>

        <b>População:</b>
        {row['Populacao']:,.0f}
        <br>

        <b>Densidade:</b>
        {row['Densidade']:.1f}
        <br>

        <b>Idosos:</b>
        {row['Idosos']:.1f}%
        <br>

        <b>Desemprego:</b>
        {row['Desemprego']:.1f}%
        <br>

        <b>Variação populacional:</b>
        {row['VariacaoPop']:.1f}%
        <br>

        <b>Ensino superior / 1000 hab.:</b>
        {row['EnsinoSuperior_por1000']:.1f}

    </div>
    """


def save_interactive_map(gdf):
    """
    Cria o mapa interativo utilizando Folium.
    """

    DOCS.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = (
        DOCS
        / "municipal_clusters_map.html"
    )

    fmap = folium.Map(
        location=[
            39.6,
            -8.0,
        ],
        zoom_start=6,
        tiles="CartoDB positron",
        control_scale=True,
    )

    clusters = sorted(
        gdf[
            "Cluster"
        ]
        .unique()
    )

    for cluster in clusters:

        group = folium.FeatureGroup(
            name=(
                f"Cluster "
                f"{int(cluster)}"
            ),
            show=True,
        )

        subset = gdf[
            gdf[
                "Cluster"
            ]
            == cluster
        ]

        for _, row in subset.iterrows():

            color = PALETTE.get(
                int(cluster),
                "#999999",
            )

            feature = folium.GeoJson(
                data=(
                    row.geometry
                    .__geo_interface__
                ),
                style_function=(
                    lambda _feature,
                    selected_color=color:
                    {
                        "fillColor":
                        selected_color,
                        "color":
                        "#ffffff",
                        "weight":
                        1.2,
                        "fillOpacity":
                        0.75,
                    }
                ),
                highlight_function=(
                    lambda _feature:
                    {
                        "weight":
                        3,
                        "color":
                        "#222222",
                        "fillOpacity":
                        0.9,
                    }
                ),
            )

            folium.Popup(
                popup_html(
                    row
                ),
                max_width=320,
            ).add_to(
                feature
            )

            folium.Tooltip(
                f"{row['Municipio']} "
                f"| Cluster "
                f"{int(row['Cluster'])}"
            ).add_to(
                feature
            )

            feature.add_to(
                group
            )

        group.add_to(
            fmap
        )

    folium.LayerControl(
        collapsed=False
    ).add_to(
        fmap
    )

    minx, miny, maxx, maxy = (
        gdf.total_bounds
    )

    fmap.fit_bounds(
        [
            [
                miny,
                minx,
            ],
            [
                maxy,
                maxx,
            ],
        ]
    )

    fmap.save(
        output
    )

    print(
        f"Mapa interativo salvo em: "
        f"{output}"
    )


def main():

    print(
        "Iniciando análise "
        "geoespacial..."
    )

    gdf = (
        join_clusters_with_geometry()
    )

    save_static_map(
        gdf
    )

    save_interactive_map(
        gdf
    )

    print(
        "\nAnálise geoespacial "
        "concluída com sucesso."
    )

    print(
        "\nArquivos gerados:"
    )

    print(
        " - images/"
        "clusters_geopandas.png"
    )

    print(
        " - docs/"
        "municipal_clusters_map.html"
    )


if __name__ == "__main__":
    main()
