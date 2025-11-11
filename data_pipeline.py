import psycopg2
import requests
import pandas as pd
from datetime import datetime, timedelta
import random
import numpy as np
from dotenv import load_dotenv
import os

# Load environment at the very top
load_dotenv()

# Get connection string
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in environment")
    print("Create .env file with: DATABASE_URL=your_neon_connection_string")
    exit(1)

EIA_API_KEY = os.getenv('EIA_API_KEY')
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')

def get_connection():
    return psycopg2.connect(DATABASE_URL)

# 1. Insert major freight routes
def seed_routes():
    routes = [
        ('Los Angeles', 'Phoenix', 'CA', 'AZ', 373, 34.0522, -118.2437, 33.4484, -112.0740),
        ('Chicago', 'Atlanta', 'IL', 'GA', 715, 41.8781, -87.6298, 33.7490, -84.3880),
        ('Dallas', 'Houston', 'TX', 'TX', 239, 32.7767, -96.7970, 29.7604, -95.3698),
        ('New York', 'Philadelphia', 'NY', 'PA', 95, 40.7128, -74.0060, 39.9526, -75.1652),
        ('Seattle', 'Portland', 'WA', 'OR', 173, 47.6062, -122.3321, 45.5152, -122.6784),
        ('Miami', 'Jacksonville', 'FL', 'FL', 345, 25.7617, -80.1918, 30.3322, -81.6557),
        ('Denver', 'Salt Lake City', 'CO', 'UT', 525, 39.7392, -104.9903, 40.7608, -111.8910),
        ('Detroit', 'Cleveland', 'MI', 'OH', 169, 42.3314, -83.0458, 41.4993, -81.6944),
        ('San Francisco', 'Sacramento', 'CA', 'CA', 87, 37.7749, -122.4194, 38.5816, -121.4944),
        ('Phoenix', 'Las Vegas', 'AZ', 'NV', 297, 33.4484, -112.0740, 36.1699, -115.1398),
        ('Boston', 'New York', 'MA', 'NY', 215, 42.3601, -71.0589, 40.7128, -74.0060),
        ('Memphis', 'Nashville', 'TN', 'TN', 211, 35.1495, -90.0490, 36.1627, -86.7816),
        ('Kansas City', 'St Louis', 'MO', 'MO', 248, 39.0997, -94.5786, 38.6270, -90.1994),
        ('Indianapolis', 'Cincinnati', 'IN', 'OH', 112, 39.7684, -86.1581, 39.1031, -84.5120),
        ('Charlotte', 'Charleston', 'NC', 'SC', 208, 35.2271, -80.8431, 32.7765, -79.9311),
        ('Minneapolis', 'Milwaukee', 'MN', 'WI', 337, 44.9778, -93.2650, 43.0389, -87.9065),
        ('San Antonio', 'Austin', 'TX', 'TX', 80, 29.4241, -98.4936, 30.2672, -97.7431),
        ('Columbus', 'Pittsburgh', 'OH', 'PA', 185, 39.9612, -82.9988, 40.4406, -79.9959),
        ('Baltimore', 'Washington DC', 'MD', 'DC', 40, 39.2904, -76.6122, 38.9072, -77.0369),
        ('Tampa', 'Orlando', 'FL', 'FL', 84, 27.9506, -82.4572, 28.5383, -81.3792),
    ]
    
    conn = get_connection()
    cur = conn.cursor()
    
    for r in routes:
        lane_name = f"{r[0]}-{r[1]}"
        cur.execute("""
            INSERT INTO routes 
            (origin_city, destination_city, origin_state, destination_state, 
             baseline_distance_miles, origin_coords, destination_coords, lane_name)
            VALUES (%s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), 
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s)
            ON CONFLICT DO NOTHING
        """, (r[0], r[1], r[2], r[3], r[4], r[6], r[5], r[8], r[7], lane_name))
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"Seeded {len(routes)} routes")

# 2. Fetch fuel prices from EIA
def fetch_fuel_prices():
    url = "https://api.eia.gov/v2/petroleum/pri/gnd/data/"
    
    params = {
        'api_key': EIA_API_KEY,
        'frequency': 'weekly',
        'data[0]': 'value',
        'facets[product][]': 'EPD2D',  # Regular gasoline
        'sort[0][column]': 'period',
        'sort[0][direction]': 'desc',
        'offset': 0,
        'length': 5000
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    conn = get_connection()
    cur = conn.cursor()
    
    state_mapping = {
        'PADD 1': ['NY', 'PA', 'NJ', 'MA', 'MD', 'DC', 'VA', 'NC', 'SC', 'GA', 'FL'],
        'PADD 2': ['IL', 'IN', 'MI', 'OH', 'WI', 'MN', 'MO', 'TN'],
        'PADD 3': ['TX', 'LA', 'MS', 'AL', 'AR'],
        'PADD 4': ['CO', 'UT', 'WY', 'MT'],
        'PADD 5': ['CA', 'WA', 'OR', 'NV', 'AZ']
    }
    
    for record in data.get('response', {}).get('data', [])[:200]:
        date_str = record['period']
        price = float(record['value'])
        region = record.get('area-name', 'US')
        
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        states = state_mapping.get(region, ['TX'])  # Default
        
        for state in states:
            cur.execute("""
                INSERT INTO fuel_prices (state_code, price_per_gallon, date_recorded, data_source)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (state_code, date_recorded) DO UPDATE 
                SET price_per_gallon = EXCLUDED.price_per_gallon
            """, (state, price, date_obj, 'EIA'))
    
    conn.commit()
    cur.close()
    conn.close()
    print("Fuel prices updated")

# 3. Generate realistic trip data
def generate_trip_logs(num_trips=500):
    conn = get_connection()
    cur = conn.cursor()
    
    # Get routes - convert Decimal to float
    cur.execute("SELECT route_id, baseline_distance_miles, origin_state FROM routes")
    routes_raw = cur.fetchall()
    routes = [(int(r[0]), float(r[1]), r[2]) for r in routes_raw]
    
    # Get date range with fuel prices
    cur.execute("SELECT MIN(date_recorded), MAX(date_recorded) FROM fuel_prices")
    min_date, max_date = cur.fetchone()
    
    if not min_date:
        print("Load fuel prices first")
        return
    
    weather_conditions = ['Clear', 'Clear', 'Clear', 'Partly Cloudy', 'Cloudy', 'Rain', 'Snow', 'Fog']
    
    trips = []
    for _ in range(num_trips):
        route_id, distance, origin_state = random.choice(routes)
        
        # Random date in range
        days_between = (max_date - min_date).days
        random_days = random.randint(0, days_between)
        trip_date = min_date + timedelta(days=random_days)
        
        # Get fuel price for that date/state
        cur.execute("""
            SELECT price_per_gallon FROM fuel_prices 
            WHERE state_code = %s AND date_recorded <= %s 
            ORDER BY date_recorded DESC LIMIT 1
        """, (origin_state, trip_date))
        
        fuel_result = cur.fetchone()
        fuel_price = float(fuel_result[0]) if fuel_result else 3.50  # Convert to float
        
        # Realistic truck MPG: 6-7 mpg average, varies by conditions
        weather = random.choice(weather_conditions)
        base_mpg = random.uniform(6.0, 7.2)
        
        # Weather impact
        if weather == 'Rain':
            base_mpg *= 0.95
        elif weather == 'Snow':
            base_mpg *= 0.88
        elif weather == 'Fog':
            base_mpg *= 0.92
        
        # Speed impact (slower = better mpg to a point)
        avg_speed = random.uniform(58, 67)
        if avg_speed > 65:
            base_mpg *= 0.94
        
        # Load weight impact
        load_weight = random.randint(25000, 45000)
        if load_weight > 40000:
            base_mpg *= 0.96
        
        # Actual miles (now both are floats)
        actual_miles = distance * random.uniform(0.98, 1.05)
        
        # Weather impact
        if weather == 'Rain':
            base_mpg *= 0.95
        elif weather == 'Snow':
            base_mpg *= 0.88
        elif weather == 'Fog':
            base_mpg *= 0.92
        
        # Speed impact (slower = better mpg to a point)
        avg_speed = random.uniform(58, 67)
        if avg_speed > 65:
            base_mpg *= 0.94
        
        # Load weight impact
        load_weight = random.randint(25000, 45000)
        if load_weight > 40000:
            base_mpg *= 0.96
        
        # Actual miles (slight variance from baseline)
        actual_miles = distance * random.uniform(0.98, 1.05)
        
        # Calculate fuel
        fuel_consumed = actual_miles / base_mpg
        fuel_cost = fuel_consumed * fuel_price
        
        # Drive time (realistic with HOS, stops, etc.)
        drive_time = actual_miles / avg_speed
        stops = random.randint(1, 4)
        delay_hours = random.uniform(0, 2.5)
        
        departure_time = f"{random.randint(0,23):02d}:{random.randint(0,59):02d}:00"
        
        trips.append((
            route_id, trip_date, departure_time, trip_date, actual_miles,
            fuel_consumed, fuel_cost, drive_time, avg_speed, stops,
            delay_hours, weather, load_weight
        ))
    
    # Batch insert
    cur.executemany("""
        INSERT INTO trip_logs 
        (route_id, departure_date, departure_time, arrival_date, actual_miles_driven,
         fuel_consumed_gallons, fuel_cost_total, drive_time_hours, avg_speed_mph,
         stops_count, delay_hours, weather_conditions, load_weight_lbs)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, trips)
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"Generated {num_trips} trip logs")

if __name__ == "__main__":
    print("Starting data pipeline...")
    seed_routes()
    fetch_fuel_prices()
    generate_trip_logs(1000)
    print("Pipeline complete")