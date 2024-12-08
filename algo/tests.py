import random
import unittest
from blossom import blossom_algorithm
from brute_force import brute_force_algorithm


class TestBlossomAlgorithm(unittest.TestCase):
    def test_basic_case(self):
        edges = [
            [0, 1, 10],
            [1, 2, 5],
            [0, 2, 15]
        ]
        result = blossom_algorithm(edges)
        self.assertEqual(sorted(result), sorted([(0, 2)]))

    def test_disconnected_graph(self):
        edges = [
            [0, 1, 10],
            [2, 3, 5],
        ]
        result = blossom_algorithm(edges)
        self.assertEqual(sorted(result), sorted([(0, 1), (2, 3)]))

    def test_single_edge(self):
        edges = [[0, 1, 100]]
        result = blossom_algorithm(edges)
        self.assertEqual(sorted(result), [(0, 1)])

    def test_no_edges(self):
        edges = []
        result = blossom_algorithm(edges)
        self.assertEqual(result, [])

    def test_huge_case(self):
        for _ in range(10):
            edges = self.generate_graph()
            correct_pairs, correct_result = brute_force_algorithm(edges)
            pairs = blossom_algorithm(edges)
            result = sum([w for i, j, w in edges if (i, j) in pairs])
            self.assertEqual(correct_result, result)

    def generate_graph(self):
        n = random.randint(10, 15)
        edges = []
        for i in range(n):
            for j in range(i + 1, n):
                if random.randint(1, 4) == 1:
                    edges.append([i, j, random.randint(1, 100)])
        return edges

