-- ==============================================================================
-- Urban Road Accident Risk & Blackspot Analytics
-- Production-Grade Analytical SQL Suite for SQLite / PostgreSQL
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 1: Monthly Accident Trends and YoY Growth Rate
-- Uses CTEs, Window Functions (LAG), Date Parsing, and YoY Percentage Change.
-- ------------------------------------------------------------------------------
WITH monthly_summary AS (
    SELECT 
        d.year,
        d.month,
        d.month_name,
        COUNT(c.collision_index) AS total_collisions,
        SUM(c.severity_ksi) AS ksi_collisions,
        ROUND(CAST(SUM(c.severity_ksi) AS REAL) / COUNT(c.collision_index) * 100, 2) AS ksi_rate_pct
    FROM fact_collisions c
    JOIN dim_date d ON c.date_key = d.date_key
    GROUP BY d.year, d.month, d.month_name
),
monthly_lagged AS (
    SELECT 
        year,
        month,
        month_name,
        total_collisions,
        ksi_collisions,
        ksi_rate_pct,
        LAG(total_collisions, 12) OVER (ORDER BY year, month) AS prior_year_collisions,
        LAG(ksi_collisions, 12) OVER (ORDER BY year, month) AS prior_year_ksi
    FROM monthly_summary
)
SELECT 
    year,
    month,
    month_name,
    total_collisions,
    prior_year_collisions,
    CASE 
        WHEN prior_year_collisions IS NOT NULL AND prior_year_collisions > 0
        THEN ROUND((CAST(total_collisions - prior_year_collisions AS REAL) / prior_year_collisions) * 100, 2)
        ELSE NULL 
    END AS yoy_growth_pct,
    ksi_collisions,
    ksi_rate_pct
FROM monthly_lagged
ORDER BY year, month;


-- ------------------------------------------------------------------------------
-- Query 2: Area-Level Severity Ranking & DENSE_RANK() by Police Force
-- Evaluates total collisions, fatal, serious, and KSI rate with window rankings.
-- ------------------------------------------------------------------------------
WITH area_metrics AS (
    SELECT 
        g.police_force,
        g.police_force_name,
        g.region,
        COUNT(c.collision_index) AS total_collisions,
        SUM(CASE WHEN c.collision_severity = 1 THEN 1 ELSE 0 END) AS fatal_count,
        SUM(CASE WHEN c.collision_severity = 2 THEN 1 ELSE 0 END) AS serious_count,
        SUM(c.severity_ksi) AS ksi_total,
        ROUND(CAST(SUM(c.severity_ksi) AS REAL) / COUNT(c.collision_index) * 100, 2) AS ksi_rate_pct
    FROM fact_collisions c
    JOIN dim_geography g ON c.police_force = g.police_force
    GROUP BY g.police_force, g.police_force_name, g.region
    HAVING COUNT(c.collision_index) >= 1000
)
SELECT 
    police_force,
    police_force_name,
    region,
    total_collisions,
    fatal_count,
    serious_count,
    ksi_total,
    ksi_rate_pct,
    DENSE_RANK() OVER (ORDER BY total_collisions DESC) AS volume_rank,
    DENSE_RANK() OVER (ORDER BY ksi_rate_pct DESC) AS severity_risk_rank
FROM area_metrics
ORDER BY volume_rank ASC
LIMIT 15;


-- ------------------------------------------------------------------------------
-- Query 3: Hourly Accident Density & Rolling 3-Hour Moving Average
-- Window function: AVG() OVER (ORDER BY hour ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING)
-- ------------------------------------------------------------------------------
WITH hourly_stats AS (
    SELECT 
        hour,
        is_rush_hour,
        COUNT(collision_index) AS collisions_count,
        SUM(severity_ksi) AS ksi_count,
        ROUND(CAST(SUM(severity_ksi) AS REAL) / COUNT(collision_index) * 100, 2) AS ksi_rate_pct
    FROM fact_collisions
    GROUP BY hour, is_rush_hour
)
SELECT 
    hour,
    is_rush_hour,
    collisions_count,
    ROUND(AVG(collisions_count) OVER (
        ORDER BY hour 
        ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING
    ), 1) AS rolling_3hr_avg_collisions,
    ksi_count,
    ksi_rate_pct
FROM hourly_stats
ORDER BY hour ASC;


-- ------------------------------------------------------------------------------
-- Query 4: Road Geometry & Speed Limit Hazard Matrix with Cumulative Partition
-- Computes KSI rate across speed limits and cumulative collision share per road type.
-- ------------------------------------------------------------------------------
WITH road_speed_matrix AS (
    SELECT 
        road_type,
        speed_limit,
        COUNT(collision_index) AS collisions_count,
        SUM(severity_ksi) AS ksi_count,
        ROUND(CAST(SUM(severity_ksi) AS REAL) / COUNT(collision_index) * 100, 2) AS ksi_rate_pct
    FROM fact_collisions
    WHERE road_type NOT IN ('Unknown', 'Missing / Unknown')
    GROUP BY road_type, speed_limit
)
SELECT 
    road_type,
    speed_limit,
    collisions_count,
    SUM(collisions_count) OVER (
        PARTITION BY road_type 
        ORDER BY speed_limit
    ) AS cumulative_collisions_by_speed,
    ROUND(CAST(collisions_count AS REAL) / SUM(collisions_count) OVER (PARTITION BY road_type) * 100, 2) AS pct_of_road_type,
    ksi_count,
    ksi_rate_pct
FROM road_speed_matrix
ORDER BY road_type, speed_limit;


-- ------------------------------------------------------------------------------
-- Query 5: Weather and Surface Condition Interaction Risk Analysis
-- CTE isolating combined adverse environmental conditions vs benign conditions.
-- ------------------------------------------------------------------------------
WITH environmental_interaction AS (
    SELECT 
        weather_conditions,
        road_surface_conditions,
        COUNT(collision_index) AS total_collisions,
        SUM(severity_ksi) AS ksi_collisions,
        ROUND(CAST(SUM(severity_ksi) AS REAL) / COUNT(collision_index) * 100, 2) AS ksi_rate_pct
    FROM fact_collisions
    WHERE weather_conditions NOT LIKE '%Unknown%' 
      AND road_surface_conditions NOT LIKE '%Unknown%'
    GROUP BY weather_conditions, road_surface_conditions
    HAVING COUNT(collision_index) >= 50
)
SELECT 
    weather_conditions,
    road_surface_conditions,
    total_collisions,
    ksi_collisions,
    ksi_rate_pct,
    ROUND(ksi_rate_pct / 23.73, 2) AS relative_risk_index
FROM environmental_interaction
ORDER BY total_collisions DESC
LIMIT 15;


-- ------------------------------------------------------------------------------
-- Query 6: High-Risk Accident Corridors & Blackspot Cluster Ranks
-- Joins analytical_blackspots with regional geography, calculating risk scores.
-- ------------------------------------------------------------------------------
SELECT 
    b.cluster_id,
    b.top_police_force,
    b.center_latitude,
    b.center_longitude,
    b.total_collisions,
    b.fatal_count,
    b.serious_count,
    b.slight_count,
    b.ksi_count,
    ROUND(CAST(b.ksi_count AS REAL) / b.total_collisions * 100, 2) AS ksi_rate_pct,
    b.severity_weighted_score,
    b.primary_road_type,
    b.speed_limit_mode,
    ROW_NUMBER() OVER (ORDER BY b.severity_weighted_score DESC) AS nationwide_hazard_rank
FROM analytical_blackspots b
ORDER BY nationwide_hazard_rank ASC
LIMIT 15;


-- ------------------------------------------------------------------------------
-- Query 7: Vulnerable Road Users (VRU) Involvement & Severity Disparity
-- Evaluates severity when Motorcycles, Cyclists, or HGVs are involved.
-- ------------------------------------------------------------------------------
SELECT 
    CASE 
        WHEN has_motorcycle = 1 THEN 'Motorcycle Involved'
        WHEN has_pedal_cycle = 1 THEN 'Pedal Cycle Involved'
        WHEN has_goods_hgv = 1 THEN 'HGV / Goods Involved'
        WHEN has_bus_coach = 1 THEN 'Bus / Coach Involved'
        ELSE 'Car / Passenger Only'
    END AS vehicle_involvement_cohort,
    COUNT(collision_index) AS collisions_count,
    SUM(CASE WHEN collision_severity = 1 THEN 1 ELSE 0 END) AS fatal_count,
    SUM(CASE WHEN collision_severity = 2 THEN 1 ELSE 0 END) AS serious_count,
    SUM(severity_ksi) AS ksi_count,
    ROUND(CAST(SUM(severity_ksi) AS REAL) / COUNT(collision_index) * 100, 2) AS ksi_rate_pct,
    ROUND(AVG(number_of_casualties), 2) AS avg_casualties_per_incident
FROM fact_collisions
GROUP BY vehicle_involvement_cohort
ORDER BY ksi_rate_pct DESC;


-- ------------------------------------------------------------------------------
-- Query 8: Casualty Demographics and Severity Distribution
-- Joins fact_casualties with fact_collisions, grouping by casualty class and age.
-- ------------------------------------------------------------------------------
SELECT 
    cas.casualty_class,
    CASE 
        WHEN cas.age_of_casualty < 18 THEN '0-17 (Youth)'
        WHEN cas.age_of_casualty BETWEEN 18 AND 24 THEN '18-24 (Young Adult)'
        WHEN cas.age_of_casualty BETWEEN 25 AND 59 THEN '25-59 (Adult)'
        WHEN cas.age_of_casualty >= 60 THEN '60+ (Senior)'
        ELSE 'Unknown Age'
    END AS age_bracket,
    COUNT(cas.casualty_id) AS total_casualties,
    SUM(CASE WHEN cas.casualty_severity = 'Fatal' THEN 1 ELSE 0 END) AS fatal_casualties,
    SUM(CASE WHEN cas.casualty_severity = 'Serious' THEN 1 ELSE 0 END) AS serious_casualties,
    SUM(CASE WHEN cas.casualty_severity = 'Slight' THEN 1 ELSE 0 END) AS slight_casualties,
    ROUND(CAST(SUM(CASE WHEN cas.casualty_severity IN ('Fatal', 'Serious') THEN 1 ELSE 0 END) AS REAL) / COUNT(cas.casualty_id) * 100, 2) AS casualty_ksi_rate_pct
FROM fact_casualties cas
GROUP BY cas.casualty_class, age_bracket
HAVING COUNT(cas.casualty_id) >= 100
ORDER BY cas.casualty_class, total_casualties DESC;


-- ------------------------------------------------------------------------------
-- Query 9: Vehicle Fleet Involvement & First Point of Impact Dynamics
-- Joins fact_vehicles with fact_collisions to analyze vehicle fleet impact types.
-- ------------------------------------------------------------------------------
SELECT 
    v.vehicle_category,
    COUNT(v.vehicle_id) AS total_vehicles_involved,
    ROUND(CAST(COUNT(v.vehicle_id) AS REAL) / (SELECT COUNT(*) FROM fact_vehicles) * 100, 2) AS fleet_share_pct,
    SUM(CASE WHEN v.first_point_of_impact = 1 THEN 1 ELSE 0 END) AS front_impacts,
    SUM(CASE WHEN v.first_point_of_impact = 2 THEN 1 ELSE 0 END) AS back_impacts,
    SUM(CASE WHEN v.first_point_of_impact = 3 THEN 1 ELSE 0 END) AS offside_impacts,
    SUM(CASE WHEN v.first_point_of_impact = 4 THEN 1 ELSE 0 END) AS nearside_impacts,
    ROUND(CAST(SUM(CASE WHEN v.first_point_of_impact = 1 THEN 1 ELSE 0 END) AS REAL) / COUNT(v.vehicle_id) * 100, 2) AS front_impact_pct
FROM fact_vehicles v
GROUP BY v.vehicle_category
ORDER BY total_vehicles_involved DESC;


-- ------------------------------------------------------------------------------
-- Query 10: Junction Type Hazard Index with National Baseline Comparison
-- Computes volume, KSI rate, and risk ratio relative to national average (23.73%).
-- ------------------------------------------------------------------------------
WITH national_baseline AS (
    SELECT ROUND(CAST(SUM(severity_ksi) AS REAL) / COUNT(collision_index) * 100, 4) AS gb_avg_ksi_rate
    FROM fact_collisions
),
junction_analysis AS (
    SELECT 
        junction_detail,
        COUNT(collision_index) AS collisions_count,
        SUM(severity_ksi) AS ksi_count,
        ROUND(CAST(SUM(severity_ksi) AS REAL) / COUNT(collision_index) * 100, 2) AS ksi_rate_pct
    FROM fact_collisions
    WHERE junction_detail NOT IN ('Missing / Unknown')
    GROUP BY junction_detail
)
SELECT 
    j.junction_detail,
    j.collisions_count,
    j.ksi_count,
    j.ksi_rate_pct,
    ROUND(j.ksi_rate_pct / b.gb_avg_ksi_rate, 2) AS relative_hazard_index
FROM junction_analysis j
CROSS JOIN national_baseline b
ORDER BY j.collisions_count DESC;


-- ------------------------------------------------------------------------------
-- Query 11: Regional Safety Pareto Analysis (80/20 Concentration Principle)
-- CTE calculating cumulative volume percentage using window SUM() OVER (ORDER BY ...).
-- ------------------------------------------------------------------------------
WITH regional_totals AS (
    SELECT 
        g.region,
        COUNT(c.collision_index) AS regional_collisions,
        SUM(c.severity_ksi) AS regional_ksi
    FROM fact_collisions c
    JOIN dim_geography g ON c.police_force = g.police_force
    GROUP BY g.region
),
pareto_calc AS (
    SELECT 
        region,
        regional_collisions,
        regional_ksi,
        SUM(regional_collisions) OVER (ORDER BY regional_collisions DESC) AS cumulative_collisions,
        SUM(regional_collisions) OVER () AS national_total_collisions
    FROM regional_totals
)
SELECT 
    region,
    regional_collisions,
    ROUND(CAST(regional_collisions AS REAL) / national_total_collisions * 100, 2) AS share_of_national_pct,
    ROUND(CAST(cumulative_collisions AS REAL) / national_total_collisions * 100, 2) AS cumulative_share_pct,
    regional_ksi,
    ROUND(CAST(regional_ksi AS REAL) / regional_collisions * 100, 2) AS regional_ksi_rate_pct
FROM pareto_calc
ORDER BY regional_collisions DESC;


-- ------------------------------------------------------------------------------
-- Query 12: Nighttime vs Daytime Corridor Risk Ratio by Jurisdiction
-- CTE calculating Day (06:00-21:59) vs Night (22:00-05:59) volume and risk multiplier.
-- ------------------------------------------------------------------------------
WITH day_night_split AS (
    SELECT 
        g.police_force_name,
        SUM(CASE WHEN c.is_night = 0 THEN 1 ELSE 0 END) AS daytime_collisions,
        SUM(CASE WHEN c.is_night = 0 AND c.severity_ksi = 1 THEN 1 ELSE 0 END) AS daytime_ksi,
        SUM(CASE WHEN c.is_night = 1 THEN 1 ELSE 0 END) AS nighttime_collisions,
        SUM(CASE WHEN c.is_night = 1 AND c.severity_ksi = 1 THEN 1 ELSE 0 END) AS nighttime_ksi
    FROM fact_collisions c
    JOIN dim_geography g ON c.police_force = g.police_force
    GROUP BY g.police_force_name
    HAVING COUNT(c.collision_index) >= 2000
)
SELECT 
    police_force_name,
    daytime_collisions,
    ROUND(CAST(daytime_ksi AS REAL) / daytime_collisions * 100, 2) AS daytime_ksi_rate_pct,
    nighttime_collisions,
    ROUND(CAST(nighttime_ksi AS REAL) / nighttime_collisions * 100, 2) AS nighttime_ksi_rate_pct,
    ROUND(
        (CAST(nighttime_ksi AS REAL) / nighttime_collisions) /
        (CAST(daytime_ksi AS REAL) / daytime_collisions), 
        2
    ) AS night_to_day_risk_multiplier
FROM day_night_split
ORDER BY night_to_day_risk_multiplier DESC
LIMIT 15;

