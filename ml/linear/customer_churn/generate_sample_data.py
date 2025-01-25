import pandas as pd
import numpy as np


def generate_sample_data(n_samples=1000, random_state=42):
    """Generates synthetic sample data for the churn model."""

    np.random.seed(random_state)

    # Generate customer IDs
    customer_ids = [f"CUST_{i:05d}" for i in range(n_samples)]

    # Generate demographic data
    gender = np.random.choice(['Male', 'Female'], size=n_samples)
    senior_citizen = np.random.choice([0, 1], size=n_samples, p=[0.8, 0.2])
    partner = np.random.choice(['Yes', 'No'], size=n_samples)
    dependents = np.random.choice(['Yes', 'No'], size=n_samples)

    # Generate service data
    tenure = np.random.randint(1, 73, size=n_samples)
    phone_service = np.random.choice(['Yes', 'No'], size=n_samples, p=[0.9, 0.1])
    internet_service = np.random.choice(['DSL', 'Fiber optic', 'No'], size=n_samples, p=[0.3, 0.5, 0.2])
    paperless_billing = np.random.choice(['Yes', 'No'], size=n_samples)

    # Generate contract and payment data
    # contract = np.random.choice(['Month-to-month', 'One year', 'Two year'], size=n_samples, p=[0.6, 0.2, 0.2])
    contract = pd.Series(np.random.choice(['Month-to-month', 'One year', 'Two year'], size=n_samples, p=[0.6, 0.2, 0.2]))

    # payment_method = np.random.choice(
    #     ['Electronic check', 'Mailed check', 'Bank transfer (automatic)', 'Credit card (automatic)'],
    #     size=n_samples, p=[0.3, 0.2, 0.25, 0.25])
    payment_method = pd.Series(np.random.choice(
        ['Electronic check', 'Mailed check', 'Bank transfer (automatic)', 'Credit card (automatic)'],
        size=n_samples, p=[0.3, 0.2, 0.25, 0.25]))

    # Generate charges data
    monthly_charges = np.round(np.random.normal(60, 30, size=n_samples).clip(0), 2)
    total_charges = (monthly_charges * tenure).round(2)
    total_charges[np.random.rand(n_samples) <= 0.01] = 0  # Simulate some 0 values

    # Generate churn data
    churn_probs = 0.1 + 0.1 * (internet_service == 'Fiber optic') + 0.05 * (contract == 'Month-to-month')
    churn_probs += 0.02 * (tenure < 12) + 0.02 * (payment_method.str.contains('check'))
    churn = (np.random.rand(n_samples) < churn_probs).astype(int)
    churn = ['Yes' if c == 1 else 'No' for c in churn]

    # Create the final dataframe
    data = {
        'CustomerID': customer_ids,
        'gender': gender,
        'SeniorCitizen': senior_citizen,
        'Partner': partner,
        'Dependents': dependents,
        'tenure': tenure,
        'PhoneService': phone_service,
        'InternetService': internet_service,
        'PaperlessBilling': paperless_billing,
        'Contract': contract,
        'PaymentMethod': payment_method,
        'MonthlyCharges': monthly_charges,
        'TotalCharges': total_charges.astype(str),  # To simulate messy data
        'Churn': churn
    }

    df = pd.DataFrame(data)
    return df
