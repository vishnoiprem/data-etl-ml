def has_cycle(graph):
    visited = set()
    stack = set()

    def dfs(node):
        if node in stack:
            return True  # Cycle detected
        if node in visited:
            return False

        visited.add(node)
        stack.add(node)

        for neighbor in graph.get(node, []):
            if dfs(neighbor):
                return True

        stack.remove(node)
        return False

    for node in graph:
        if dfs(node):
            return True
    return False

# Example 1: Contract dependency graph WITH cycle
dependency_graph_with_cycle = {
    "Token": ["Exchange"],
    "Exchange": ["Wallet"],
    "Wallet": ["Token"]  # Cycle: Token -> Exchange -> Wallet -> Token
}

# Example 2: Contract dependency graph WITHOUT cycle
dependency_graph_without_cycle = {
    "Token": ["Exchange"],
    "Exchange": ["Wallet"],
    "Wallet": []
}
print("With cycle:", has_cycle(dependency_graph_with_cycle))      # True
print("Without cycle:", has_cycle(dependency_graph_without_cycle))  # False