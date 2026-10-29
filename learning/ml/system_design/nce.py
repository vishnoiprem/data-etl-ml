import numpy as np

# Example Data
true_labels = np.array([1, 0, 1, 1, 0])  # True click labels
predicted_probs = np.array([0.9, 0.1, 0.8, 0.6, 0.2])  # Predicted probabilities
background_ctr = np.mean(true_labels)  # Baseline CTR

print(background_ctr)

# Log-loss computation
log_loss = -np.mean(
    ((1 + true_labels) / 2) * np.log(predicted_probs) +
    ((1 - true_labels) / 2) * np.log(1 - predicted_probs)
)

# Background entropy computation
background_entropy = -(background_ctr * np.log(background_ctr) +
                      (1 - background_ctr) * np.log(1 - background_ctr))

# NCE Calculation
nce = log_loss / background_entropy
print(f"Normalized Cross-Entropy (NCE): {nce:.4f}")