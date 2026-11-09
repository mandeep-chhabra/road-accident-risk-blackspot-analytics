# Quantitative Evidence & Reproducibility Verification Table

This table maps every metric claimed in project reports, resume bullets, and technical presentations to its exact measured value, underlying mathematical formula, evaluation split, and generating script/artifact.

| Domain | Claimed Metric | Measured Value | Mathematical Formula / Definition | Evaluation Split / Scope | Generating Artifact & Script |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **Data Engineering** | Raw Multi-Table Records | **862,079 records** | $N_{col} + N_{cas} + N_{veh} = 210,262 + 268,457 + 383,360$ | Great Britain (2022–2023) | `reports/data_quality_report.json` via `scripts/01_build_pipeline.py` |
| **Data Engineering** | Clean Validated Collisions | **210,228 records** | Bounding box: $49.8 \le \text{lat} \le 60.9, -8.5 \le \text{lon} \le 2.0$ | Great Britain (2-year longitudinal) | `data/processed/fact_collisions.parquet` |
| **Data Engineering** | Invalid Coordinates Dropped | **34 collisions** (0.016%) | Rows with null or out-of-bounds latitude/longitude | Raw 2022–2023 collisions | `reports/data_quality_report.json` |
| **Statistical Analysis** | National Severe Injury (KSI) Rate | **23.73%** | $P_{KSI} = \frac{N_{fatal} + N_{serious}}{N_{total}} = \frac{49,885}{210,228}$ | National (2022–2023) | `reports/statistical_analysis_report.json` via `scripts/02_run_eda_and_stats.py` |
| **Statistical Analysis** | 95% Wilson Score CI for KSI | **[23.55%, 23.91%]** | $\frac{\hat{p} + \frac{z^2}{2n} \pm z\sqrt{\frac{\hat{p}(1-\hat{p})}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}}, z=1.96$ | National (N = 210,228) | `reports/statistical_findings.md` |
| **Statistical Analysis** | Speed Limit Association ($\chi^2$) | **$\chi^2 = 3,678.9$** ($p < 10^{-300}$) | Pearson's Chi-Square Test of Independence with Cramér's $V = 0.0934$ | Substantive categories (N = 210,228) | `reports/statistical_analysis_report.json` |
| **Statistical Analysis** | Urban vs Rural Odds Ratio | **1.77x Severe Odds** | $\frac{P_{rural}/(1-P_{rural})}{P_{urban}/(1-P_{urban})} = \frac{0.319 / 0.681}{0.210 / 0.790}$ | Rural (N = 43,842) vs Urban (N = 166,386) | `reports/statistical_findings.md` |
| **Statistical Analysis** | Motorcycle KSI Disparity | **40.29% KSI Rate** | $\chi^2 = 1,765.1$ ($p < 10^{-300}$), Cramér's $V = 0.0916$ | Motorcycle-involved collisions ($N=34,708$) | `reports/statistical_findings.md` |
| **Geospatial Analytics** | Identified Spatial Blackspots | **621 clusters** | Metric-space DBSCAN: $\epsilon = 150\text{m}$, $\text{MinPts} = 15$ | Nationwide British National Grid (EPSG:27700) | `reports/spatial_validation.json` via `scripts/03_run_geospatial_analytics.py` |
| **Geospatial Analytics** | Clustered Collision Share | **22,808 collisions** (10.85%) | Collisions with $\text{cluster\_id} \ne -1$ | Nationwide (2022–2023) | `data/processed/dim_blackspots.csv` |
| **Geospatial Analytics** | Peak Hazard Cluster Score | **889.0 Index Points** | $Score = 10 \cdot N_{fatal} + 3 \cdot N_{serious} + 1 \cdot N_{slight}$ | Cluster #1 (Metropolitan Police Corridor) | `data/road_safety.db:analytical_blackspots` |
| **Geospatial Analytics** | Hotspot Temporal Stability | **Precision@20 = 75.0%** | $\frac{\text{Count of Top-20 2022 Clusters with 2023 Match} \le 250\text{m}}{20}$ | 2022 clusters vs 2023 independent clusters | `reports/spatial_validation.json` |
| **Geospatial Analytics** | Hotspot Stability (Top 100) | **Precision@100 = 72.0%** | $\frac{\text{Count of Top-100 2022 Clusters with 2023 Match} \le 250\text{m}}{100}$ | 2022 vs 2023 annual recurrence | `reports/spatial_validation.json` |
| **Geospatial Analytics** | Getis-Ord $G_i^*$ Hotspot Cells | **4,215 cells** (9.24%) | $z \ge 1.96$ ($p < 0.05$) local spatial concentration | 45,635 1km BNG grid cells | `reports/spatial_validation.json` |
| **Machine Learning** | Temporal Generalization ROC-AUC | **0.6981** | Area Under ROC Curve (LightGBM champion) | 2023 Chronological Holdout ($N=99,558$) | `reports/final_evaluation.json` via `scripts/04_train_and_evaluate_models.py` |
| **Machine Learning** | Temporal Generalization PR-AUC | **0.4263** | Average Precision (Baseline prevalence = 0.2409) | 2023 Chronological Holdout | `reports/final_evaluation.json` |
| **Machine Learning** | Optimal Macro F1 Score | **0.6172** | Macro-averaged F1 at tuned decision threshold $t = 0.61$ | 2023 Chronological Holdout | `reports/model_comparison.csv` |
| **Machine Learning** | Severe Class (KSI) Recall | **37.63%** (Precision = 43.97%) | $\frac{TP}{TP + FN}$ for severe collision class | 2023 Chronological Holdout ($t = 0.61$) | `reports/final_evaluation.json` |
| **Machine Learning** | Spatial Generalization ROC-AUC | **0.6702** | ROC-AUC evaluated on unseen geography (West Midlands) | 2023 Geographic Holdout ($N=4,688$) | `reports/final_evaluation.json` |
| **SQL Analytics** | Analytical Queries Executed | **12 / 12 queries** | CTEs, Window functions (`DENSE_RANK`, `LAG`, `AVG OVER`), Joins | Relational SQLite database (`data/road_safety.db`) | `sql/analytical_queries.sql` via `scripts/05_run_sql_analytics.py` |
| **Power BI** | Report Architecture | **5 interactive pages** | Executive Overview, Temporal, Geospatial, Severity, Predictive | Power BI Desktop star schema | `powerbi/README.md`, `powerbi/screenshots/` |
| **Power BI** | DAX Measures Library | **26 DAX measures** | Core KPIs, Time Intelligence, Operational Ratios, Model Scored | Power BI Desktop model | `powerbi/dax_measures.md` |

