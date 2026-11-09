# Power BI Implementation, Data Modeling & Refresh Guide
### Urban Road Accident Risk & Blackspot Analytics

This guide provides end-to-end instructions for deploying, modeling, and interacting with the 5-page Power BI Dashboard using Power BI Desktop.

---

## 1. Curated Analytical Datasets

The curated analytical tables are pre-processed and ready for 1-click import located in `data/processed/`:

| Table Name | Source File | Description | Total Rows |
| :--- | :--- | :--- | :---: |
| **`fact_collisions`** | `fact_collisions.csv` | Central collision event table with environmental, fleet, and severity flags | 210,228 |
| **`dim_date`** | `dim_date.csv` | Conformed calendar dimension with day/month/season/weekend flags | 730 |
| **`dim_geography`** | `dim_geography.csv` | Territorial police forces and regional macro groupings | 53 |
| **`dim_blackspots`** | `dim_blackspots.csv` | Spatial hazard clusters (DBSCAN eps=150m) with severity-weighted scores | 621 |
| **`dim_model_predictions`** | `dim_model_predictions.csv` | Pre-crash ML severity predictions and classification flags | 50,000+ |
| **`fact_casualties`** | `fact_casualties_sample.csv` | Casualty-level demographics, road user classes, and injury severity | 100,000 |
| **`fact_vehicles`** | `fact_vehicles_sample.csv` | Vehicle-level fleet classifications and first impact point dynamics | 100,000 |

---

## 2. Power BI Desktop Setup & Ingestion Steps

### Step 1: Open Power BI Desktop & Load Data
1. Launch **Power BI Desktop**.
2. Click **Get Data** -> **Text/CSV**.
3. Select and import each table from the `data/processed/` directory.
4. Click **Transform Data** to open Power Query Editor.

### Step 2: Power Query Data Types & Validations
Ensure the following key column types are assigned:
- In `fact_collisions`:
  - `date_key`: Date
  - `latitude`, `longitude`, `easting`, `northing`: Decimal Number / Float (Set Data Category to Latitude / Longitude)
  - `collision_severity`, `severity_ksi`, `speed_limit`, `hour`: Whole Number
- In `dim_date`:
  - `date_key`, `date`: Date
  - Mark as official **Date Table** in Power BI (`Table tools` -> `Mark as Date Table` -> Select `date`).

### Step 3: Establish Star Schema Relationships
In the **Model View**, establish the following 1-to-Many relationships:
1. `dim_date[date_key]` (1) ───> `fact_collisions[date_key]` (*) [Single cross-filter]
2. `dim_geography[police_force]` (1) ───> `fact_collisions[police_force]` (*) [Single cross-filter]
3. `fact_collisions[collision_index]` (1) ───> `dim_model_predictions[collision_index]` (1) [Both cross-filter]

---

## 3. DAX Measures Installation

Create a dedicated empty table named `_Measures`:
1. Click **Enter Data**, name the table `_Measures`, and click **Load**.
2. Copy and paste the 25+ DAX measures defined in [`powerbi/dax_measures.md`](dax_measures.md).

Key Core KPIs include:
- `Total Collisions = COUNTROWS(fact_collisions)`
- `KSI Collisions = CALCULATE(COUNTROWS(fact_collisions), fact_collisions[severity_ksi] = 1)`
- `KSI Rate % = DIVIDE([KSI Collisions], [Total Collisions], 0)`
- `YoY Collision Change % = DIVIDE([Total Collisions] - [Collisions Prior Year], [Collisions Prior Year], 0)`
- `Rush Hour Ratio % = DIVIDE([Rush Hour Collisions], [Total Collisions], 0)`

---

## 4. Five Core Dashboard Pages & Visual Layout

### Page 1: Executive Overview (`page1_executive_overview.png`)
- **Top Slicers**: Calendar Year (2022, 2023), Region, Severity Class.
- **KPI Cards**: Total Collisions (`210,228`), Severe Collisions KSI (`49,885`), Total Casualties (`268,421`), YoY Volume Trend (`-1.65%`).
- **Main Visual (Area/Line)**: Monthly Collision Trajectory comparing 2022 vs 2023.
- **Donut Chart**: 3-Class Severity Breakdown (Slight 76.3%, Serious 22.2%, Fatal 1.5%).
- **Bar Chart**: Regional Collision Volumes (London, South East, Yorkshire & Humber, etc.).
- **Bar Chart**: Severe Injury (KSI) Rate (%) by Posted Speed Limit (20 to 70 mph).

### Page 2: Temporal Analysis (`page2_temporal_analysis.png`)
- **KPI Cards**: Rush Hour Collisions (`64,528`), Peak Incident Hour (`17:00–18:00`), Weekend Crashes (`54,120`), Night-to-Day Risk Ratio (`1.45x`).
- **Line Chart**: 24-Hour Diurnal Volume Curve highlighting Morning (07-09) and Evening (16-18) peaks.
- **Matrix / Heatmap**: 2D Incident Density across Hour of Day x Day of Week.
- **Line Chart**: Hourly KSI Rate (%) showing severe crash elevation during late-night hours (30-32%).
- **Column Chart**: Seasonal Collision Distribution (Autumn peak vs Spring trough).

### Page 3: Geospatial Blackspot Analysis (`page3_geospatial_blackspots.png`)
- **KPI Cards**: Total Identified Blackspots (`621`), Max Hazard Score (`889.0`), Clustered Incidents (`22,808`), Temporal Stability P@20 (`75.0%`).
- **Map Visual (Bubble Map / Shape Map)**: Latitude & Longitude centroids sized by collision volume, colored by `severity_weighted_score`.
- **Top 10 Hazard Table**: Ranked Corridors showing Police Force, Crash Count, Fatal, Serious, and Severity Score.
- **Filter**: Speed Limit Slicer and Road Geometry Slicer.

### Page 4: Accident Severity & Contributing Factors (`page4_severity_factors.png`)
- **KPI Cards**: National KSI Baseline (`23.7%`), Motorcycle KSI Rate (`40.3%`), Rural Road KSI Rate (`31.9%`), Unlit Darkness KSI Rate (`33.7%`).
- **Horizontal Bar Charts**: Severe Injury Rate (%) by Lighting Conditions and Road Surface Friction.
- **Column Chart**: Vulnerable Road User (VRU) Disparity (Motorcycles, Pedal Cycles, HGVs vs Passenger Cars).
- **Column Chart**: Road Geometry Classification (Single vs Dual Carriageway vs Roundabouts).

### Page 5: Predictive Analytics & Risk Insights (`page5_predictive_risk.png`)
- **KPI Cards**: Temporal Holdout ROC-AUC (`0.698`), Optimal Macro F1 (`0.617`), KSI Recall @ Optimal (`37.6%`), Spatial Generalization ROC-AUC (`0.670`).
- **Model Comparison Bar Chart**: Baseline vs Logistic Regression vs Random Forest vs XGBoost vs LightGBM.
- **Horizontal Bar Chart**: Top SHAP Feature Importances (Historical Spatial Base Rate, Fleet Size, Motorcycle Involvement, Speed Limit).
- **Heatmap**: Normalized Confusion Matrix on unseen 2023 holdout.
- **Generalization Gap Bar Chart**: In-Distribution Temporal Performance vs Unseen Jurisdiction (West Midlands).

---

## 5. Dataset Refresh & Maintenance

To refresh data when new annual releases (e.g. 2024+) are ingested:
1. Run `python scripts/01_build_pipeline.py` to process new raw CSVs.
2. In Power BI Desktop, click **Home** -> **Refresh**.
3. All star schema relationships, DAX calculations, and report pages automatically update with zero schema changes.

