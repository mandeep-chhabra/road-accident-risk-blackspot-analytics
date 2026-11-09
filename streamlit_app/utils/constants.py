"""
Constants, Color Themes, and Configuration Settings for the Streamlit Analytics Dashboard.
"""

# Carto Basemap API Key provided by user
CARTO_API_KEY = "cb1_5246_1_3e759eaaffe30e8104e6a4d3"

# Canonical Severity Color Convention
COLOR_FATAL = "#990000"     # Dark Red
COLOR_SERIOUS = "#E65100"   # Deep Orange
COLOR_SLIGHT = "#2E7D32"    # Calm Forest Green / Neutral
COLOR_KSI = "#B71C1C"       # Vibrant Crimson for Severe (KSI)
COLOR_NON_KSI = "#3B82F6"   # Slate Blue for Slight

# Theme Accents
COLOR_NAVY = "#0F172A"
COLOR_SLATE = "#1E293B"
COLOR_BLUE = "#2563EB"
COLOR_TEAL = "#0D9488"
COLOR_AMBER = "#D97706"
COLOR_MUTED = "#64748B"
COLOR_CARD_BG = "#FFFFFF"
COLOR_PAGE_BG = "#F8FAFC"
COLOR_BORDER = "#E2E8F0"

# Plotly Color Mappings
SEVERITY_COLORS = {
    "Fatal": COLOR_FATAL,
    "Serious": COLOR_SERIOUS,
    "Slight": COLOR_SLIGHT
}

SEVERITY_KSI_COLORS = {
    "KSI": COLOR_KSI,
    "Slight": COLOR_SLIGHT,
    1: COLOR_KSI,
    0: COLOR_SLIGHT
}

# Carto Basemap URLs
CARTO_VOYAGER_URL = f"https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png?api_key={CARTO_API_KEY}"
CARTO_POSITRON_URL = f"https://{{s}}.basemaps.cartocdn.com/rastertiles/light_all/{{z}}/{{x}}/{{y}}{{r}}.png?api_key={CARTO_API_KEY}"
CARTO_DARK_URL = f"https://{{s}}.basemaps.cartocdn.com/rastertiles/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png?api_key={CARTO_API_KEY}"
CARTO_ATTRIBUTION = "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> &copy; <a href='https://carto.com/attributions'>CARTO</a>"

# File Paths
PATH_DATABASE = "data/road_safety.db"
PATH_FACT_COLLISIONS = "data/processed/fact_collisions.parquet"
PATH_DIM_BLACKSPOTS = "data/processed/dim_blackspots.csv"
PATH_DIM_DATE = "data/processed/dim_date.csv"
PATH_DIM_GEOGRAPHY = "data/processed/dim_geography.csv"
PATH_DIM_PREDICTIONS = "data/processed/dim_model_predictions.csv"
PATH_DATA_QUALITY_REPORT = "reports/data_quality_report.json"
PATH_STATISTICAL_REPORT = "reports/statistical_analysis_report.json"
PATH_SPATIAL_VALIDATION = "reports/spatial_validation.json"
PATH_MODEL_COMPARISON = "reports/model_comparison.csv"
PATH_FINAL_EVALUATION = "reports/final_evaluation.json"
PATH_FEATURE_IMPORTANCE = "reports/feature_importance.json"
PATH_CHAMPION_MODEL = "models/champion_lightgbm.joblib"
PATH_SQL_QUERIES = "sql/analytical_queries.sql"
PATH_POWERBI_SCREENSHOTS = "powerbi/screenshots"
PATH_FOLIUM_MAP = "visualization/accident_blackspots_map.html"

