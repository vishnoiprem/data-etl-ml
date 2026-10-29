import numpy as np

class Neuron:
    def __init__(self, num_inputs):
        self.weights = np.random.randn(num_inputs) * 0.1
        self.bias = 0.0

    def forward(self, inputs):
        self.last_inputs = inputs
        self.z = np.dot(self.weights, inputs) + self.bias
        self.output = 1 / (1 + np.exp(-self.z))
        return self.output

    def backward(self, dL_dout, learning_rate=0.01):
        sigmoid_derivative = self.output * (1 - self.output)
        local_gradient = dL_dout * sigmoid_derivative

        # Update
        self.weights -= learning_rate * local_gradient * self.last_inputs
        self.bias -= learning_rate * local_gradient

        return local_gradient * self.weights

class Layer:
    def __init__(self, num_inputs, num_neurons):
        self.neurons = [Neuron(num_inputs) for _ in range(num_neurons)]

    def forward(self, inputs):
        self.last_inputs = inputs
        self.outputs = np.array([neuron.forward(inputs) for neuron in self.neurons])
        return self.outputs

    def backward(self, dL_douts, learning_rate=0.01):
        gradients = np.zeros(len(self.neurons[0].weights))
        for i, neuron in enumerate(self.neurons):
            grad = neuron.backward(dL_douts[i], learning_rate)
            gradients += grad
        return gradients

class SimpleNetwork:
    def __init__(self, num_inputs, num_hidden, num_outputs):
        self.hidden = Layer(num_inputs, num_hidden)
        self.output = Layer(num_hidden, num_outputs)

    def forward(self, inputs):
        self.hidden_out = self.hidden.forward(inputs)
        self.output_out = self.output.forward(self.hidden_out)
        return self.output_out

    def backward(self, y_true, learning_rate=0.01):
        # Assume MSE loss
        dL_dout = -(y_true - self.output_out)
        dL_dhidden = self.output.backward(dL_dout, learning_rate)
        self.hidden.backward(dL_dhidden, learning_rate)

# Example usage
np.random.seed(42)
net = SimpleNetwork(num_inputs=2, num_hidden=2, num_outputs=1)

X = np.array([0.5, -0.5])
y_true = np.array([1.0])

for epoch in range(1000):
    y_pred = net.forward(X)
    net.backward(y_true, learning_rate=0.1)
    if epoch % 100 == 0:
        loss = 0.5 * (y_true - y_pred) ** 2
        print(f"Epoch {epoch}, Loss: {loss[0]:.4f}")

print("Final prediction:", net.forward(X))