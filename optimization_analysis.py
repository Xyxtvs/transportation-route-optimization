import psycopg2
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def analyze_route_optimization():
    conn = get_connection()
    
    # Find optimal conditions for each route
    query = """
    WITH route_stats AS (
        SELECT 
            t.route_id,
            r.lane_name,
            r.baseline_distance_miles,
            
            -- Overall statistics
            COUNT(t.trip_id) as total_trips,
            ROUND(AVG(t.mpg_achieved)::numeric, 2) as avg_mpg,
            ROUND(MAX(t.mpg_achieved)::numeric, 2) as best_mpg,
            ROUND(MIN(t.mpg_achieved)::numeric, 2) as worst_mpg,
            ROUND(AVG(t.cost_per_mile)::numeric, 4) as avg_cost_per_mile,
            ROUND(MIN(t.cost_per_mile)::numeric, 4) as best_cost_per_mile,
            
            -- Best conditions analysis
            (SELECT weather_conditions 
             FROM trip_logs t2 
             WHERE t2.route_id = t.route_id 
             ORDER BY mpg_achieved DESC LIMIT 1) as best_weather,
            
            (SELECT EXTRACT(HOUR FROM departure_time)::int
             FROM trip_logs t2 
             WHERE t2.route_id = t.route_id 
             ORDER BY mpg_achieved DESC LIMIT 1) as optimal_departure_hour,
            
            -- Calculate potential savings
            ROUND((AVG(t.cost_per_mile) - MIN(t.cost_per_mile)) * r.baseline_distance_miles, 2) 
                as savings_per_trip
            
        FROM trip_logs t
        JOIN routes r ON t.route_id = r.route_id
        GROUP BY t.route_id, r.lane_name, r.baseline_distance_miles
    )
    SELECT 
        *,
        -- Annual savings estimate (assume 50 trips/year per route)
        ROUND(savings_per_trip * 50, 2) as annual_savings_per_route
    FROM route_stats
    ORDER BY savings_per_trip DESC;
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    return df

def weather_impact_analysis():
    conn = get_connection()
    
    query = """
    SELECT 
        weather_conditions,
        COUNT(*) as trip_count,
        ROUND(AVG(mpg_achieved)::numeric, 2) as avg_mpg,
        ROUND(AVG(cost_per_mile)::numeric, 4) as avg_cost_per_mile,
        ROUND(AVG(avg_speed_mph)::numeric, 1) as avg_speed,
        ROUND(AVG(delay_hours)::numeric, 2) as avg_delay_hours
    FROM trip_logs
    GROUP BY weather_conditions
    ORDER BY avg_mpg DESC;
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    return df

def time_of_day_analysis():
    conn = get_connection()
    
    query = """
    SELECT 
        EXTRACT(HOUR FROM departure_time)::int as departure_hour,
        COUNT(*) as trips,
        ROUND(AVG(mpg_achieved)::numeric, 2) as avg_mpg,
        ROUND(AVG(cost_per_mile)::numeric, 4) as avg_cost_per_mile,
        ROUND(AVG(delay_hours)::numeric, 2) as avg_delay
    FROM trip_logs
    GROUP BY departure_hour
    ORDER BY departure_hour;
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    return df

def insert_optimization_results():
    """Calculate and store optimization recommendations"""
    conn = get_connection()
    cur = conn.cursor()
    
    # Clear old results
    cur.execute("DELETE FROM optimization_results")
    
    # Insert new optimization results
    query = """
    INSERT INTO optimization_results 
    (route_id, avg_fuel_cost_per_mile, optimal_departure_time, optimal_departure_day,
     avg_mpg, best_case_mpg, worst_case_mpg, potential_savings_per_trip, 
     annual_savings_estimate, recommendation)
    
    WITH route_analysis AS (
        SELECT 
            t.route_id,
            r.baseline_distance_miles,
            AVG(t.cost_per_mile) as avg_cpm,
            MIN(t.cost_per_mile) as best_cpm,
            AVG(t.mpg_achieved) as avg_mpg,
            MAX(t.mpg_achieved) as best_mpg,
            MIN(t.mpg_achieved) as worst_mpg,
            
            -- Find optimal departure hour
            (SELECT EXTRACT(HOUR FROM departure_time)::int
             FROM trip_logs t2 
             WHERE t2.route_id = t.route_id 
             ORDER BY mpg_achieved DESC, cost_per_mile ASC LIMIT 1) as best_hour,
            
            -- Find best day of week
            (SELECT TO_CHAR(departure_date, 'Day')
             FROM trip_logs t2 
             WHERE t2.route_id = t.route_id 
             ORDER BY mpg_achieved DESC LIMIT 1) as best_day,
            
            -- Best weather condition
            (SELECT weather_conditions 
             FROM trip_logs t2 
             WHERE t2.route_id = t.route_id 
             ORDER BY mpg_achieved DESC LIMIT 1) as best_weather
            
        FROM trip_logs t
        JOIN routes r ON t.route_id = r.route_id
        GROUP BY t.route_id, r.baseline_distance_miles
    )
    SELECT 
        route_id,
        avg_cpm,
        (best_hour || ':00:00')::TIME as optimal_time,
        best_day,
        avg_mpg,
        best_mpg,
        worst_mpg,
        (avg_cpm - best_cpm) * baseline_distance_miles as savings_per_trip,
        (avg_cpm - best_cpm) * baseline_distance_miles * 50 as annual_savings,
        'Depart at ' || best_hour || ':00 on ' || best_day || 
        ' for optimal fuel efficiency. Expect ' || best_weather || 
        ' conditions for best MPG.' as recommendation
    FROM route_analysis;
    """
    
    cur.execute(query)
    conn.commit()
    
    # Show results
    cur.execute("""
        SELECT 
            r.lane_name,
            o.optimal_departure_time,
            o.avg_mpg,
            o.best_case_mpg,
            o.potential_savings_per_trip,
            o.annual_savings_estimate
        FROM optimization_results o
        JOIN routes r ON o.route_id = r.route_id
        ORDER BY o.annual_savings_estimate DESC
        LIMIT 10;
    """)
    
    results = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return results

if __name__ == "__main__":
    print("\n=== ROUTE OPTIMIZATION ANALYSIS ===\n")
    
    print("1. Route-by-route optimization opportunities:")
    route_opt = analyze_route_optimization()
    print(route_opt.head(10))
    print(f"\nTotal potential annual savings: ${route_opt['annual_savings_per_route'].sum():,.2f}")
    
    print("\n\n2. Weather impact on performance:")
    weather = weather_impact_analysis()
    print(weather)
    
    print("\n\n3. Time of day analysis:")
    time_analysis = time_of_day_analysis()
    print(time_analysis)
    
    print("\n\n4. Storing optimization recommendations...")
    results = insert_optimization_results()
    print("\nTop 10 routes by savings potential:")
    for r in results:
        print(f"{r[0]}: Depart at {r[1]}, Save ${r[5]:,.2f}/year")
    
    print("\n✓ Analysis complete. Optimization results stored in database.")