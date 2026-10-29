from scipy.stats import ttest_1samp
import numpy as np
# Sample data
sample_data = [1.83, 1.93, 1.85, 1.78, 1.82]

# Null hypothesis: Mean height = 1.8
t_statistic, p_value = ttest_1samp(sample_data, 1.8)

print(f"T-Statistic: {t_statistic}, P-Value: {p_value}")


import scipy.stats as st

confidence_level = 0.95
degrees_freedom = len(sample_data) - 1
sample_mean = np.mean(sample_data)
sample_standard_error = st.sem(sample_data)

confidence_interval = st.t.interval(confidence_level, degrees_freedom, sample_mean, sample_standard_error)

print(f"95% Confidence Interval: {confidence_interval}")

from sklearn.linear_model import LinearRegression
import numpy as np

# Example data
X = np.array([[1], [2], [3], [4], [5]])
y = np.array([1, 2, 1.5, 3.5, 2])

model = LinearRegression()
model.fit(X, y)
predictions = model.predict(X)

print(f"Coefficients: {model.coef_}, Intercept: {model.intercept_}")

sample_means = []
data =[1, 2, 3, 4, 5]
for _ in range(1000):
    sample = np.random.choice(data, size=30, replace=True)

