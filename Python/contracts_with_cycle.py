# Example 1: Cycle present
contracts_with_cycle = {
    "A": ["B"],
    "B": ["C"],
    "C": ["A"]  # A -> B -> C -> A (cycle!)
}

# Example 2: No cycle
contracts_no_cycle = {
    "A": ["B"],
    "B": ["C"],
    "C": []      # A -> B -> C (no cycle)
}



def detect_cycle(graph):
    visited = []
    path = []

    def dfs(contract):
        if contract in path:
            return True  # cycle detected
        if contract in visited:
            return False

        path.append(contract)
        for called in graph.get(contract, []):
            if dfs(called):
                return True
        path.pop()
        visited.append(contract)
        return False

    for contract in graph:
        print(contract)
        if dfs(contract):
            return True
    return False

print("Cycle in contracts_with_cycle:", detect_cycle(contracts_with_cycle))  # True
# print("Cycle in contracts_no_cycle:", detect_cycle(contracts_no_cycle))      # False