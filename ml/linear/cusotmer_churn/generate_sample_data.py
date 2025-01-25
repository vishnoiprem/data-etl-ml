# generate_sample_data.py

import pandas as pd
import numpy as np

def generate_customer_data(n_records=1000, random_state=42):
    """Generate synthetic customer data for testing"""
    np.random.seed(random_state)
    
    # Generate basic customer information
    customer_ids = [f'CUST{str(i).zfill(6)}' for i in range(1, n_records + 1)]
    gender = np.random.choice(['Male', 'Female'], size=n_records)
    senior_citizen = np.random.choice([0, 1], size=n_records, p=[0.85, 0.15])
    partner = np.random.choice(['Yes', 'No'], size=n_records)
    dependents = np.random.choice(['Yes', 'No'], size=n_records)
    
    # Generate service tenure and charges
    tenure = np.random.gamma(shape=2.0, scale=20, size=n_records)
    tenure = np.round(tenure).clip(1, 72)
    
    monthly_charges = np.random.normal(70, 20, n_records).clip(20, 120)
    total_charges = monthly_charges * tenure * np.random.uniform(0.95, 1.05, n_records)
    
    # Generate service choices
    internet_service = np.random.choice(
        ['DSL', 'Fiber optic', 'No'],
        size=n_records,
        p=[0.4, 0.5, 0.1]
    )
    
    phone_service = np.random.choice(['Yes', 'No'], size=n_records, p=[0.9, 0.1])
    
    # Generate contract information
    contract = np.random.choice(
        ['Month-to-month', 'One year', 'Two year'],
        size=n_records,
        p=[0.5, 0.3, 0.2]
    )
    
    paperless_billing = np.random.choice(['Yes', 'No'], size=n_records)
    
    payment_method = np.random.choice(
        ['Electronic check', 'Mailed check', 'Bank transfer', 'Credit card'],
        size=n_records,
        p=[0.4, 0.2, 0.2, 0.2]
    )
    
    # Calculate churn probability and generate churn status
    churn_prob = np.zeros(n_records)
    
    for i in range(n_records):
        base_prob = 0.10
        
        # Factors that increase churn probability
        if contract[i] == 'Month-to-month':
            base_prob += 0.15
        if payment_method[i] == 'Electronic check':
            base_prob += 0.05
        if internet_service[i] == 'Fiber optic':
            base_prob += 0.05
        if monthly_charges[i] > 100:
            base_prob += 0.10
            
        # Factors that decrease churn probability
        base_prob -= (tenure[i] / 72) * 0.10
        
        # Add random variation
        churn_prob[i] = min(max(base_prob + np.random.normal(0, 0.05), 0), 1)
    
    # Generate final churn decisions
    churn = np.random.binomial(1, churn_prob)
    churn = ['Yes' if c == 1 else 'No' for c in churn]
    
    # Create the DataFrame
    df = pd.DataFrame({
        'CustomerID': customer_ids,
        'gender': gender,
        'SeniorCitizen': senior_citizen,
        'Partner': partner,
        'Dependents': dependents,
        'tenure': tenure,
        'PhoneService': phone_service,
        'InternetService': internet_service,
        'Contract': contract,
        'PaperlessBilling': paperless_billing,
        'PaymentMethod': payment_method,
        'MonthlyCharges': np.round(monthly_charges, 2),
        'TotalCharges': np.round(total_charges, 2),
        'Churn': churn
    })
    
    return df