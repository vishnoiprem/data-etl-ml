import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from scipy.stats import binom, norm, ttest_1samp, sem
from sklearn.linear_model import LinearRegression

# ------------------------------
# 1. Probability Basics
# ------------------------------

# A. Basic Probability
def simulate_coin_toss():
    flips = [np.random.choice(['heads', 'tails']) for _ in range(1000)]
    heads_count = flips.count('heads')
    prob_heads = heads_count / 1000
    print(f"Probability of getting heads: {prob_heads}")

simulate_coin_toss()

# B. Conditional Probability
def conditional_probability():
    p_rain_and_cloudy = 0.4  # P(A ∩ B)
    p_cloudy = 0.5  # P(B)
    p_rain_given_cloudy = p_rain_and_cloudy / p_cloudy
    print(f"Probability of rain given it's cloudy: {p_rain_given_cloudy}")

conditional_probability()

# C. Bayes’ Theorem
def bayes_theorem_example():
    p_disease = 0.01
    p_pos_given_disease = 0.99
    p_pos_given_no_disease = 0.05
    p_no_disease = 1 - p_disease

    p_positive_test = (p_pos_given_disease * p_disease) + (p_pos_given_no_disease * p_no_disease)
    p_disease_given_positive = (p_pos_given_disease * p_disease) / p_positive_test

    print(f"Probability of having the disease given a positive test: {p_disease_given_positive}")

bayes_theorem_example()

# D. Binomial Distribution
def binomial_distribution_example():
    n = 10  # number of trials
    p = 0.5  # probability of success
    prob_5_successes = binom.pmf(5, n, p)
    print(f"Probability of 5 successes out of 10: {prob_5_successes}")

binomial_distribution_example()

# E. Normal Distribution
def normal_distribution_example():
    mu, sigma = 0, 1  # mean and standard deviation
    s = np.random.normal(mu, sigma, 1000)
    plt.hist(s, bins=30, density=True)
    plt.title('Normal Distribution')
    plt.show()

normal_distribution_example()

# ------------------------------
# 2. Descriptive Statistics
# ------------------------------

data = [1, 2, 2, 3, 4, 7, 9]

# A. Measures of Central Tendency
def descriptive_statistics(data):
    mean = np.mean(data)
    median = np.median(data)
    mode = stats.mode(data)
    print(f"Mean: {mean}, Median: {median}, Mode: {mode}")

descriptive_statistics(data)

# B. Measures of Dispersion
def dispersion_statistics(data):
    variance = np.var(data)
    std_dev = np.std(data)
    range_val = np.ptp(data)
    print(f"Variance: {variance}, Standard Deviation: {std_dev}, Range: {range_val}")

dispersion_statistics(data)

# ------------------------------
# 3. Inferential Statistics
# ------------------------------

# A. Hypothesis Testing - T-Test
def t_test_example():
    sample_data = [1.83, 1.93, 1.85, 1.78, 1.82]
    t_statistic, p_value = ttest_1samp(sample_data, 1.8)
    print(f"T-Statistic: {t_statistic}, P-Value: {p_value}")

t_test_example()

# B. Confidence Intervals
def confidence_interval_example():
    sample_data = [1.83, 1.93, 1.85, 1.78, 1.82]
    confidence_level = 0.95
    degrees_freedom = len(sample_data) - 1
    sample_mean = np.mean(sample_data)
    sample_standard_error = sem(sample_data)

    confidence_interval = stats.t.interval(confidence_level, degrees_freedom, sample_mean, sample_standard_error)
    print(f"95% Confidence Interval: {confidence_interval}")

confidence_interval_example()

# C. Regression Analysis
def regression_example():
    X = np.array([[1], [2], [3], [4], [5]])
    y = np.array([1, 2, 1.5, 3.5, 2])

    model = LinearRegression()
    model.fit(X, y)
    predictions = model.predict(X)

    print(f"Coefficients: {model.coef_}, Intercept: {model.intercept_}")
    print(f"Predictions: {predictions}")

regression_example()

# ------------------------------
# 4. Advanced Topics in Probability and Statistics
# ------------------------------

# A. Central Limit Theorem
def central_limit_theorem_example():
    sample_means = []
    for _ in range(1000):
        sample = np.random.choice(data, size=30, replace=True)
        sample_means.append(np.mean(sample))

    plt.hist(sample_means, bins=30, density=True)
    plt.title('Distribution of Sample Means')
    plt.show()

central_limit_theorem_example()