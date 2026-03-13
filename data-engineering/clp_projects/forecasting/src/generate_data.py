"""
CLP Energy Demand Data Generator
================================
Generates realistic dummy data for energy demand forecasting.

This simulates:
- Hourly electricity consumption across Hong Kong districts
- Weather data (temperature, humidity)
- Calendar features (holidays, weekends)
- Seasonal patterns
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

def generate_energy_data(
    start_date: str = "2023-01-01",
    end_date: str = "2025-12-31",
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate synthetic energy consumption data.
    
    Returns:
        DataFrame with columns:
        - timestamp: Hourly timestamps
        - district: Hong Kong district
        - consumption_mwh: Energy consumption in MWh
        - temperature_c: Temperature in Celsius
        - humidity_pct: Relative humidity
        - is_weekend: Weekend flag
        - is_holiday: Holiday flag
        - hour: Hour of day
        - day_of_week: Day of week (0=Monday)
        - month: Month
    """
    np.random.seed(seed)
    
    # Generate date range (hourly)
    date_range = pd.date_range(start=start_date, end=end_date, freq='h')
    
    # Hong Kong districts
    districts = [
        "Central & Western", "Wan Chai", "Eastern", "Southern",
        "Yau Tsim Mong", "Sham Shui Po", "Kowloon City", "Wong Tai Sin",
        "Kwun Tong", "Kwai Tsing", "Tsuen Wan", "Tuen Mun",
        "Yuen Long", "North", "Tai Po", "Sha Tin", "Sai Kung", "Islands"
    ]
    
    # Base consumption by district (MW)
    district_base = {
        "Central & Western": 450, "Wan Chai": 380, "Eastern": 420,
        "Southern": 280, "Yau Tsim Mong": 350, "Sham Shui Po": 320,
        "Kowloon City": 340, "Wong Tai Sin": 300, "Kwun Tong": 380,
        "Kwai Tsing": 420, "Tsuen Wan": 350, "Tuen Mun": 380,
        "Yuen Long": 340, "North": 180, "Tai Po": 220,
        "Sha Tin": 380, "Sai Kung": 200, "Islands": 150
    }
    
    # Hong Kong public holidays (simplified)
    holidays = [
        "01-01", "02-10", "02-11", "02-12",  # New Year, CNY
        "04-04", "04-05",  # Ching Ming, Easter
        "05-01", "06-22",  # Labour Day, Dragon Boat
        "07-01", "10-01",  # HKSAR, National Day
        "12-25", "12-26"   # Christmas
    ]
    
    records = []
    
    for district in districts:
        base = district_base[district]
        
        for ts in date_range:
            # Time features
            hour = ts.hour
            day_of_week = ts.dayofweek
            month = ts.month
            is_weekend = day_of_week >= 5
            
            # Check holiday
            date_str = ts.strftime("%m-%d")
            is_holiday = date_str in holidays
            
            # Temperature model (seasonal + daily pattern)
            # Hong Kong: hot summers (28-33°C), mild winters (15-20°C)
            seasonal_temp = 23 + 8 * np.sin(2 * np.pi * (month - 4) / 12)
            daily_temp = 3 * np.sin(2 * np.pi * (hour - 6) / 24)
            temperature = seasonal_temp + daily_temp + np.random.normal(0, 2)
            temperature = np.clip(temperature, 10, 38)
            
            # Humidity (higher in summer)
            base_humidity = 70 + 15 * np.sin(2 * np.pi * (month - 7) / 12)
            humidity = base_humidity + np.random.normal(0, 10)
            humidity = np.clip(humidity, 40, 98)
            
            # Consumption model
            # Base load
            consumption = base
            
            # Hourly pattern (peak at 14:00-18:00 for commercial, 19:00-22:00 for residential)
            if 9 <= hour <= 18:  # Business hours
                consumption *= 1.3
            elif 19 <= hour <= 22:  # Evening peak
                consumption *= 1.4
            elif 0 <= hour <= 5:  # Night trough
                consumption *= 0.6
            
            # Weekend effect (less commercial, more residential)
            if is_weekend:
                consumption *= 0.85
            
            # Holiday effect
            if is_holiday:
                consumption *= 0.75
            
            # Temperature effect (AC usage)
            # Hong Kong: heavy AC usage when temp > 25°C
            if temperature > 25:
                consumption *= 1 + 0.03 * (temperature - 25)
            elif temperature < 18:
                consumption *= 1 + 0.01 * (18 - temperature)  # Heating (minimal in HK)
            
            # Seasonal adjustment
            if month in [6, 7, 8]:  # Summer peak
                consumption *= 1.15
            elif month in [12, 1, 2]:  # Winter
                consumption *= 0.9
            
            # Add noise
            consumption *= (1 + np.random.normal(0, 0.05))
            consumption = max(consumption, 50)  # Minimum load
            
            records.append({
                'timestamp': ts,
                'district': district,
                'consumption_mwh': round(consumption, 2),
                'temperature_c': round(temperature, 1),
                'humidity_pct': round(humidity, 1),
                'is_weekend': int(is_weekend),
                'is_holiday': int(is_holiday),
                'hour': hour,
                'day_of_week': day_of_week,
                'month': month
            })
    
    df = pd.DataFrame(records)
    return df


def generate_aggregated_data(hourly_df: pd.DataFrame) -> dict:
    """Generate aggregated views of the data"""
    
    # Daily aggregation
    daily_df = hourly_df.groupby([
        hourly_df['timestamp'].dt.date,
        'district'
    ]).agg({
        'consumption_mwh': 'sum',
        'temperature_c': 'mean',
        'humidity_pct': 'mean',
        'is_weekend': 'max',
        'is_holiday': 'max'
    }).reset_index()
    daily_df.columns = ['date', 'district', 'consumption_mwh', 
                        'avg_temperature_c', 'avg_humidity_pct',
                        'is_weekend', 'is_holiday']
    
    # Monthly aggregation (total Hong Kong)
    monthly_df = hourly_df.groupby(
        hourly_df['timestamp'].dt.to_period('M')
    ).agg({
        'consumption_mwh': 'sum',
        'temperature_c': 'mean'
    }).reset_index()
    monthly_df.columns = ['month', 'total_consumption_mwh', 'avg_temperature_c']
    monthly_df['month'] = monthly_df['month'].astype(str)
    
    return {
        'daily': daily_df,
        'monthly': monthly_df
    }


def save_data(output_dir: str = "."):
    """Generate and save all datasets"""
    import os
    
    print("Generating energy consumption data...")
    
    # Generate hourly data (sample - full would be too large)
    # For demo, generate 1 year of data
    hourly_df = generate_energy_data(
        start_date="2024-01-01",
        end_date="2024-12-31"
    )
    
    # Save hourly sample (first 10000 rows)
    hourly_sample = hourly_df.head(10000)
    hourly_sample.to_csv(
        os.path.join(output_dir, "energy_hourly_sample.csv"),
        index=False
    )
    print(f"Saved hourly sample: {len(hourly_sample)} rows")
    
    # Generate aggregated data
    agg_data = generate_aggregated_data(hourly_df)
    
    # Save daily data
    agg_data['daily'].to_csv(
        os.path.join(output_dir, "energy_daily.csv"),
        index=False
    )
    print(f"Saved daily data: {len(agg_data['daily'])} rows")
    
    # Save monthly data
    agg_data['monthly'].to_csv(
        os.path.join(output_dir, "energy_monthly.csv"),
        index=False
    )
    print(f"Saved monthly data: {len(agg_data['monthly'])} rows")
    
    # Generate statistics
    stats = {
        'total_records': len(hourly_df),
        'date_range': {
            'start': str(hourly_df['timestamp'].min()),
            'end': str(hourly_df['timestamp'].max())
        },
        'districts': list(hourly_df['district'].unique()),
        'consumption_stats': {
            'mean_mwh': round(hourly_df['consumption_mwh'].mean(), 2),
            'max_mwh': round(hourly_df['consumption_mwh'].max(), 2),
            'min_mwh': round(hourly_df['consumption_mwh'].min(), 2),
            'total_mwh': round(hourly_df['consumption_mwh'].sum(), 2)
        }
    }
    
    with open(os.path.join(output_dir, "data_stats.json"), 'w') as f:
        json.dump(stats, f, indent=2)
    print("Saved data statistics")
    
    return hourly_df, agg_data


if __name__ == "__main__":
    import os
    
    # Get the data directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "..", "data")
    
    # Create if not exists
    os.makedirs(data_dir, exist_ok=True)
    
    # Generate and save data
    save_data(data_dir)
    
    print("\nData generation complete!")
