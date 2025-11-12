# Route Optimization Analysis: Freight Cost Reduction

[View Interactive Tableau Dashboard](https://public.tableau.com/views/RouteOptimizationAnalysisFreightTransportationCostReduction/CostAnalysisProjections?:language=en-US&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link)

## Executive Summary

Analyzed 1,000 freight trips across 20 major corridors to identify cost optimization opportunities.
**Key finding: $88,928 annual savings potential per analyzed route set,**
with a forcast of **8.6M** for a 100-truck fleet.

### Impact Metrics
- 27% MPG improvement through weather-aware routing.
- 8% efficiency gain via optimal departure timing.
- $0.0488 average cost variance per mile across conditions.

## Business Context

**The Problem:** Freight carriers operate on 3-5% net margins. Fuel represents 24% of operating costs. Small efficiency gains compound significantly at scale.

**The Opportunity:** Most carriers lack data infrastructure to optimize route timing, weather avoidance, and fuel purchasing decisions. This analysis quantifies the value of data-driven dispatch.

## Methodology

### Data Architecture

**Database:** PostgreSQL 14 + PostGIS (Neon serverless)
- 20 routes across major freight corridors
- 1,000 trip logs with operational variables
- 599 fuel price data points (state-level, weekly)
- Weather data integrated via OpenWeather API

**Schema Design:**
```sql
routes (geospatial route definitions)
  ├── Origin/destination coordinates
  └── Baseline distance metrics

trip_logs (operational data)
  ├── Fuel consumption & costs
  ├── Weather conditions at departure
  ├── MPG calculations (generated columns)
  └── Timing data (departure hour, delays)

fuel_prices (EIA API data)
optimization_results (analysis outputs)
```

### Analysis Approach

**SQL-based optimization:**
- Window functions for time-series patterns
- CTEs for multi-stage aggregations
- Geospatial queries for weather-route correlation

**Key calculations:**
```sql
-- Optimal conditions by route
WITH route_performance AS (
  SELECT route_id,
         weather_conditions,
         AVG(mpg_achieved) as avg_mpg,
         AVG(cost_per_mile) as avg_cost
  FROM trip_logs
  GROUP BY route_id, weather_conditions
)
SELECT route_id,
       MAX(avg_mpg) - MIN(avg_mpg) as mpg_variance,
       (AVG(cost_per_mile) - MIN(cost_per_mile)) * distance 
         as savings_potential
FROM route_performance;
```

## Key Findings

### 1. Weather Impact (27% efficiency variance)
- **Clear conditions:** 6.28 MPG average
- **Snow conditions:** 4.90 MPG average  
- **Recommendation:** Route around forecasted snow when possible

### 2. Timing Optimization (8% improvement)
- **Optimal window:** 1:00-5:00 AM departures
- **Worst window:** 3:00-6:00 PM (traffic congestion)
- **Implementation:** Shift dispatch schedules, minimal infrastructure cost

### 3. Route-Specific Opportunities
- **Chicago-Atlanta:** $13,762 annual savings potential (highest)
- **Los Angeles-Phoenix:** $8,969 annual savings
- **Top 10 routes:** $70K combined savings annually

### 4. Scaled Impact
**100-truck fleet projection:**
- Annual savings: $8,892,824
- 3-year value: $26,678,472
- ROI timeline: < 6 months (assuming $500K dispatch system investment)

## Technical Implementation

### Stack
- **Database:** PostgreSQL + PostGIS
- **Python:** 3.11 (psycopg2, pandas, requests)
- **APIs:** EIA (fuel), OpenWeather (conditions), NOAA (historical)
- **Visualization:** Tableau Public
- **Hosting:** Neon (database), GitHub (code)

### Data Pipeline
```python
# Automated data collection
def fetch_fuel_prices():
    # EIA API → PostgreSQL
    # State-level weekly prices

def fetch_weather_data():
    # OpenWeather API → Route coordinates
    # Historical conditions

def generate_trip_logs():
    # Synthetic data based on 12 years operational experience
    # Realistic MPG variance (6-7 baseline)
    # HOS-compliant drive times
```

### Reproducibility
```bash
# Setup
git clone repo
pip install -r requirements.txt
# Configure .env with API keys

# Execute pipeline
python data_pipeline.py
python optimization_analysis.py
python export_for_tableau.py
```

## Business Recommendations

### Immediate (0-30 days)
1. **Departure time optimization** — No infrastructure cost
   - Implement preferred dispatch windows per route
   - Expected impact: $28K annual savings

2. **Weather monitoring** — Minimal cost ($200/mo weather API)
   - Integrate 48-hour forecasts into dispatch
   - Delay shipments when snow/severe weather forecasted
   - Expected impact: $45K annual savings

### Medium-term (3-6 months)
3. **Route alternative analysis** — Moderate cost (analyst time)
   - Identify alternate routes for high-variance lanes
   - Test detour vs. delay trade-offs
   - Expected impact: $16K annual savings

### Long-term (6-12 months)
4. **Predictive routing system** — Significant investment
   - ML models for MPG prediction
   - Dynamic route optimization
   - Driver behavior scoring
   - Expected impact: 15-20% total fuel cost reduction

## Domain Expertise Applied

This analysis leverages 12 years of trucking operations experience:

- **Realistic MPG modeling:** 6-7 MPG baseline matches Class 8 truck performance
- **HOS compliance:** Drive time calculations respect 11-hour driving limits
- **Weather impact:** Snow degrades efficiency 12% (industry standard)
- **Load weight variance:** 25K-45K lbs realistic freight range
- **Route mileage:** Actual miles consistently 2-5% above baseline (real-world routing)

Traditional data analysts without operational context miss these nuances, producing unrealistic models.

## Project Files
```
route-optimization-analysis/
├── data_pipeline.py           # ETL & data generation
├── optimization_analysis.py   # Business logic
├── export_for_tableau.py      # Dashboard data prep
├── sql/
│   └── schema.sql            # Database structure
├── data/
│   └── tableau_*.csv         # Visualization sources
├── README.md
└── PORTFOLIO_CASE_STUDY.md   # This document
```

## Next Steps

**Potential extensions:**
- Incorporate load board rate data (DAT/Truckstop APIs)
- Add driver behavior variables (speed variance, idle time)
- Build predictive maintenance model (see Project 2)
- Seasonal analysis (winter vs. summer efficiency)

---

## About This Project

Created as part of data analytics portfolio demonstrating:
- SQL proficiency (complex queries, geospatial analysis)
- Python data engineering (API integration, ETL pipelines)
- Business analytics (cost-benefit analysis, ROI calculations)
- Data visualization (Tableau dashboard design)
- Domain expertise (logistics/transportation operations)

**Technologies:** PostgreSQL, Python, Tableau, REST APIs, Git  
**Timeline:** 1 week (data pipeline: 2 days, analysis: 2 days, visualization: 3 days)

[View Live Dashboard](https://public.tableau.com/views/RouteOptimizationAnalysisFreightTransportationCostReduction/CostAnalysisProjections?:language=en-US&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link) | [GitHub Repository](https://github.com/Xyxtvs/transportation-route-optimization)