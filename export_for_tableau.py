import psycopg2
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

def export_all_data():
    """Export data for Tableau visualization"""
    conn = psycopg2.connect(DATABASE_URL)
    
    # Main trip analysis
    query1 = """
    SELECT 
        r.lane_name,
        r.origin_city,
        r.destination_city,
        r.baseline_distance_miles,
        t.departure_date,
        EXTRACT(HOUR FROM t.departure_time)::int as departure_hour,
        TO_CHAR(t.departure_date, 'Day') as day_of_week,
        t.actual_miles_driven,
        t.fuel_consumed_gallons,
        t.fuel_cost_total,
        t.mpg_achieved,
        t.cost_per_mile,
        t.drive_time_hours,
        t.avg_speed_mph,
        t.weather_conditions,
        t.delay_hours,
        t.load_weight_lbs,
        f.price_per_gallon
    FROM trip_logs t
    JOIN routes r ON t.route_id = r.route_id
    LEFT JOIN fuel_prices f ON f.state_code = r.origin_state 
        AND f.date_recorded = t.departure_date;
    """
    
    df1 = pd.read_sql(query1, conn)
    df1.to_csv('data/tableau_trip_data.csv', index=False)
    print(f"Exported {len(df1)} trip records")
    
    # Optimization results
    query2 = """
    SELECT 
        r.lane_name,
        r.origin_city,
        r.destination_city,
        o.avg_fuel_cost_per_mile,
        o.optimal_departure_time,
        o.avg_mpg,
        o.best_case_mpg,
        o.worst_case_mpg,
        o.potential_savings_per_trip,
        o.annual_savings_estimate,
        o.recommendation
    FROM optimization_results o
    JOIN routes r ON o.route_id = r.route_id
    ORDER BY o.annual_savings_estimate DESC;
    """
    
    df2 = pd.read_sql(query2, conn)
    df2.to_csv('data/tableau_optimization_results.csv', index=False)
    print(f"Exported {len(df2)} optimization records")
    
    # Aggregated metrics for KPIs
    query3 = """
    SELECT 
        COUNT(DISTINCT route_id) as total_routes,
        COUNT(*) as total_trips,
        ROUND(AVG(mpg_achieved)::numeric, 2) as avg_mpg,
        ROUND(AVG(cost_per_mile)::numeric, 4) as avg_cost_per_mile,
        ROUND(SUM(fuel_cost_total)::numeric, 2) as total_fuel_cost,
        ROUND(SUM(actual_miles_driven)::numeric, 2) as total_miles
    FROM trip_logs;
    """
    
    df3 = pd.read_sql(query3, conn)
    df3.to_csv('data/tableau_kpi_metrics.csv', index=False)
    print(f"Exported KPI metrics")
    
    conn.close()
    print("\n✓ All data exported to data/ directory")
    print("Load these CSVs into Tableau to build dashboard")

if __name__ == "__main__":
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    export_all_data()