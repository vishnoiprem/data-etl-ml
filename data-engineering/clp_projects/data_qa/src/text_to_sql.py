"""
Conversational Data Analytics - Text-to-SQL System for CLP
============================================================
Enable business users to ask questions in natural language
and get answers from the data warehouse.

Examples:
- "What was the total energy consumption last month by district?"
- "Show me the top 10 customers by usage"
- "Compare Q1 vs Q2 revenue"

Author: Prem Vishnoi
Date: March 2026
"""

import pandas as pd
import numpy as np
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import re
import json


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class TextToSQLConfig:
    """Configuration for Text-to-SQL system"""
    llm_model: str = "gpt-4"
    temperature: float = 0.0
    max_tokens: int = 500
    show_sql: bool = True
    validate_sql: bool = True


# ============================================================================
# DATABASE SCHEMA
# ============================================================================

SCHEMA_DEFINITION = """
-- CLP Energy Data Warehouse Schema

-- Customer dimension
CREATE TABLE dim_customer (
    customer_id VARCHAR(20) PRIMARY KEY,
    customer_name VARCHAR(100),
    customer_type VARCHAR(20),  -- 'residential', 'commercial', 'industrial'
    district VARCHAR(50),
    tariff_plan VARCHAR(20),    -- 'standard', 'tou', 'commercial'
    registered_date DATE,
    is_active BOOLEAN
);

-- Time dimension
CREATE TABLE dim_time (
    date_key INTEGER PRIMARY KEY,
    full_date DATE,
    year INTEGER,
    quarter INTEGER,
    month INTEGER,
    month_name VARCHAR(20),
    day_of_month INTEGER,
    day_of_week INTEGER,
    day_name VARCHAR(20),
    is_weekend BOOLEAN,
    is_holiday BOOLEAN
);

-- Location dimension
CREATE TABLE dim_location (
    location_id VARCHAR(20) PRIMARY KEY,
    district VARCHAR(50),
    region VARCHAR(20),         -- 'hong_kong_island', 'kowloon', 'new_territories'
    substation_id VARCHAR(20)
);

-- Energy consumption fact table
CREATE TABLE fact_consumption (
    consumption_id INTEGER PRIMARY KEY,
    customer_id VARCHAR(20),
    location_id VARCHAR(20),
    date_key INTEGER,
    hour INTEGER,
    consumption_kwh DECIMAL(10,2),
    demand_kw DECIMAL(10,2),
    power_factor DECIMAL(3,2),
    FOREIGN KEY (customer_id) REFERENCES dim_customer(customer_id),
    FOREIGN KEY (location_id) REFERENCES dim_location(location_id),
    FOREIGN KEY (date_key) REFERENCES dim_time(date_key)
);

-- Billing fact table
CREATE TABLE fact_billing (
    bill_id INTEGER PRIMARY KEY,
    customer_id VARCHAR(20),
    billing_month DATE,
    consumption_kwh DECIMAL(12,2),
    demand_kw DECIMAL(10,2),
    energy_charge DECIMAL(10,2),
    demand_charge DECIMAL(10,2),
    fuel_adjustment DECIMAL(10,2),
    total_amount DECIMAL(10,2),
    payment_status VARCHAR(20),
    FOREIGN KEY (customer_id) REFERENCES dim_customer(customer_id)
);

-- Outage events table
CREATE TABLE fact_outage (
    outage_id INTEGER PRIMARY KEY,
    location_id VARCHAR(20),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_minutes INTEGER,
    affected_customers INTEGER,
    cause VARCHAR(50),
    FOREIGN KEY (location_id) REFERENCES dim_location(location_id)
);
"""

SCHEMA_DESCRIPTIONS = {
    "dim_customer": {
        "description": "Customer master data with type, district, and tariff information",
        "columns": {
            "customer_id": "Unique customer identifier (e.g., 'CUST001')",
            "customer_type": "One of: 'residential', 'commercial', 'industrial'",
            "district": "Hong Kong district name",
            "tariff_plan": "One of: 'standard', 'tou' (time-of-use), 'commercial'"
        },
        "sample_values": {
            "customer_type": ["residential", "commercial", "industrial"],
            "district": ["Central & Western", "Wan Chai", "Eastern", "Kowloon City", "Sha Tin"]
        }
    },
    "fact_consumption": {
        "description": "Hourly electricity consumption records",
        "columns": {
            "consumption_kwh": "Energy consumed in kilowatt-hours",
            "demand_kw": "Peak demand in kilowatts",
            "hour": "Hour of day (0-23)"
        }
    },
    "fact_billing": {
        "description": "Monthly billing records with charges breakdown",
        "columns": {
            "total_amount": "Total bill amount in HKD",
            "payment_status": "One of: 'paid', 'pending', 'overdue'"
        }
    },
    "dim_time": {
        "description": "Calendar dimension for date analysis",
        "columns": {
            "quarter": "Quarter number (1-4)",
            "month_name": "Full month name (January, February, etc.)"
        }
    }
}


# ============================================================================
# SAMPLE DATA GENERATOR
# ============================================================================

class DataGenerator:
    """Generate sample data for the CLP data warehouse"""
    
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        self.districts = [
            "Central & Western", "Wan Chai", "Eastern", "Southern",
            "Yau Tsim Mong", "Sham Shui Po", "Kowloon City", "Wong Tai Sin",
            "Kwun Tong", "Kwai Tsing", "Tsuen Wan", "Tuen Mun",
            "Yuen Long", "North", "Tai Po", "Sha Tin", "Sai Kung", "Islands"
        ]
        self.regions = {
            "Central & Western": "hong_kong_island",
            "Wan Chai": "hong_kong_island",
            "Eastern": "hong_kong_island",
            "Southern": "hong_kong_island",
            "Yau Tsim Mong": "kowloon",
            "Sham Shui Po": "kowloon",
            "Kowloon City": "kowloon",
            "Wong Tai Sin": "kowloon",
            "Kwun Tong": "kowloon",
            "Kwai Tsing": "new_territories",
            "Tsuen Wan": "new_territories",
            "Tuen Mun": "new_territories",
            "Yuen Long": "new_territories",
            "North": "new_territories",
            "Tai Po": "new_territories",
            "Sha Tin": "new_territories",
            "Sai Kung": "new_territories",
            "Islands": "new_territories"
        }
    
    def generate_customers(self, n: int = 1000) -> pd.DataFrame:
        """Generate customer dimension data"""
        customer_types = ['residential', 'commercial', 'industrial']
        type_weights = [0.7, 0.25, 0.05]
        tariff_plans = ['standard', 'tou', 'commercial']
        
        customers = []
        for i in range(n):
            cust_type = np.random.choice(customer_types, p=type_weights)
            district = np.random.choice(self.districts)
            
            if cust_type == 'residential':
                tariff = np.random.choice(['standard', 'tou'], p=[0.8, 0.2])
            else:
                tariff = 'commercial'
            
            customers.append({
                'customer_id': f'CUST{i+1:05d}',
                'customer_name': f'Customer {i+1}',
                'customer_type': cust_type,
                'district': district,
                'tariff_plan': tariff,
                'registered_date': pd.Timestamp('2020-01-01') + pd.Timedelta(days=np.random.randint(0, 1500)),
                'is_active': np.random.choice([True, False], p=[0.95, 0.05])
            })
        
        return pd.DataFrame(customers)
    
    def generate_time_dimension(self, start_date: str = '2023-01-01', 
                                 end_date: str = '2025-12-31') -> pd.DataFrame:
        """Generate time dimension"""
        dates = pd.date_range(start=start_date, end=end_date, freq='d')
        
        holidays = ['01-01', '02-10', '02-11', '04-04', '05-01', 
                    '07-01', '10-01', '12-25', '12-26']
        
        time_dim = []
        for i, date in enumerate(dates):
            time_dim.append({
                'date_key': int(date.strftime('%Y%m%d')),
                'full_date': date,
                'year': date.year,
                'quarter': date.quarter,
                'month': date.month,
                'month_name': date.strftime('%B'),
                'day_of_month': date.day,
                'day_of_week': date.dayofweek,
                'day_name': date.strftime('%A'),
                'is_weekend': date.dayofweek >= 5,
                'is_holiday': date.strftime('%m-%d') in holidays
            })
        
        return pd.DataFrame(time_dim)
    
    def generate_locations(self) -> pd.DataFrame:
        """Generate location dimension"""
        locations = []
        loc_id = 0
        
        for district in self.districts:
            n_substations = np.random.randint(2, 6)
            for j in range(n_substations):
                locations.append({
                    'location_id': f'LOC{loc_id+1:04d}',
                    'district': district,
                    'region': self.regions[district],
                    'substation_id': f'SUB_{district[:3].upper()}_{j+1}'
                })
                loc_id += 1
        
        return pd.DataFrame(locations)
    
    def generate_consumption(self, customers: pd.DataFrame, 
                             locations: pd.DataFrame,
                             time_dim: pd.DataFrame,
                             n_records: int = 50000) -> pd.DataFrame:
        """Generate consumption fact data"""
        consumption = []
        
        # Base consumption by customer type (kWh per hour)
        base_consumption = {
            'residential': 2,
            'commercial': 50,
            'industrial': 200
        }
        
        for i in range(n_records):
            customer = customers.sample(1).iloc[0]
            location = locations[locations['district'] == customer['district']].sample(1).iloc[0]
            date_row = time_dim.sample(1).iloc[0]
            hour = np.random.randint(0, 24)
            
            # Calculate consumption
            base = base_consumption[customer['customer_type']]
            
            # Hour pattern
            if 9 <= hour <= 18:
                base *= 1.3
            elif 19 <= hour <= 22:
                base *= 1.2
            elif 0 <= hour <= 5:
                base *= 0.5
            
            # Weekend effect
            if date_row['is_weekend']:
                if customer['customer_type'] == 'commercial':
                    base *= 0.3
                else:
                    base *= 1.1
            
            # Add randomness
            consumption_kwh = base * np.random.uniform(0.8, 1.2)
            
            consumption.append({
                'consumption_id': i + 1,
                'customer_id': customer['customer_id'],
                'location_id': location['location_id'],
                'date_key': date_row['date_key'],
                'hour': hour,
                'consumption_kwh': round(consumption_kwh, 2),
                'demand_kw': round(consumption_kwh * np.random.uniform(0.8, 1.0), 2),
                'power_factor': round(np.random.uniform(0.85, 0.99), 2)
            })
        
        return pd.DataFrame(consumption)
    
    def generate_billing(self, customers: pd.DataFrame, 
                         n_months: int = 24) -> pd.DataFrame:
        """Generate billing fact data"""
        billing = []
        bill_id = 0
        
        base_rates = {
            'residential': 1.2,  # HKD per kWh
            'commercial': 1.0,
            'industrial': 0.8
        }
        
        for _, customer in customers.iterrows():
            monthly_base = {
                'residential': 500,
                'commercial': 15000,
                'industrial': 80000
            }[customer['customer_type']]
            
            for month_offset in range(n_months):
                billing_month = pd.Timestamp('2023-01-01') + pd.DateOffset(months=month_offset)
                
                # Seasonal variation
                month = billing_month.month
                if month in [6, 7, 8]:
                    seasonal_factor = 1.3
                elif month in [12, 1, 2]:
                    seasonal_factor = 0.85
                else:
                    seasonal_factor = 1.0
                
                consumption = monthly_base * seasonal_factor * np.random.uniform(0.9, 1.1)
                demand = consumption / 720 * np.random.uniform(1.2, 1.5)
                
                energy_charge = consumption * base_rates[customer['customer_type']]
                demand_charge = demand * 50
                fuel_adjustment = consumption * 0.08
                total = energy_charge + demand_charge + fuel_adjustment
                
                billing.append({
                    'bill_id': bill_id + 1,
                    'customer_id': customer['customer_id'],
                    'billing_month': billing_month,
                    'consumption_kwh': round(consumption, 2),
                    'demand_kw': round(demand, 2),
                    'energy_charge': round(energy_charge, 2),
                    'demand_charge': round(demand_charge, 2),
                    'fuel_adjustment': round(fuel_adjustment, 2),
                    'total_amount': round(total, 2),
                    'payment_status': np.random.choice(
                        ['paid', 'pending', 'overdue'],
                        p=[0.85, 0.10, 0.05]
                    )
                })
                bill_id += 1
        
        return pd.DataFrame(billing)


# ============================================================================
# SQL GENERATOR
# ============================================================================

class SQLGenerator:
    """
    Generate SQL from natural language using LLM.
    
    Uses schema context and few-shot examples for accurate SQL generation.
    """
    
    def __init__(self, config: TextToSQLConfig):
        self.config = config
        self.schema = SCHEMA_DEFINITION
        self.schema_descriptions = SCHEMA_DESCRIPTIONS
        
        # Few-shot examples
        self.examples = [
            {
                "question": "What is the total consumption by district?",
                "sql": """SELECT l.district, SUM(c.consumption_kwh) as total_kwh
FROM fact_consumption c
JOIN dim_location l ON c.location_id = l.location_id
GROUP BY l.district
ORDER BY total_kwh DESC"""
            },
            {
                "question": "Show me the top 10 customers by usage last month",
                "sql": """SELECT cu.customer_id, cu.customer_name, cu.customer_type,
       SUM(co.consumption_kwh) as total_kwh
FROM fact_consumption co
JOIN dim_customer cu ON co.customer_id = cu.customer_id
JOIN dim_time t ON co.date_key = t.date_key
WHERE t.month = strftime('%m', 'now', '-1 month')
  AND t.year = strftime('%Y', 'now', '-1 month')
GROUP BY cu.customer_id, cu.customer_name, cu.customer_type
ORDER BY total_kwh DESC
LIMIT 10"""
            },
            {
                "question": "What is the average bill amount by customer type?",
                "sql": """SELECT cu.customer_type, 
       AVG(b.total_amount) as avg_bill,
       COUNT(*) as num_bills
FROM fact_billing b
JOIN dim_customer cu ON b.customer_id = cu.customer_id
GROUP BY cu.customer_type
ORDER BY avg_bill DESC"""
            },
            {
                "question": "Compare Q1 vs Q2 revenue",
                "sql": """SELECT t.quarter,
       SUM(b.total_amount) as total_revenue,
       COUNT(DISTINCT b.customer_id) as customers
FROM fact_billing b
JOIN dim_time t ON strftime('%Y%m%d', b.billing_month) = t.date_key
WHERE t.quarter IN (1, 2)
GROUP BY t.quarter
ORDER BY t.quarter"""
            },
            {
                "question": "How many active customers are in each region?",
                "sql": """SELECT l.region, COUNT(DISTINCT cu.customer_id) as customer_count
FROM dim_customer cu
JOIN dim_location l ON cu.district = l.district
WHERE cu.is_active = 1
GROUP BY l.region
ORDER BY customer_count DESC"""
            }
        ]
    
    def generate_sql(self, question: str) -> Tuple[str, str]:
        """
        Generate SQL query from natural language question.
        
        Returns:
            Tuple of (sql_query, explanation)
        """
        # Build prompt
        prompt = self._build_prompt(question)
        
        # In production, call LLM API
        # sql = self._call_llm(prompt)
        
        # For demo, use pattern matching
        sql, explanation = self._generate_sql_demo(question)
        
        return sql, explanation
    
    def _build_prompt(self, question: str) -> str:
        """Build the prompt for SQL generation"""
        examples_text = "\n\n".join([
            f"Question: {ex['question']}\nSQL:\n{ex['sql']}"
            for ex in self.examples
        ])
        
        prompt = f"""You are a SQL expert for CLP Power Hong Kong's data warehouse.
Generate a SQL query to answer the user's question.

DATABASE SCHEMA:
{self.schema}

COLUMN DESCRIPTIONS:
{json.dumps(self.schema_descriptions, indent=2)}

EXAMPLES:
{examples_text}

USER QUESTION: {question}

Generate a valid SQLite query. Return only the SQL, no explanations.
SQL:"""
        
        return prompt
    
    def _generate_sql_demo(self, question: str) -> Tuple[str, str]:
        """
        Demo SQL generation using pattern matching.
        In production, this would call GPT-4 or Claude.
        """
        q = question.lower()
        
        # Pattern: consumption by district
        if 'consumption' in q and 'district' in q:
            sql = """SELECT l.district, 
       SUM(c.consumption_kwh) as total_consumption_kwh,
       AVG(c.consumption_kwh) as avg_consumption_kwh,
       COUNT(*) as num_records
FROM fact_consumption c
JOIN dim_location l ON c.location_id = l.location_id
GROUP BY l.district
ORDER BY total_consumption_kwh DESC"""
            explanation = "Aggregating consumption data by district from fact_consumption joined with dim_location"
            return sql, explanation
        
        # Pattern: top customers
        if 'top' in q and 'customer' in q:
            limit = 10
            match = re.search(r'top\s+(\d+)', q)
            if match:
                limit = int(match.group(1))
            
            sql = f"""SELECT cu.customer_id, 
       cu.customer_name, 
       cu.customer_type,
       cu.district,
       SUM(c.consumption_kwh) as total_consumption_kwh
FROM fact_consumption c
JOIN dim_customer cu ON c.customer_id = cu.customer_id
GROUP BY cu.customer_id, cu.customer_name, cu.customer_type, cu.district
ORDER BY total_consumption_kwh DESC
LIMIT {limit}"""
            explanation = f"Finding top {limit} customers by total consumption"
            return sql, explanation
        
        # Pattern: monthly/quarter comparison
        if 'q1' in q or 'q2' in q or 'quarter' in q:
            sql = """SELECT t.year,
       t.quarter,
       SUM(b.total_amount) as total_revenue,
       SUM(b.consumption_kwh) as total_consumption,
       COUNT(DISTINCT b.customer_id) as unique_customers
FROM fact_billing b
JOIN dim_time t ON CAST(strftime('%Y%m%d', b.billing_month) AS INTEGER) = t.date_key
GROUP BY t.year, t.quarter
ORDER BY t.year, t.quarter"""
            explanation = "Comparing quarterly metrics from billing data"
            return sql, explanation
        
        # Pattern: average/mean
        if 'average' in q or 'avg' in q:
            if 'bill' in q:
                sql = """SELECT cu.customer_type,
       cu.district,
       AVG(b.total_amount) as avg_bill_amount,
       AVG(b.consumption_kwh) as avg_consumption,
       COUNT(*) as num_bills
FROM fact_billing b
JOIN dim_customer cu ON b.customer_id = cu.customer_id
GROUP BY cu.customer_type, cu.district
ORDER BY avg_bill_amount DESC"""
                explanation = "Calculating average billing metrics by customer type and district"
            else:
                sql = """SELECT l.district,
       AVG(c.consumption_kwh) as avg_consumption_kwh,
       AVG(c.demand_kw) as avg_demand_kw
FROM fact_consumption c
JOIN dim_location l ON c.location_id = l.location_id
GROUP BY l.district
ORDER BY avg_consumption_kwh DESC"""
                explanation = "Calculating average consumption by district"
            return sql, explanation
        
        # Pattern: count/how many
        if 'how many' in q or 'count' in q:
            if 'customer' in q:
                sql = """SELECT cu.customer_type,
       l.region,
       COUNT(*) as customer_count
FROM dim_customer cu
JOIN dim_location l ON cu.district = l.district
WHERE cu.is_active = 1
GROUP BY cu.customer_type, l.region
ORDER BY customer_count DESC"""
                explanation = "Counting customers by type and region"
            else:
                sql = """SELECT COUNT(*) as total_count FROM dim_customer WHERE is_active = 1"""
                explanation = "Counting total active customers"
            return sql, explanation
        
        # Pattern: revenue/billing
        if 'revenue' in q or 'billing' in q or 'bill' in q:
            sql = """SELECT strftime('%Y-%m', b.billing_month) as month,
       SUM(b.total_amount) as total_revenue,
       SUM(b.energy_charge) as energy_revenue,
       SUM(b.demand_charge) as demand_revenue,
       COUNT(*) as num_bills
FROM fact_billing b
GROUP BY strftime('%Y-%m', b.billing_month)
ORDER BY month DESC
LIMIT 12"""
            explanation = "Summarizing monthly revenue from billing data"
            return sql, explanation
        
        # Pattern: peak/demand
        if 'peak' in q or 'demand' in q:
            sql = """SELECT c.hour,
       AVG(c.demand_kw) as avg_demand_kw,
       MAX(c.demand_kw) as max_demand_kw,
       COUNT(*) as num_records
FROM fact_consumption c
GROUP BY c.hour
ORDER BY c.hour"""
            explanation = "Analyzing demand patterns by hour"
            return sql, explanation
        
        # Pattern: overdue/payment
        if 'overdue' in q or 'payment' in q:
            sql = """SELECT b.payment_status,
       COUNT(*) as num_bills,
       SUM(b.total_amount) as total_amount,
       AVG(b.total_amount) as avg_amount
FROM fact_billing b
GROUP BY b.payment_status
ORDER BY total_amount DESC"""
            explanation = "Summarizing billing by payment status"
            return sql, explanation
        
        # Default: general consumption summary
        sql = """SELECT 
    (SELECT COUNT(*) FROM dim_customer WHERE is_active = 1) as active_customers,
    (SELECT SUM(consumption_kwh) FROM fact_consumption) as total_consumption_kwh,
    (SELECT SUM(total_amount) FROM fact_billing) as total_revenue,
    (SELECT COUNT(DISTINCT district) FROM dim_location) as num_districts"""
        explanation = "Providing general summary statistics"
        return sql, explanation


# ============================================================================
# QUERY EXECUTOR
# ============================================================================

class QueryExecutor:
    """Execute SQL queries safely against the database"""
    
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        return self
    
    def setup_database(self, data_generator: DataGenerator):
        """Create tables and load sample data"""
        if not self.conn:
            self.connect()
        
        cursor = self.conn.cursor()
        
        # Create tables
        cursor.executescript(SCHEMA_DEFINITION)
        
        # Generate and load data
        print("Generating sample data...")
        
        customers = data_generator.generate_customers(500)
        time_dim = data_generator.generate_time_dimension('2024-01-01', '2024-12-31')
        locations = data_generator.generate_locations()
        consumption = data_generator.generate_consumption(customers, locations, time_dim, 20000)
        billing = data_generator.generate_billing(customers, 12)
        
        # Insert data
        customers.to_sql('dim_customer', self.conn, if_exists='replace', index=False)
        time_dim.to_sql('dim_time', self.conn, if_exists='replace', index=False)
        locations.to_sql('dim_location', self.conn, if_exists='replace', index=False)
        consumption.to_sql('fact_consumption', self.conn, if_exists='replace', index=False)
        billing.to_sql('fact_billing', self.conn, if_exists='replace', index=False)
        
        print(f"Loaded: {len(customers)} customers, {len(locations)} locations, "
              f"{len(consumption)} consumption records, {len(billing)} billing records")
        
        return self
    
    def execute(self, sql: str) -> Tuple[pd.DataFrame, Optional[str]]:
        """
        Execute SQL query and return results.
        
        Returns:
            Tuple of (results DataFrame, error message if any)
        """
        try:
            # Basic SQL injection prevention
            if self._is_unsafe(sql):
                return pd.DataFrame(), "Query rejected: potentially unsafe operation"
            
            result = pd.read_sql_query(sql, self.conn)
            return result, None
        except Exception as e:
            return pd.DataFrame(), str(e)
    
    def _is_unsafe(self, sql: str) -> bool:
        """Check for potentially dangerous SQL operations"""
        unsafe_patterns = [
            r'\bDROP\b', r'\bDELETE\b', r'\bTRUNCATE\b',
            r'\bINSERT\b', r'\bUPDATE\b', r'\bALTER\b',
            r'\bCREATE\b', r'\bEXEC\b', r'\bEXECUTE\b'
        ]
        sql_upper = sql.upper()
        for pattern in unsafe_patterns:
            if re.search(pattern, sql_upper):
                return True
        return False
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


# ============================================================================
# RESPONSE FORMATTER
# ============================================================================

class ResponseFormatter:
    """Format query results into human-readable responses"""
    
    def format_response(self, question: str, sql: str, 
                        results: pd.DataFrame, explanation: str) -> str:
        """Format the complete response"""
        response = []
        
        response.append("=" * 60)
        response.append(f"QUESTION: {question}")
        response.append("=" * 60)
        
        response.append("\n📊 SQL QUERY:")
        response.append("-" * 40)
        response.append(sql)
        
        response.append("\n💡 EXPLANATION:")
        response.append(explanation)
        
        response.append("\n📈 RESULTS:")
        response.append("-" * 40)
        
        if results.empty:
            response.append("No data found.")
        else:
            # Format results nicely
            response.append(results.to_string(index=False))
            
            # Add summary statistics
            response.append("\n📌 SUMMARY:")
            response.append(f"   • Rows returned: {len(results)}")
            
            # Numeric column summaries
            numeric_cols = results.select_dtypes(include=[np.number]).columns
            for col in numeric_cols[:3]:  # First 3 numeric columns
                response.append(f"   • {col}: Total={results[col].sum():,.2f}, "
                              f"Avg={results[col].mean():,.2f}")
        
        response.append("\n" + "=" * 60)
        
        return "\n".join(response)


# ============================================================================
# MAIN CONVERSATIONAL ANALYTICS CLASS
# ============================================================================

class ConversationalAnalytics:
    """
    Main class for Text-to-SQL conversational analytics.
    
    Usage:
        analytics = ConversationalAnalytics()
        analytics.setup()
        response = analytics.ask("What is the total consumption by district?")
        print(response)
    """
    
    def __init__(self, config: TextToSQLConfig = None):
        self.config = config or TextToSQLConfig()
        self.sql_generator = SQLGenerator(self.config)
        self.executor = QueryExecutor()
        self.formatter = ResponseFormatter()
        self.is_setup = False
    
    def setup(self):
        """Initialize database with sample data"""
        print("\n" + "=" * 60)
        print("SETTING UP CONVERSATIONAL ANALYTICS")
        print("=" * 60 + "\n")
        
        data_gen = DataGenerator()
        self.executor.connect().setup_database(data_gen)
        self.is_setup = True
        
        print("\nSetup complete! You can now ask questions about the data.")
        print("=" * 60 + "\n")
    
    def ask(self, question: str) -> str:
        """
        Ask a question in natural language.
        
        Args:
            question: Natural language question about the data
        
        Returns:
            Formatted response with SQL, results, and explanation
        """
        if not self.is_setup:
            return "Error: Call setup() first to initialize the database."
        
        # Generate SQL
        sql, explanation = self.sql_generator.generate_sql(question)
        
        # Execute query
        results, error = self.executor.execute(sql)
        
        if error:
            return f"Query Error: {error}\n\nGenerated SQL:\n{sql}"
        
        # Format response
        response = self.formatter.format_response(
            question, sql, results, explanation
        )
        
        return response
    
    def get_sample_questions(self) -> List[str]:
        """Return list of sample questions"""
        return [
            "What is the total consumption by district?",
            "Show me the top 10 customers by usage",
            "What is the average bill amount by customer type?",
            "Compare Q1 vs Q2 revenue",
            "How many active customers are in each region?",
            "What are the peak demand hours?",
            "Show me overdue payments summary",
            "What is the monthly revenue trend?",
        ]
    
    def close(self):
        """Clean up resources"""
        self.executor.close()


# ============================================================================
# PRODUCTION VERSION WITH LLM
# ============================================================================

PRODUCTION_CODE = '''
"""
Production Text-to-SQL using OpenAI GPT-4
"""

from openai import OpenAI
import os

class ProductionSQLGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.schema = SCHEMA_DEFINITION
        self.examples = [...]  # Same as demo
    
    def generate_sql(self, question: str) -> str:
        prompt = self._build_prompt(question)
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a SQL expert. Generate valid SQLite queries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=500
        )
        
        sql = response.choices[0].message.content
        
        # Clean up response
        sql = sql.replace("```sql", "").replace("```", "").strip()
        
        return sql
    
    def _build_prompt(self, question: str) -> str:
        # Same as demo version
        pass


# Using LangChain for more advanced features
from langchain.llms import OpenAI
from langchain.chains import create_sql_query_chain
from langchain.utilities import SQLDatabase

db = SQLDatabase.from_uri("sqlite:///clp_warehouse.db")
llm = OpenAI(model="gpt-4", temperature=0)
chain = create_sql_query_chain(llm, db)

# Query
sql = chain.invoke({"question": "What is the total consumption by district?"})
'''


# ============================================================================
# DEMO
# ============================================================================

def demo():
    """Run demonstration of the Conversational Analytics system"""
    
    print("\n" + "=" * 70)
    print("  CONVERSATIONAL DATA ANALYTICS - TEXT-TO-SQL")
    print("  CLP Power Hong Kong - AI Interview Project")
    print("=" * 70 + "\n")
    
    # Initialize
    analytics = ConversationalAnalytics()
    analytics.setup()
    
    # Demo questions
    questions = [
        "What is the total consumption by district?",
        "Show me the top 5 customers by usage",
        "What is the average bill amount by customer type?",
        "How many customers are in each region?",
        "What are the peak demand hours?",
    ]
    
    print("\n" + "=" * 70)
    print("  RUNNING DEMO QUERIES")
    print("=" * 70)
    
    for question in questions:
        response = analytics.ask(question)
        print(response)
        print("\n")
    
    # Interactive mode
    print("\n" + "=" * 70)
    print("  INTERACTIVE MODE")
    print("  Type 'quit' to exit, 'help' for sample questions")
    print("=" * 70 + "\n")
    
    while True:
        try:
            user_input = input("\n🔍 Your question: ").strip()
        except EOFError:
            break
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            break
        
        if user_input.lower() == 'help':
            print("\nSample questions you can ask:")
            for i, q in enumerate(analytics.get_sample_questions(), 1):
                print(f"  {i}. {q}")
            continue
        
        if user_input:
            response = analytics.ask(user_input)
            print(response)
    
    analytics.close()
    print("\nGoodbye!")


if __name__ == "__main__":
    demo()
