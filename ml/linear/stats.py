import numpy as np

data = [1, 2, 2, 3, 4, 7, 9]
mean = np.mean(data)
print(f"Mean: {mean}")


median = np.median(data)
print(f"Median: {median}")


from scipy import stats

mode = stats.mode(data)
print(f"Mode: {mode}")

variance = np.var(data)
print(f"Variance: {variance}")


std_dev = np.std(data)
print(f"Standard Deviation: {std_dev}")

range_val = np.ptp(data)
print(f"Range: {range_val}")