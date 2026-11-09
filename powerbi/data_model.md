# Power BI Star Schema Data Model Specification

## 1. Architectural Overview

The analytical data model for **Urban Road Accident Risk & Blackspot Analytics** is designed as a Kimball-style Star Schema, optimized for high performance, dynamic DAX time intelligence, slicing, cross-filtering, and drill-through capabilities.

```mermaid
erDiagram
    dim_date ||--o{ fact_collisions : "date_key (1 to Many)"
    dim_geography ||--o{ fact_collisions : "police_force (1 to Many)"
    fact_collisions ||--o{ fact_casualties : "collision_index (1 to Many)"
    fact_collisions ||--o{ fact_vehicles : "collision_index (1 to Many)"
    fact_collisions ||--o| dim_model_predictions : "collision_index (1 to 1)"
    dim_blackspots ||--o{ fact_collisions : "spatial proximity (Analytical Overlay)"

    dim_date {
        string date_key PK
        date date
        int year
        int month
        string month_name
        int day
        string day_name
        int day_of_week
        string quarter
        int is_weekend
        string season
    }

    dim_geography {
        int police_force PK
        string police_force_name
        string region
    }

    fact_collisions {
        string collision_index PK
        string date_key FK
        string collision_date
        int collision_year
        int month
        string month_name
        int day
        string day_name
        int day_of_week
        int is_weekend
        string collision_time
        int hour
        int is_rush_hour
        int is_night
        float latitude
        float longitude
        float easting
        float northing
        string grid_cell_1km
        int police_force FK
        int collision_severity
        string severity_name
        int severity_ksi
        int number_of_vehicles
        int number_of_casualties
        int speed_limit
        string road_type
        string light_conditions
        string weather_conditions
        string road_surface_conditions
        string junction_detail
        string urban_or_rural
        int has_motorcycle
        int has_pedal_cycle
        int has_goods_hgv
        int has_bus_coach
        int has_car
    }

    dim_blackspots {
        int cluster_id PK
        float center_latitude
        float center_longitude
        int total_collisions
        int fatal_count
        int serious_count
        int slight_count
        int ksi_count
        float ksi_rate_pct
        float severity_weighted_score
        int risk_rank
        string police_force_name
        string primary_road_type
        int speed_limit_mode
    }

    dim_model_predictions {
        string collision_index PK
        string collision_date
        int collision_year
        int police_force
        int speed_limit
        string road_type
        string severity_name
        int severity_ksi
        float predicted_probability_ksi
        int predicted_severity_ksi
        string predicted_severity_label
        int is_prediction_correct
    }
```

---

## 2. Table Dictionaries & Schema Definitions

### 1. `fact_collisions` (Central Fact Table)
- **Granularity**: One row per recorded collision in Great Britain.
- **Total Records**: 210,228 validated collisions (2022–2023).
- **Key Relationships**:
  - `date_key` -> `dim_date.date_key` (Many-to-One, Single cross-filter)
  - `police_force` -> `dim_geography.police_force` (Many-to-One, Single cross-filter)
  - `collision_index` -> `dim_model_predictions.collision_index` (One-to-One / Active)

### 2. `dim_date` (Conformed Date Dimension)
- **Granularity**: One row per calendar day (730 days spanning 2022-01-01 to 2023-12-31).
- **Attributes**: Calendar Year, Month, Month Name, Day of Month, Day Name, Day of Week, Quarter, Weekend Flag, Season.

### 3. `dim_geography` (Geographic Hierarchy)
- **Granularity**: One row per police force jurisdiction (53 territorial police forces).
- **Hierarchy**: `Region` -> `Police Force Name` -> `Collision Location`.

### 4. `dim_blackspots` (Geospatial Hazard Cluster Dimension)
- **Granularity**: One row per identified metric-space spatial cluster (DBSCAN eps=150m, min_samples=15).
- **Total Clusters**: 621 blackspots nationwide.
- **Attributes**: Cluster Centroid (Latitude/Longitude/Easting/Northing), Total 2-Year Collisions, Fatal Count, Serious Count, Slight Count, KSI Count, Severity-Weighted Hazard Score, Hazard Rank.

### 5. `dim_model_predictions` (Predictive Scoring Dimension)
- **Granularity**: One row per evaluated collision scored by the champion LightGBM model.
- **Attributes**: Ground Truth Severity, Predicted Probability of Severe Injury $P(\text{KSI})$, Binarized Decision Label (Optimal $t=0.61$), Prediction Correctness Flag.

---

## 3. Power Query M Transformations

The curated CSV datasets are directly ingested using the following Power Query parameters:

```powerquery
let
    Source = Csv.Document(File.Contents("data/processed/fact_collisions.csv"), [Delimiter=",", Columns=37, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"collision_index", type text},
        {"date_key", type date},
        {"collision_year", Int64.Type},
        {"hour", Int64.Type},
        {"latitude", type number},
        {"longitude", type number},
        {"collision_severity", Int64.Type},
        {"severity_ksi", Int64.Type},
        {"number_of_vehicles", Int64.Type},
        {"number_of_casualties", Int64.Type},
        {"speed_limit", Int64.Type}
    })
in
    #"Changed Type"
```

