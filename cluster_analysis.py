"""
Clusterização dos municípios com K-Means.

A seleção de variáveis evita redundância direta entre proporções etárias
(Jovens + IdadeAtiva + Idosos ≈ 100%) e exclui população absoluta para
reduzir o peso do porte municipal na segmentação.
"""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
from scipy.stats import f_oneway

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "pordata_municipios_2024.csv"

FEATURES = [
    "Densidade",
    "Idosos",
    "Desemprego",
    "Residuos",
    "Energia",
    "VariacaoPop",
    "EnsinoSuperior_por1000",
]

df = pd.read_csv(DATA)
X = df[FEATURES].copy()

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

print("Silhueta por k:")
scores = {}
for k in range(2, 7):
    model = KMeans(n_clusters=k, random_state=42, n_init=100)
    labels = model.fit_predict(X_scaled)
    score = silhouette_score(X_scaled, labels)
    scores[k] = score
    print(f"k={k}: {score:.3f}")

k_final = max(scores, key=scores.get)
model = KMeans(n_clusters=k_final, random_state=42, n_init=100)
df["Cluster"] = model.fit_predict(X_scaled)

print(f"\nK selecionado: {k_final}")
print(df[["Municipio", "Cluster"]].sort_values(["Cluster", "Municipio"]).to_string(index=False))

print("\nANOVA por variável:")
for feature in FEATURES:
    groups = [df.loc[df["Cluster"] == c, feature].values for c in sorted(df["Cluster"].unique())]
    _, p = f_oneway(*groups)
    print(f"{feature}: p={p:.4f}")

pca = PCA(n_components=2)
coords = pca.fit_transform(X_scaled)
print(f"\nVariância explicada por PC1+PC2: {pca.explained_variance_ratio_.sum():.1%}")
