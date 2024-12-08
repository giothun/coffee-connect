from itertools import combinations


def is_valid_matching(edges):
    used_vertices = set()
    for u, v, _ in edges:
        if u in used_vertices or v in used_vertices:
            return False
        used_vertices.add(u)
        used_vertices.add(v)
    return True


def calculate_weight(edges):
    return sum(w for _, _, w in edges)


# This is the function that brute forces all possible matching and finds the max one
# It is used for stress tests
def brute_force_algorithm(edges):
    max_weight = float('-inf')
    max_matching = []
    m = len(edges)

    for r in range(1, m + 1):
        for subset in combinations(edges, r):
            if is_valid_matching(subset):
                if len(subset) == len(max_matching):
                    weight = calculate_weight(subset)
                    if weight > max_weight:
                        max_weight = weight
                        max_matching = subset
                if len(subset) > len(max_matching):
                    max_weight = calculate_weight(subset)
                    max_matching = subset
    return max_matching, max_weight
