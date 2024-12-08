from config import INFINITY
from blossom import blossom_algorithm


# Greedy approach to compare with smart algorithm
def greedy(graph):
    edges = sorted(graph, key=lambda x: -x[2])
    n = max([i for i, j, w in graph]) + 1
    used = [0] * n
    cost = 0
    res = []
    for value, i, j in edges:
        if used[i] == 0 and used[j] == 0:
            used[i] = 1
            used[j] = 1
            cost += value
            res.append([i, j])
    return res, cost


# Function to make an offset in the graph so that the implementation of algorithm is easier
def preprocess_graph(graph):
    return [[0] * (len(graph) + 1), *([0] + graph[i] for i in range(len(graph)))]


# Hungarian algorithm to find the best matching
# Returns the result as pairs of vertices that are matched
def hungarian_algorithm(graph):
    graph = preprocess_graph(graph)
    n = len(graph)
    u = [0] * n
    v = [0] * n
    p = [0] * n
    way = [0] * n
    for i in range(1, n):
        p[0] = i
        j0 = 0
        minv = [INFINITY] * n
        used = [0] * n
        while True:
            used[j0] = 1
            i0 = p[j0]
            delta = INFINITY
            j1 = 0
            for j in range(1, n):
                if used[j] == 0:
                    cur = graph[i0][j] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j
            for j in range(0, n):
                if used[j] != 0:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break
    res = []
    print(p)
    used = [0] * n
    for i in range(1, len(p)):
        if p[i] != 0 and p[i] != i and used[p[i]] == 0 and used[i] == 0:
            used[i] = 1
            used[p[i]] = 1
            res.append([i - 1, p[i] - 1])
            p[p[i]] = 0
    print(res)
    # print(-v[0])
    return res, -v[0]


# Function that compares which algorithm finds a better matching
# Returns True if first algorithm did not worse, False otherwise
def compare(graph, f1, f2):
    _, cost1 = f1(graph)
    _, cost2 = f2(graph)
    return cost2 >= cost1


# Takes graph (dict where key is user id, and value is a list of user id that are connected)
# Returns a list of pairs representing new connections for current week
def create_new_pairs(graph):
    pairs = blossom_algorithm(graph)
    # print(pairs)
    return pairs
