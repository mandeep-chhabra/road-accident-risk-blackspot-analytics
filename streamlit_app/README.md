# Streamlit Analytics Dashboard
### Urban Road Accident Risk & Blackspot Analytics

The **Streamlit Analytics Dashboard** serves as the unified interactive web interface for the entire Data Science and Business Intelligence project. It consolidates exploratory data analysis, inferential statistics, GIS blackspot exploration, machine learning model evaluation, SHAP explainability, SQL analytics, and Power BI report functionality into an enterprise-grade multi-page web application.

---

## 1. Quick Start Guide

### Launching the Dashboard
Execute the following command from the repository root:

```bash
streamlit run streamlit_app/app.py
```

The application will start at `http://localhost:8501`.

---

## 2. Dashboard Architecture & 8 Dedicated Modules

```text
streamlit_app/
│
├── app.py                         # Master application router & global sidebar filters
│
├── views/                         # 8 Feature Modules
│   ├── page1_executive_overview.py   # Page 1: Macro KPIs, longitudinal trends & regional rankings
│   ├── page2_temporal_analytics.py   # Page 2: Diurnal curves, 2D day x hour heatmaps & rush-hour surges
│   ├── page3_statistical_analysis.py # Page 3: 12 Chi-square tests, Wilson 95% CIs & FDR adjustments
│   ├── page4_geospatial_explorer.py  # Page 4: DBSCAN blackspots, CARTO basemap maps & stability validation
│   ├── page5_predictive_analytics.py # Page 5: Model benchmark, spatial holdout gap & live prediction simulator
│   ├── page6_sql_explorer.py         # Page 6: Safe read-only execution of 12 production queries + console
│   ├── page7_powerbi_consolidation.py# Page 7: Functional replication of 5 Power BI pages & 26 DAX measures
│   └── page8_data_quality.py         # Page 8: Ingestion funnel, missing values & coordinate boundary audit
│
├── components/
│   ├── kpi_cards.py               # Reusable styled metric cards with deltas
│   ├── charts.py                  # Standardized Plotly visualizations with canonical severity palette
│   ├── tables.py                  # Interactive DataFrames with sorting & instant CSV download
│   ├── maps.py                    # Folium & Plotly map renderers with CARTO API key integration
│   └── filters.py                 # Multi-criteria global sidebar filters
│
├── services/
│   ├── data_loader.py             # Memory-cached (st.cache_data) Parquet & JSON loaders
│   ├── database_service.py        # Safe read-only SQLite execution with injection protection
│   ├── analytics_service.py       # High-speed in-memory filtering & dynamic narrative generation
│   └── ml_service.py              # Cached model pipeline & real-time inference engine
│
├── utils/
│   ├── constants.py               # Severity colors, file paths, CARTO API key
│   └── formatting.py              # Number formatting & percentage strings
│
└── assets/
    └── custom.css                 # Enterprise typography, cards, badges & dark slate header
```

---

## 3. Implemented Capabilities by Page

### Page 1: Executive Overview
- **Verified KPI Cards**: Total Valid Collisions (`210,228`), Total Casualties (`268,421`), Fatal (`3,124`), Serious (`46,761`), Slight (`160,343`), National KSI Rate (`23.73%`), Identified Blackspots (`621`), Clustered Volume (`22,808`).
- **Visualizations**: Monthly trajectory (2022 vs 2023), 3-class severity split donut, longitudinal stacked severity trends, regional collision rankings, urban vs rural distribution, and top 10 police forces by volume.
- **Dynamic Narrative**: Auto-generated 2-sentence analytical summary based on current filter selections.

### Page 2: Temporal Analytics
- **Visualizations**: 24-hour diurnal volume curve vs KSI severity rate line, 2D Hour x Day heatmap matrix, weekday vs weekend daily average curves, hourly KSI rate curve showing late-night severity surge (31.9% peak), day-of-week KSI breakdown, and seasonal accident distribution.
- **Interactive Controls**: Hour range slider, day-of-week selector, and rush-hour toggle.

### Page 3: Statistical Analysis & Hypothesis Testing
- **Proportion Estimates**: Fatal (1.49% [1.44%, 1.54%]), Serious (22.24% [22.07%, 22.42%]), Slight (76.27%), Combined KSI (23.73% [23.55%, 23.91%]) with Wilson Score error bars.
- **12 Chi-Square Tests**: Full interactive results table with test statistics, raw p-values, Benjamini-Hochberg FDR adjusted p-values, Cramér's V effect sizes, and qualitative association strengths.
- **Non-Parametric Tests**: Kruskal-Wallis on casualties across severity, Mann-Whitney U for vehicles, and Mann-Whitney U for speeds.

### Page 4: Geospatial Analytics & Blackspot Explorer
- **Interactive Folium Map**: Powered by the user's **CARTO Basemaps API Key** (`Voyager` and `Positron` tiles) featuring 621 cluster centroids, severity-weighted popups, and kernel density heatmap.
- **Ranked Corridor Directory**: Ranked table of top 10, 20, 50, or all 621 blackspots with instant CSV download.
- **Longitudinal Stability**: Visualizes 2-year recurrence rates (Precision@10 = 70.0%, Precision@20 = 75.0%, Precision@50 = 72.0%, Precision@100 = 72.0% within a 250m buffer).
- **Getis-Ord $G_i^*$ Analysis**: Summary of 4,215 statistically significant hotspot cells out of 45,635 1km cells.

### Page 5: Predictive Machine Learning Analytics
- **Model Benchmark**: Comparison table & grouped bar chart (Baseline, Logistic Regression, Random Forest, XGBoost, LightGBM) across ROC-AUC, PR-AUC, Balanced Accuracy, Macro F1, and KSI Recall.
- **Generalization Gap**: Bar chart and technical breakdown comparing Temporal Holdout (0.698 ROC-AUC, 0.617 Macro F1) vs Spatial Holdout (0.670 ROC-AUC, 0.537 Macro F1).
- **SHAP Explainability**: Global feature importance horizontal bar chart, display of saved SHAP beeswarm summary plot, and local high/low risk waterfall explanations.
- **Threshold Explorer**: Interactive slider adjusting classification threshold $t \in [0.15, 0.85]$, dynamically recalculating Precision, Recall, F1, and confusion matrix.
- **Live Prediction Simulator**: Form interface allowing users to adjust pre-crash factors and obtain real-time probability $P(\text{KSI})$, binary classification, and risk level gauge using the trained LightGBM pipeline.

### Page 6: SQL Analytics Explorer
- **Predefined Queries**: 12 production SQL queries with syntax-highlighted previews, one-click execution on `data/road_safety.db`, execution timers, and CSV export.
- **Custom Console**: Read-only SQL console protected by security filters blocking destructive statements (`DROP`, `DELETE`, `INSERT`, `UPDATE`).
- **Schema Inspector**: Database browser detailing table record counts and column data types.

### Page 7: Power BI Dashboard Consolidation
- **Functional Consolidation**: Full interactive replication of all 5 Power BI report pages (Executive Overview, Temporal, Blackspots, Severity Factors, Predictive Risk).
- **DAX Suite Reference**: Complete markdown documentation of all 26 verified DAX measures.
- **Screenshot Gallery**: High-resolution previews of the generated Power BI Desktop report pages.

### Page 8: Data Quality & Pipeline Monitoring
- **Ingestion & Validation Yield**: Raw vs processed records across Collisions, Casualties, and Vehicles.
- **Coordinate Boundary Audit**: Validation against the British geographic bounding box ($49.8^\circ \le \text{lat} \le 60.9^\circ$, $-8.5^\circ \le \text{lon} \le 2.0^\circ$) with an audit of the 34 dropped records.
- **Schema Dictionary**: Column-level data types, missing value counts, and feature completeness percentages.

---

## 4. Performance & Caching Strategy
- **`st.cache_data`**: The 86 MB Parquet fact table loads into memory once (in ~0.25 seconds) and is reused across all exploratory filters and page switches.
- **`st.cache_resource`**: Database connections and machine learning models are cached as shared singletons.
- **Lazy Rendering**: Expensive maps and plots render on demand within tabs to maintain fluid UI responsiveness.

