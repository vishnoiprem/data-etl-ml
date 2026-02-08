# File: caching_analysis.py
"""
Quick analysis to compare in-house vs. managed Redis cache.
Used to inform a technical decision discussion.
"""

import pandas as pd

# Hypothetical data based on research and past projects
data = {
    'Criteria': ['Time to Market (weeks)', 'Ops Load (FTE months/year)',
                 'High-Availability Setup', 'Peak Throughput (req/sec)',
                 'Estimated 3-year Cost (USD)'],
    'In-House Redis': [6, 0.5, 'Manual cluster setup', 50_000, 85_000],  # Hardware, ops salary, etc.
    'Managed ElastiCache': [2, 0.1, 'Automated failover', 100_000, 45_000],  # Subscription cost
}

df = pd.DataFrame(data).set_index('Criteria')

# Add a derived column for quick comparison
def get_recommendation(row):
    if row.name == 'Estimated 3-year Cost (USD)':
        return 'Managed' if row['Managed ElastiCache'] < row['In-House Redis'] else 'In-House'
    elif row.name in ['Time to Market (weeks)', 'Ops Load (FTE months/year)']:
        return 'Managed' if row['Managed ElastiCache'] < row['In-House Redis'] else 'In-House'
    elif row.name == 'Peak Throughput (req/sec)':
        return 'Managed' if row['Managed ElastiCache'] > row['In-House Redis'] else 'In-House'
    else:
        return 'N/A'

df['Recommendation'] = df.apply(get_recommendation, axis=1)

print("=== Caching Solution Analysis ===")
print("(For discussion with Tech Lead/Manager)")
print("\nKey Trade-offs:")
print(df.to_string())
print("\n---")
print("Proposal: Use Managed ElastiCache for MVP to hit deadline,")
print("and re-evaluate for Phase 2 if cost becomes a concern.")
print("This gives us robustness and lets the team focus on core features.")