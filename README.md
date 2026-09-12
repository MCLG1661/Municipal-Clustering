# <img width="400" height="400" alt="Municipal Clustering" src="https://github.com/user-attachments/assets/e7a233d9-2d11-4ee7-9ead-a234f366126d" />

# Sustentabilidade e Desenvolvimento nos Municípios Portugueses

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-blue)
![Scikit-learn](https://img.shields.io/badge/Scikit--learn-Machine%20Learning-orange)
![K-Means](https://img.shields.io/badge/Clustering-K--Means-green)
![GeoPandas](https://img.shields.io/badge/GeoPandas-Geospatial%20Analysis-139C5A)
![Folium](https://img.shields.io/badge/Folium-Interactive%20Maps-77B829)
![PORDATA](https://img.shields.io/badge/Dados-PORDATA-red)
![CAOP2025](https://img.shields.io/badge/Geodados-CAOP2025-005A9C)

Projeto de **Data Science** que combina análise multivariada, Machine Learning não supervisionado e análise geoespacial para estudar perfis de desenvolvimento e sustentabilidade em **25 municípios portugueses**.

O projeto nasceu como trabalho final do curso **Análise de Dados com Python**, do então Instituto Politécnico de Viana do Castelo (IPVC), atual Universidade Politécnica de Viana do Castelo, e foi posteriormente expandido com **GeoPandas e Folium** durante a evolução dos estudos em Data Science.

---

## 🎯 Pergunta de partida

Os municípios portugueses apresentam perfis homogéneos de desenvolvimento e sustentabilidade ou é possível identificar grupos com características distintas?

Além da segmentação estatística, a evolução geoespacial acrescenta uma segunda pergunta:

**Como esses perfis se distribuem espacialmente pelo território português?**

---

## 📊 Dataset

A base analítica utiliza arquivos municipais da **PORDATA** com dados de **2011, 2021 e 2024**.

Para a clusterização, o recorte principal é 2024, incorporando também a variação populacional entre 2011 e 2024.

Foram consolidados indicadores demográficos, socioeconómicos e ambientais.

A camada geográfica utiliza a **Carta Administrativa Oficial de Portugal — CAOP2025**, disponibilizada pela **Direção-Geral do Território (DGT)**.

As geometrias municipais são obtidas a partir dos **GeoPackages oficiais da CAOP2025**, contemplando:

- Portugal Continental;
- Região Autónoma dos Açores;
- Região Autónoma da Madeira.

Isso permite integrar geometrias oficiais aos resultados obtidos pelo modelo de clustering.

---

## 🔬 Metodologia

### Fase 1 — Data Science e Clustering

1. Extração e consolidação dos 25 arquivos Excel da PORDATA.
2. Validação dos dados.
3. Engenharia de variáveis.
4. Seleção de atributos evitando redundância direta.
5. Padronização com `StandardScaler`.
6. Teste de `k` entre 2 e 6 com coeficiente de silhueta.
7. Clusterização com `K-Means`.
8. Interpretação por perfis médios, ANOVA e PCA.

### Fase 2 — Análise Geoespacial

9. Obtenção das geometrias municipais oficiais da CAOP2025.
10. Leitura dos GeoPackages com GeoPandas.
11. Normalização dos nomes dos municípios.
12. Integração dos clusters com as geometrias.
13. Validação do join dos 25 municípios.
14. Criação de mapa estático com GeoPandas.
15. Desenvolvimento de mapa interativo com Folium.
16. Inclusão de tooltips, popups e camadas por cluster.

---

## 🧠 Variáveis utilizadas no modelo

As variáveis utilizadas na clusterização são:

- `Densidade`
- `Idosos`
- `Desemprego`
- `Residuos`
- `Energia`
- `VariacaoPop`
- `EnsinoSuperior_por1000`

A população absoluta foi excluída do modelo para reduzir o peso do porte do município sobre a segmentação.

---

## 🤖 Resultado do Clustering

A melhor solução encontrada entre `k = 2..6` foi:

**k = 3**

com coeficiente de silhueta de aproximadamente:

**0,291**

A separação encontrada é moderada e deve ser interpretada como uma **segmentação exploratória**, e não como uma classificação definitiva dos municípios.

### Cluster 0 — 18 municípios

Aveiro  
Beja  
Braga  
Bragança  
Castelo Branco  
Coimbra  
Faro  
Guarda  
Guimarães  
Leiria  
Portalegre  
Santarém  
Setúbal  
Viana do Castelo  
Vila Nova de Gaia  
Vila Real  
Viseu  
Évora

### Cluster 1 — 5 municípios

Almada  
Cascais  
Funchal  
Ponta Delgada  
Sintra

### Cluster 2 — 2 municípios

Lisboa  
Porto

---

## 📈 Visualizações do modelo

### Seleção do número de clusters

![Seleção de k](images/silhouette_k.png)

### Visualização dos clusters com PCA

![PCA dos clusters](images/pca_clusters.png)

---

## 🌍 Análise Geoespacial com GeoPandas

A evolução do projeto acrescenta uma **dimensão territorial** aos resultados obtidos pelo modelo de clustering.

Com **GeoPandas**, os resultados analíticos são associados às geometrias oficiais dos municípios portugueses fornecidas pela CAOP2025.

O processo transforma:

```text
Município + Indicadores + Cluster
```

em:

```text
Município + Indicadores + Cluster + Geometria
```

Isso permite analisar não apenas **quais municípios possuem características semelhantes**, mas também **como esses grupos estão distribuídos geograficamente**.

### Mapa estático dos clusters

O mapa estático apresenta os **23 municípios analisados em Portugal Continental**, permitindo visualizar territorialmente a distribuição dos três clusters.

**Funchal e Ponta Delgada**, pertencentes às regiões autónomas da Madeira e dos Açores, permanecem contemplados na análise completa e podem ser explorados no mapa interativo.

![Mapa estático dos clusters municipais](images/clusters_geopandas.png)

---

## 🗺️ Mapa Interativo com Folium

A segunda etapa da evolução geoespacial utiliza **Folium** para transformar os resultados em um mapa navegável e interativo.

Diferentemente da visualização estática, o mapa Folium contempla os **25 municípios analisados**, incluindo:

- Portugal Continental;
- Funchal — Madeira;
- Ponta Delgada — Açores.

Cada município pode ser explorado individualmente.

Ao selecionar uma geometria, o mapa apresenta informações como:

- Município;
- Cluster;
- Região;
- População;
- Densidade populacional;
- Percentual de idosos;
- Desemprego;
- Variação populacional;
- Ensino superior por 1.000 habitantes.

Também é possível ativar e desativar visualmente os diferentes clusters.

O arquivo interativo está disponível em:

[`docs/municipal_clusters_map.html`](docs/municipal_clusters_map.html)

---

## 🔄 Pipeline do Projeto

```text
PORDATA
   │
   ▼
Pandas
   │
   ▼
Tratamento e Engenharia de Variáveis
   │
   ▼
StandardScaler
   │
   ▼
K-Means
   │
   ├── Silhouette Score
   ├── ANOVA
   └── PCA
   │
   ▼
Clusters Municipais
   │
   ▼
CAOP2025
   │
   ▼
GeoPandas
   │
   ▼
Integração Dados + Geometria
   │
   ├── Mapa Estático
   │
   ▼
Folium
   │
   ▼
Mapa Interativo dos 25 Municípios
```

---

## 📁 Estrutura do Repositório

```text
Municipal-Clustering/
│
├── README.md
├── requirements.txt
│
├── build_dataset.py
├── cluster_analysis.py
├── geospatial_analysis.py
│
├── 01_pordata_municipal_clustering.ipynb
│
├── pordata_municipios_2024.csv
├── municipal_clusters.csv
│
├── *.xlsx
│
├── images/
│   ├── silhouette_k.png
│   ├── pca_clusters.png
│   └── clusters_geopandas.png
│
└── docs/
    ├── ANÁLISE CRÍTICA DOS RESULTADOS.docx
    ├── INFORMAÇÕES DO TRABALHO.docx
    └── municipal_clusters_map.html
```

> Os arquivos da CAOP2025 utilizados durante a execução são obtidos automaticamente pelo script geoespacial e armazenados localmente, não sendo necessários como arquivos permanentes do repositório.

---

## ⚙️ Como Executar

Clone o repositório:

```bash
git clone https://github.com/MCLG1661/Municipal-Clustering.git
cd Municipal-Clustering
```

Crie um ambiente virtual:

```bash
python -m venv .venv
```

### Windows — PowerShell

```bash
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

### 1. Reconstruir o dataset

Para reconstruir o dataset consolidado a partir dos arquivos Excel da PORDATA:

```bash
python build_dataset.py
```

O processo gera:

```text
pordata_municipios_2024.csv
```

### 2. Executar o clustering

```bash
python cluster_analysis.py
```

O processo gera:

```text
municipal_clusters.csv
```

Esse arquivo contém os indicadores municipais e o cluster atribuído pelo modelo.

### 3. Executar a análise geoespacial

```bash
python geospatial_analysis.py
```

Essa etapa:

```text
municipal_clusters.csv
          +
     CAOP2025
          │
          ▼
      GeoPandas
          │
          ├── Mapa Estático
          │
          ▼
        Folium
          │
          ▼
Mapa Interativo dos Clusters
```

e gera:

```text
images/clusters_geopandas.png
docs/municipal_clusters_map.html
```

A análise geoespacial requer conexão com a internet na primeira execução para obter os **GeoPackages oficiais da CAOP2025**.

---

## 🛠️ Tecnologias Utilizadas

### Data Analysis

- Python
- Pandas
- NumPy
- Jupyter

### Machine Learning

- Scikit-learn
- StandardScaler
- K-Means
- Silhouette Score
- PCA

### Estatística

- SciPy
- ANOVA

### Data Visualization

- Matplotlib

### Geospatial Data Science

- GeoPandas
- GeoDataFrame
- GeoPackage
- CAOP2025
- Sistemas de Referência de Coordenadas (CRS)

### Interactive Data Visualization

- Folium
- GeoJSON
- Tooltips
- Popups
- Feature Groups

---

## 📚 Fontes de Dados

### PORDATA

A **PORDATA — Base de Dados Portugal Contemporâneo** fornece os indicadores estatísticos municipais utilizados na análise.

Os dados utilizados no projeto abrangem **2011, 2021 e 2024**, com foco analítico principal em 2024.

### Direção-Geral do Território — DGT

A **CAOP2025 — Carta Administrativa Oficial de Portugal** fornece as geometrias administrativas oficiais utilizadas na análise geoespacial.

Para garantir a cobertura dos 25 municípios selecionados, o projeto utiliza as geometrias correspondentes a:

```text
Portugal Continental
Açores
Madeira
```

---

## 🚀 Evolução do Projeto

Este projeto foi desenvolvido de forma incremental, incorporando novas técnicas sobre uma base analítica já existente.

### Etapa original

**Análise de Dados com Python — IPVC**

Competências aplicadas:

```text
Python
Pandas
Análise Exploratória
Tratamento de Dados
Engenharia de Variáveis
K-Means
Silhouette Score
ANOVA
PCA
Interpretação de Clusters
```

### Evolução

**Avançando em Data Science com Python — Alura**

Novas competências incorporadas:

```text
GeoPandas
GeoDataFrame
GeoPackage
Dados Geoespaciais
Sistemas de Coordenadas
Integração Dados + Geometria
Visualização Cartográfica
Folium
Mapas Interativos
Tooltips
Popups
Camadas Geográficas
```

O projeto passa, portanto, de uma análise predominantemente estatística para uma abordagem que combina:

**Data Science + Machine Learning + Geospatial Analysis + Interactive Data Visualization**

---

## 💡 Competências Demonstradas

Este projeto demonstra conhecimentos em:

- análise exploratória de dados;
- tratamento e preparação de datasets;
- engenharia e seleção de variáveis;
- normalização de dados;
- Machine Learning não supervisionado;
- K-Means;
- avaliação de clusters;
- Silhouette Score;
- PCA;
- análise estatística;
- ANOVA;
- integração de dados tabulares e geográficos;
- GeoPandas;
- manipulação de GeoDataFrames;
- GeoPackage;
- sistemas de coordenadas;
- análise geoespacial;
- Folium;
- visualização cartográfica;
- mapas interativos;
- interpretação de dados orientada a problemas reais.

---

## 📌 Conclusão

Os resultados mostram que os municípios analisados apresentam **perfis distintos de desenvolvimento e sustentabilidade**, permitindo identificar grupos com características semelhantes.

A incorporação da análise geoespacial acrescenta uma nova dimensão ao estudo: além de identificar matematicamente os clusters, torna-se possível observar **como esses perfis se distribuem territorialmente**.

O mapa estático permite uma leitura imediata dos municípios analisados em Portugal Continental, enquanto o mapa interativo amplia a exploração para os **25 municípios**, incluindo Madeira e Açores.

Essa evolução demonstra como técnicas de Data Science podem integrar **estatística, Machine Learning, informação geográfica e visualização interativa** para produzir análises mais completas, exploráveis e interpretáveis.

---

## 👤 Autor

**Marcus Guedes**

Marketing | Data Science | Inteligência Artificial | Gestão de Projetos

- GitHub: [MCLG1661](https://github.com/MCLG1661)
- LinkedIn: [Marcus Guedes](https://www.linkedin.com/in/marcusguedes/)
