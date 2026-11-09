# Statistical Analysis & Hypothesis Testing Findings

## 1. Accident Severity Proportions & 95% Wilson Score Intervals

- **Total Valid Collisions**: 210,228
- **Fatal Collisions**: 3,124 (1.49% [1.44%, 1.54%])
- **Serious Collisions**: 46,761 (22.24% [22.07%, 22.42%])
- **Killed or Seriously Injured (KSI)**: 49,885 (23.73% [23.55%, 23.91%])
- **Slight Collisions**: 160,343 (76.27%)

## 2. Chi-Square Tests of Independence (Association with Severity)

| Factor | Chi-Square (χ²) | df | Raw p-value | FDR Adj p-value | Cramér's V | Association Strength |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| Speed Limit (mph) | 3,678.9 | 10 | 0.00e+00 | 0.00e+00 | 0.0934 | Small |
| Road Geometry Type | 891.7 | 8 | 3.47e-187 | 8.33e-187 | 0.0465 | Weak |
| Lighting Conditions | 1,535.2 | 8 | 0.00e+00 | 0.00e+00 | 0.0603 | Small |
| Weather Conditions | 165.6 | 14 | 5.19e-28 | 5.66e-28 | 0.0193 | Weak |
| Road Surface Conditions | 79.5 | 8 | 6.15e-14 | 6.15e-14 | 0.0132 | Weak |
| Urban vs Rural Environment | 2,430.0 | 2 | 0.00e+00 | 0.00e+00 | 0.1075 | Small |
| Junction Detail | 446.6 | 10 | 1.11e-89 | 2.22e-89 | 0.0326 | Weak |
| Rush Hour Indicator | 379.2 | 2 | 4.59e-83 | 7.86e-83 | 0.0424 | Weak |
| Weekend Indicator | 291.4 | 2 | 5.27e-64 | 7.02e-64 | 0.0371 | Weak |
| Motorcycle Involvement | 1,765.1 | 2 | 0.00e+00 | 0.00e+00 | 0.0916 | Small |
| Pedal Cycle Involvement | 305.9 | 2 | 3.75e-67 | 5.63e-67 | 0.0380 | Weak |
| HGV / Goods Vehicle Involvement | 257.2 | 2 | 1.38e-56 | 1.66e-56 | 0.0348 | Weak |

*Note: Multiplicity controlled via Benjamini-Hochberg False Discovery Rate (FDR) at α=0.05.*

## 3. Non-Parametric Group Comparisons

### Kruskal-Wallis H-test: Number of casualties across accident severity levels (Slight, Serious, Fatal)
- **Test Statistic**: 1407.41
- **p-value**: 2.43e-306
- **Practical Interpretation**: Casualty count increases with collision severity; fatal collisions involve significantly higher casualty counts.

### Mann-Whitney U Test: Number of vehicles involved: Fatal vs Slight collisions
- **Test Statistic**: 219954863.0
- **p-value**: 1.36e-43
- **Practical Interpretation**: Fatal collisions involve a statistically significant difference in vehicle composition compared to slight collisions.

### Mann-Whitney U Test: Speed limits in Rural vs Urban road networks
- **Test Statistic**: 8349552939.0
- **p-value**: 0.00e+00
- **Practical Interpretation**: Rural road networks have significantly higher posted speed limits (mean 53.4 mph vs 27.5 mph), contributing to higher kinetic energy and collision severity.

