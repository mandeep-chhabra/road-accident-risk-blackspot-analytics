# Power BI DAX Measures Reference Library

This document contains the complete DAX calculation library for the **Urban Road Accident Risk & Blackspot Analytics** Power BI report. All measures are grouped into a dedicated `_Measures` table.

---

## 1. Core Accident & Severity KPIs

### `[Total Collisions]`
```dax
Total Collisions = COUNTROWS(fact_collisions)
```

### `[Total Casualties]`
```dax
Total Casualties = SUM(fact_collisions[number_of_casualties])
```

### `[Casualties Per Collision]`
```dax
Casualties Per Collision = 
DIVIDE([Total Casualties], [Total Collisions], 0)
```

### `[Fatal Collisions]`
```dax
Fatal Collisions = 
CALCULATE(
    COUNTROWS(fact_collisions),
    fact_collisions[collision_severity] = 1
)
```

### `[Serious Collisions]`
```dax
Serious Collisions = 
CALCULATE(
    COUNTROWS(fact_collisions),
    fact_collisions[collision_severity] = 2
)
```

### `[Slight Collisions]`
```dax
Slight Collisions = 
CALCULATE(
    COUNTROWS(fact_collisions),
    fact_collisions[collision_severity] = 3
)
```

### `[KSI Collisions]`
```dax
KSI Collisions = 
CALCULATE(
    COUNTROWS(fact_collisions),
    fact_collisions[severity_ksi] = 1
)
```

### `[KSI Rate %]`
```dax
KSI Rate % = 
DIVIDE([KSI Collisions], [Total Collisions], 0)
```

### `[Fatal Rate %]`
```dax
Fatal Rate % = 
DIVIDE([Fatal Collisions], [Total Collisions], 0)
```

---

## 2. Time Intelligence & Trend Measures

### `[Collisions Prior Year]`
```dax
Collisions Prior Year = 
CALCULATE(
    [Total Collisions],
    SAMEPERIODLASTYEAR(dim_date[date])
)
```

### `[YoY Collision Change %]`
```dax
YoY Collision Change % = 
VAR CurrentVol = [Total Collisions]
VAR PriorVol = [Collisions Prior Year]
RETURN
    IF(
        NOT ISBLANK(PriorVol) && PriorVol > 0,
        DIVIDE(CurrentVol - PriorVol, PriorVol, 0),
        BLANK()
    )
```

### `[KSI Prior Year]`
```dax
KSI Prior Year = 
CALCULATE(
    [KSI Collisions],
    SAMEPERIODLASTYEAR(dim_date[date])
)
```

### `[YoY KSI Change %]`
```dax
YoY KSI Change % = 
VAR CurrentKSI = [KSI Collisions]
VAR PriorKSI = [KSI Prior Year]
RETURN
    IF(
        NOT ISBLANK(PriorKSI) && PriorKSI > 0,
        DIVIDE(CurrentKSI - PriorKSI, PriorKSI, 0),
        BLANK()
    )
```

### `[Collisions YTD]`
```dax
Collisions YTD = 
TOTALYTD([Total Collisions], dim_date[date])
```

### `[7-Day Moving Avg Collisions]`
```dax
7-Day Moving Avg Collisions = 
AVERAGEX(
    DATESINPERIOD(dim_date[date], LASTDATE(dim_date[date]), -7, DAY),
    [Total Collisions]
)
```

---

## 3. Temporal & Operational Dynamics

### `[Rush Hour Collisions]`
```dax
Rush Hour Collisions = 
CALCULATE(
    [Total Collisions],
    fact_collisions[is_rush_hour] = 1
)
```

### `[Rush Hour Ratio %]`
```dax
Rush Hour Ratio % = 
DIVIDE([Rush Hour Collisions], [Total Collisions], 0)
```

### `[Weekend Collisions]`
```dax
Weekend Collisions = 
CALCULATE(
    [Total Collisions],
    fact_collisions[is_weekend] = 1
)
```

### `[Nighttime Collisions]`
```dax
Nighttime Collisions = 
CALCULATE(
    [Total Collisions],
    fact_collisions[is_night] = 1
)
```

### `[Night to Day Risk Ratio]`
```dax
Night to Day Risk Ratio = 
VAR NightKSI = CALCULATE([KSI Rate %], fact_collisions[is_night] = 1)
VAR DayKSI = CALCULATE([KSI Rate %], fact_collisions[is_night] = 0)
RETURN
    DIVIDE(NightKSI, DayKSI, 1.0)
```

---

## 4. Geospatial & Blackspot Hazard Analytics

### `[Total Identified Blackspots]`
```dax
Total Identified Blackspots = COUNTROWS(dim_blackspots)
```

### `[Max Blackspot Severity Score]`
```dax
Max Blackspot Severity Score = MAX(dim_blackspots[severity_weighted_score])
```

### `[Avg Blackspot Collisions]`
```dax
Avg Blackspot Collisions = AVERAGE(dim_blackspots[total_collisions])
```

### `[Top 10 Blackspots Cumulative Score]`
```dax
Top 10 Blackspots Cumulative Score = 
CALCULATE(
    SUM(dim_blackspots[severity_weighted_score]),
    dim_blackspots[risk_rank] <= 10
)
```

---

## 5. Predictive Machine Learning & Risk Scoring

### `[Model Scored Incidents]`
```dax
Model Scored Incidents = COUNTROWS(dim_model_predictions)
```

### `[Predicted KSI Count]`
```dax
Predicted KSI Count = 
CALCULATE(
    COUNTROWS(dim_model_predictions),
    dim_model_predictions[predicted_severity_ksi] = 1
)
```

### `[Predicted KSI Rate %]`
```dax
Predicted KSI Rate % = 
DIVIDE([Predicted KSI Count], [Model Scored Incidents], 0)
```

### `[Model Overall Accuracy %]`
```dax
Model Overall Accuracy % = 
DIVIDE(
    CALCULATE(COUNTROWS(dim_model_predictions), dim_model_predictions[is_prediction_correct] = 1),
    [Model Scored Incidents],
    0
)
```

### `[Model High Risk Threshold]`
```dax
Model High Risk Threshold = 0.610
```

### `[Dynamic Page Title]`
```dax
Dynamic Page Title = 
VAR SelectedRegion = SELECTEDVALUE(dim_geography[region], "Great Britain (Nationwide)")
VAR SelectedYear = SELECTEDVALUE(dim_date[year], "2022–2023")
RETURN
    "Road Accident Analytics & Risk Report: " & SelectedRegion & " (" & SelectedYear & ")"
```

