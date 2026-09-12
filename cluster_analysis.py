from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import f_oneway
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "pordata_municipios_2024.csv"
OUTPUT = ROOT / "municipal_clusters.csv"
IMAGES = ROOT / "images"

FEATURES = [
    "Densidade",
    "Idosos",
    "Desemprego",
    "Residuos",
    "Energia",
    "VariacaoPop",
    "EnsinoSuperior_por1000",
]


def load_data():
    if not DATA.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {DATA.name}. "
            "Execute primeiro o build_dataset.py ou confirme se o CSV está na raiz."
        )

    df = pd.read_csv(DATA)

    required = {"Municipio", "Regiao", *FEATURES}
    missing = required.difference(df.columns)

    if missing:
        raise ValueError(
            "O dataset não contém todas as colunas necessárias: "
            + ", ".join(sorted(missing))
        )

    if df[FEATURES].isna().any().any():
        raise ValueError(
            "Existem valores ausentes nas variáveis utilizadas no clustering."
        )

    return df


def evaluate_k(x_scaled):
    results = []

    for k in range(2, 7):
        model = KMeans(
            n_clusters=k,
            random_state=42,
            n_init=100,
        )

        labels = model.fit_predict(x_scaled)

        results.append(
            {
                "k": k,
                "silhouette": silhouette_score(x_scaled, labels),
                "inertia": model.inertia_,
            }
        )

    return pd.DataFrame(results)


def save_silhouette_chart(scores):
    IMAGES.mkdir(exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.plot(
        scores["k"],
        scores["silhouette"],
        marker="o",
    )

    ax.set_title("Coeficiente de Silhueta por número de clusters")
    ax.set_xlabel("Número de clusters (k)")
    ax.set_ylabel("Silhouette Score")
    ax.set_xticks(scores["k"])
    ax.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(
        IMAGES / "silhouette_k.png",
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(fig)


def perform_clustering(df, x_scaled, best_k):
    model = KMeans(
        n_clusters=best_k,
        random_state=42,
        n_init=100,
    )

    df = df.copy()
    df["Cluster"] = model.fit_predict(x_scaled)

    return df, model


def run_anova(df):
    print("\nANOVA por variável:")

    for feature in FEATURES:
        groups = [
            group[feature].values
            for _, group in df.groupby("Cluster")
        ]

        result = f_oneway(*groups)

        print(
            f"{feature}: "
            f"F={result.statistic:.3f} | "
            f"p={result.pvalue:.5f}"
        )


def save_pca_chart(df, x_scaled):
    IMAGES.mkdir(exist_ok=True)

    pca = PCA(n_components=2)
    components = pca.fit_transform(x_scaled)

    pca_df = pd.DataFrame(
        components,
        columns=["PC1", "PC2"],
    )

    pca_df["Cluster"] = df["Cluster"].values
    pca_df["Municipio"] = df["Municipio"].values

    fig, ax = plt.subplots(figsize=(10, 7))

    scatter = ax.scatter(
        pca_df["PC1"],
        pca_df["PC2"],
        c=pca_df["Cluster"],
        cmap="Set2",
        s=80,
        edgecolor="black",
        linewidth=0.5,
    )

    for _, row in pca_df.iterrows():
        ax.annotate(
            row["Municipio"],
            (row["PC1"], row["PC2"]),
            xytext=(5, 4),
            textcoords="offset points",
            fontsize=8,
        )

    ax.set_title("Visualização dos clusters com PCA")
    ax.set_xlabel(
        f"PC1 ({pca.explained_variance_ratio_[0] * 100:.1f}% da variância)"
    )
    ax.set_ylabel(
        f"PC2 ({pca.explained_variance_ratio_[1] * 100:.1f}% da variância)"
    )

    legend = ax.legend(
        *scatter.legend_elements(),
        title="Cluster",
    )

    ax.add_artist(legend)
    ax.grid(alpha=0.25)

    fig.tight_layout()
    fig.savefig(
        IMAGES / "pca_clusters.png",
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(fig)


def print_cluster_summary(df):
    print("\nMunicípios por cluster:")

    for cluster, group in df.groupby("Cluster"):
        municipalities = sorted(group["Municipio"].tolist())

        print(f"\nCluster {cluster} — {len(municipalities)} municípios")

        for municipality in municipalities:
            print(f" - {municipality}")

    print("\nMédias das variáveis por cluster:")
    print(
        df.groupby("Cluster")[FEATURES]
        .mean()
        .round(2)
        .to_string()
    )


def save_results(df):
    df.to_csv(
        OUTPUT,
        index=False,
        encoding="utf-8",
    )

    print(f"\nArquivo salvo: {OUTPUT.name}")


def main():
    df = load_data()

    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(df[FEATURES])

    scores = evaluate_k(x_scaled)
    save_silhouette_chart(scores)

    print("Avaliação de k:")
    print(scores.round(4).to_string(index=False))

    best_row = scores.loc[scores["silhouette"].idxmax()]
    best_k = int(best_row["k"])
    best_score = float(best_row["silhouette"])

    print(
        f"\nMelhor solução: k={best_k} "
        f"| silhouette={best_score:.3f}"
    )

    df_clustered, _ = perform_clustering(
        df,
        x_scaled,
        best_k,
    )

    run_anova(df_clustered)
    save_pca_chart(df_clustered, x_scaled)
    print_cluster_summary(df_clustered)
    save_results(df_clustered)

    print("\nClustering concluído com sucesso.")


if __name__ == "__main__":
    main()
