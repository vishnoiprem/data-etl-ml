import matplotlib.pyplot as plt

# Sample sizes
sample_sizes = list(range(1000, 21000, 1000))

# Replace these with your measured values
xgb_times = [0.23, 0.35, 0.56, 0.79, 1.05, 1.34, 1.56, 1.88, 2.27, 3.14, 3.9, 4.4, 5.2, 5.8, 6.5, 7.1, 7.7, 8.3, 9.0, 9.7]
lgbm_times = [0.09, 0.12, 0.19, 0.22, 0.28, 0.32, 0.41, 0.47, 0.56, 0.9, 1.1, 1.3, 1.5, 1.7, 1.9, 2.0, 2.1, 2.3, 2.4, 2.6]

xgb_accuracies = [0.87, 0.88, 0.89, 0.89, 0.89, 0.89, 0.90, 0.90, 0.89, 0.90, 0.90, 0.91, 0.91, 0.91, 0.91, 0.91, 0.91, 0.91, 0.91, 0.91]
lgbm_accuracies = [0.88, 0.89, 0.89, 0.90, 0.90, 0.90, 0.90, 0.90, 0.91, 0.90, 0.90, 0.91, 0.91, 0.91, 0.91, 0.91, 0.91, 0.91, 0.91, 0.91]


plt.figure(figsize=(10, 6))
plt.plot(sample_sizes, xgb_times, label='XGBoost', marker='o')
plt.plot(sample_sizes, lgbm_times, label='LightGBM', marker='s')
plt.title('Training Time vs Sample Size')
plt.xlabel('Sample Size')
plt.ylabel('Training Time (seconds)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()



plt.figure(figsize=(10, 6))
plt.plot(sample_sizes, xgb_accuracies, label='XGBoost', marker='o')
plt.plot(sample_sizes, lgbm_accuracies, label='LightGBM', marker='s')
plt.title('Accuracy vs Sample Size')
plt.xlabel('Sample Size')
plt.ylabel('Accuracy')
plt.ylim(0.85, 1.0)  # Focused view
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
