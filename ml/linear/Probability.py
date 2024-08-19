import random

# Simulate flipping a coin 1000 times
flips = [random.choice(['heads', 'tails']) for _ in range(1000)]
# print(flips)
heads_count = flips.count('heads')
prob_heads = heads_count / 1000

# print(f"Probability of getting heads: {prob_heads}")

# Example probabilities
p_rain_and_cloudy = 0.4  # P(A ∩ B)
p_cloudy = 0.5  # P(B)

p_rain_given_cloudy = p_rain_and_cloudy / p_cloudy
# print(f"Probability of rain given it's cloudy: {p_rain_given_cloudy}")






# Probabilities
p_disease = 0.01
p_pos_given_disease = 0.99
p_pos_given_no_disease = 0.05
p_no_disease = 1 - p_disease

# Bayes' Theorem
p_positive_test = (p_pos_given_disease * p_disease) + (p_pos_given_no_disease * p_no_disease)
p_disease_given_positive = (p_pos_given_disease * p_disease) / p_positive_test

# print(f"Probability of having the disease given a positive test: {p_disease_given_positive}")



from scipy.stats import binom

# Parameters
n = 10  # number of trials
p = 0.5  # probability of success

# Probability of getting exactly 5 successes in 10 trials
prob_5_successes = binom.pmf(5, n, p)
# print(f"Probability of 5 successes out of 10: {prob_5_successes}")


import numpy as np
import matplotlib.pyplot as plt

mu, sigma = 0, 1  # mean and standard deviation
s = np.random.normal(mu, sigma, 1000)

plt.hist(s, bins=30, density=True)
plt.title('Normal Distribution')
plt.show()