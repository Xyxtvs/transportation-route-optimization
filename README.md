# Route Optimization Analysis: Freight Transportation Cost Reduction

## Business Problem

Freight transportation companies face rising fuel costs and operational inefficiencies. Small improvements in route
planning, departure timing, and weather-based decision-making can yield significant cost savings. This project analyzes
historical trip data to identify optimization opportunities.

## Key Findings

- **$88,928 annual savings potential** across 20 analyzed freight corridors
- **27% MPG improvement** possible through weather-aware routing
- **Early morning departures** (1-5am) show 8% better fuel efficiency
- **Clear weather routing** yields 6.28 MPG vs 4.90 MPG in snow

### Scaled Impact

For a 100-truck fleet:
**$890,000 annual savings**

3 year ROI: **$2.67 million**

## Technical Approach

### Data Architecture

- **Database**: PostgreSQL (Neon) with PostGIS for geospatial analysis
- **Data Sources**:
    - EIA API (fuel prices)
    - OpenWeather API (historical weather)
    - Synthetic trip logs based on industry-standard parameters

### Schema Design

```
routes (20 major freight corridors)
├── Origin/destination coordinates (PostGIS)
├── Baseline distance metrics
└── Lane identifiers

trip_logs (1,000 historical trips)
├── Fuel consumption
├── Weather conditions
├── Departure timing
└── Calculated MPG & cost metrics

fuel_prices (599 regional price points)
optimization_results (route-specific recommendations)
```

### Analysis Methods

**SQL-based analysis:**

- Window functions for time-series patterns
- Geospatial joins for weather-route correlation
- CTEs for multi-stage optimization logic

**Key queries:**

- Cost variance by weather condition
- Optimal departure time by route
- Fuel efficiency regression analysis

## Business Recommendations

1. **Implement weather-based route planning**: Save $45K annually
2. **Shift departures to early morning windows**: Save $28K annually
3. **Avoid snow-condition travel when possible**: Save $16K annually

### Implementation Priority

- **Quick Win**: Departure time optimization (0 infrastructure cost)
- **Medium-term**: Weather API integration into dispatch system
- **Long-term**: Predictive routing with ML models

## Technical Stack

- **Database**: PostgreSQL 17 + PostGIS
- **Language**: Python 3.11
- **Key Libraries**: psycopg2, pandas, requests
- **Visualization**: Tableau Public
- **Cloud**: Neon (serverless Postgres)
- **APIs**: EIA, OpenWeather, NOAA

## Project Structure

```
route-optimization-analysis/
├── data_pipeline.py          # Data collection & loading
├── optimization_analysis.py  # Business logic & calculations
├── export_for_tableau.py     # Visualization data export
├── sql/
│   ├── schema.sql           # Database schema
│   └── analysis_queries.sql # Optimization queries
├── data/
│   ├── tableau_*.csv        # Viz exports
│   └── raw/                 # API responses
└── README.md
```

## Reproducibility

1. Clone repository
2. Set up Neon PostgreSQL instance
3. Configure `.env` with API keys
4. Run: `python data_pipeline.py`
5. Run: `python optimization_analysis.py`
6. Load CSVs into Tableau Public

## Domain Context

This analysis leverages 12 years of trucking industry experience, including:

- Realistic MPG expectations (6-7 MPG baseline)
- HOS (Hours of Service) compliance constraints
- Weather impact on fuel efficiency
- Regional fuel price variance
- Actual route mileage vs baseline distance

Traditional data analysts without operational knowledge often underestimate weather impacts and miss timing optimization
opportunities.

## Future Enhancements

- Machine learning models for MPG prediction
- Real-time weather integration
- Load weight optimization analysis
- Driver behavior scoring
- Seasonal demand forecasting

## Contact

Yogape Rodriguez  
Data Analyst | Logistics & Supply Chain Optimization

http://www.linkedin.com/in/yogape