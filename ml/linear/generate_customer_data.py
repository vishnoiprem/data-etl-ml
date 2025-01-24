import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set random seed for reproducibility
np.random.seed(42)

# Number of records to generate
n_records = 1000


def generate_customer_data():
    """
    Generate synthetic customer data with realistic patterns and relationships.
    The data includes customer demographics, service usage, and churn status.
    """

    # Generate customer IDs
    customer_ids = [f'CUST{str(i).zfill(6)}' for i in range(1, n_records + 1)]

    # Generate tenure (months)
    tenure = np.random.gamma(shape=2.0, scale=20, size=n_records)
    tenure = np.round(tenure).clip(1, 72)  # Clip to realistic range

    # Generate monthly charges with some correlation to services
    base_charge = np.random.normal(50, 10, n_records)
    service_multiplier = np.random.uniform(1, 2.5, n_records)
    monthly_charges = base_charge * service_multiplier
    monthly_charges = monthly_charges.clip(20, 120)  # Clip to realistic range

    # Calculate total charges with some random variation
    total_charges = (monthly_charges * tenure *
                     np.random.uniform(0.95, 1.05, n_records))  # Add some noise

    # Generate contract types with realistic distribution
    contract_types = np.random.choice(
        ['Month-to-month', '1 year', '2 year'],
        size=n_records,
        p=[0.5, 0.3, 0.2]  # Realistic probabilities
    )

    # Generate payment methods
    payment_methods = np.random.choice(
        ['Electronic check', 'Mailed check', 'Bank transfer', 'Credit card'],
        size=n_records,
        p=[0.4, 0.2, 0.2, 0.2]
    )

    # Generate internet service types
    internet_service = np.random.choice(
        ['DSL', 'Fiber optic', 'No'],
        size=n_records,
        p=[0.4, 0.5, 0.1]
    )

    # Generate additional services based on internet service
    online_security = []
    online_backup = []
    device_protection = []
    tech_support = []
    streaming_tv = []
    streaming_movies = []

    for service in internet_service:
        if service == 'No':
            # No internet means no additional services
            online_security.append('No internet service')
            online_backup.append('No internet service')
            device_protection.append('No internet service')
            tech_support.append('No internet service')
            streaming_tv.append('No internet service')
            streaming_movies.append('No internet service')
        else:
            # With internet, generate random services with realistic probabilities
            online_security.append(np.random.choice(['Yes', 'No'], p=[0.4, 0.6]))
            online_backup.append(np.random.choice(['Yes', 'No'], p=[0.4, 0.6]))
            device_protection.append(np.random.choice(['Yes', 'No'], p=[0.3, 0.7]))
            tech_support.append(np.random.choice(['Yes', 'No'], p=[0.3, 0.7]))
            streaming_tv.append(np.random.choice(['Yes', 'No'], p=[0.5, 0.5]))
            streaming_movies.append(np.random.choice(['Yes', 'No'], p=[0.5, 0.5]))

    # Generate phone service and multiple lines
    phone_service = np.random.choice(['Yes', 'No'], size=n_records, p=[0.9, 0.1])
    multiple_lines = []
    for has_phone in phone_service:
        if has_phone == 'No':
            multiple_lines.append('No phone service')
        else:
            multiple_lines.append(np.random.choice(['Yes', 'No'], p=[0.4, 0.6]))

    # Calculate churn probability based on various factors
    churn_prob = np.zeros(n_records)

    # Increase churn probability based on various factors
    for i in range(n_records):
        base_prob = 0.1  # Base churn probability

        # Contract type impact
        if contract_types[i] == 'Month-to-month':
            base_prob += 0.15

        # Payment method impact
        if payment_methods[i] == 'Electronic check':
            base_prob += 0.05

        # Service impact
        if internet_service[i] == 'Fiber optic':
            base_prob += 0.05

        # Tenure impact (longer tenure = lower churn)
        base_prob -= (tenure[i] / 72) * 0.1

        # Price sensitivity
        if monthly_charges[i] > 100:
            base_prob += 0.1

        # Add some randomness
        churn_prob[i] = min(max(base_prob + np.random.normal(0, 0.1), 0), 1)

    # Generate final churn decisions
    churn = np.random.binomial(1, churn_prob)
    churn = ['Yes' if c == 1 else 'No' for c in churn]

    # Create the DataFrame
    df = pd.DataFrame({
        'CustomerID': customer_ids,
        'gender': np.random.choice(['Male', 'Female'], size=n_records),
        'SeniorCitizen': np.random.choice([0, 1], size=n_records, p=[0.85, 0.15]),
        'Partner': np.random.choice(['Yes', 'No'], size=n_records),
        'Dependents': np.random.choice(['Yes', 'No'], size=n_records),
        'tenure': tenure,
        'PhoneService': phone_service,
        'MultipleLines': multiple_lines,
        'InternetService': internet_service,
        'OnlineSecurity': online_security,
        'OnlineBackup': online_backup,
        'DeviceProtection': device_protection,
        'TechSupport': tech_support,
        'StreamingTV': streaming_tv,
        'StreamingMovies': streaming_movies,
        'Contract': contract_types,
        'PaperlessBilling': np.random.choice(['Yes', 'No'], size=n_records),
        'PaymentMethod': payment_methods,
        'MonthlyCharges': np.round(monthly_charges, 2),
        'TotalCharges': np.round(total_charges, 2),
        'Churn': churn
    })

    return df


# Generate the data
customer_df = generate_customer_data()

# Save to CSV
customer_df.to_csv('customer_data.csv', index=False)

# Print summary statistics
print("\nDataset Summary:")
print(f"Total Records: {len(customer_df)}")
print(f"Churn Rate: {(customer_df['Churn'] == 'Yes').mean():.2%}")
print("\nNumerical Features Summary:")
print(customer_df[['tenure', 'MonthlyCharges', 'TotalCharges']].describe())
print("\nCategory Distributions:")
for col in ['InternetService', 'Contract', 'PaymentMethod']:
    print(f"\n{col}:")
    print(customer_df[col].value_counts(normalize=True).round(3))
