# Plot the reservations/pizzas dataset.
def train(X, Y, iterations, lr):
    w = 0
    for i in range(iterations):
        current_loss = loss(X, Y, w)
        print("Iteration %4d => Loss: %.6f" % (i, current_loss))

        if loss(X, Y, w + lr) < current_loss:
            w += lr
        elif loss(X, Y, w - lr) < current_loss:
            w -= lr
        else:
            return w

    raise Exception("Couldn't converge within %d iterations" % iterations)

def loss(X, Y, w):
  return np.average((predict(X, w) - Y) ** 2)

def predict(X, w):
  return X * w



import numpy as np
import matplotlib.pyplot as plt
import seaborn as sea
sea.set()
plt.axis([0, 50, 0, 50])                                 # scale axes (0 to 50)
plt.xticks(fontsize=14)                                  # set x axis ticks
plt.yticks(fontsize=14)                                  # set y axis ticks
plt.xlabel("Reservations", fontsize=14)                  # set x axis label
plt.ylabel("Pizzas", fontsize=14)                        # set y axis label
X, Y = np.loadtxt("../../data/pizza.txt", skiprows=1, unpack=True)  # load data
plt.plot(X, Y, "bo")                                     # plot data
plt.show()

# display chart

# Import the dataset
X, Y = np.loadtxt("./../data/pizza.txt", skiprows=1, unpack=True)

# Train the system
w = train(X, Y, iterations=10000, lr=0.01)
print("\nw=%.3f" % w)

# Predict the number of pizzas
print("Prediction: x=%d => y=%.2f" % (20, predict(20, w)))

