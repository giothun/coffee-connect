import random
import unittest

from matching import greedy, compare
from blossom import blossom_algorithm
from brute_force import brute_force_algorithm


class TestBlossomAlgorithm(unittest.TestCase):
    def test_basic_case(self):
        edges = [
            [0, 1, 10],
            [1, 2, 5],
            [0, 2, 15]
        ]
        result, weight = blossom_algorithm(edges)
        self.assertEqual(sorted(result), sorted([(0, 2)]))

    def test_disconnected_graph(self):
        edges = [
            [0, 1, 10],
            [2, 3, 5],
        ]
        result, weight = blossom_algorithm(edges)
        self.assertEqual(sorted(result), sorted([(0, 1), (2, 3)]))

    def test_single_edge(self):
        edges = [[0, 1, 100]]
        result, weight = blossom_algorithm(edges)
        self.assertEqual(sorted(result), [(0, 1)])

    def test_no_edges(self):
        edges = []
        result, weight = blossom_algorithm(edges)
        self.assertEqual(result, [])

    def test_huge_case(self):
        for _ in range(10):
            edges = self.generate_graph(10, 15)
            correct_pairs, correct_result = brute_force_algorithm(edges)
            pairs, weight = blossom_algorithm(edges)
            self.assertEqual(correct_result, weight)

    def test_compare_with_greedy(self):
        num = 5000
        cnt = 0
        sm = 0
        more_pairs = 0
        for _ in range(num):
            edges = self.generate_graph(50, 100)
            f = compare(edges, blossom_algorithm, greedy)
            self.assertTrue(f)
            greedy_pairs, greedy_result = greedy(edges)
            pairs, result = blossom_algorithm(edges)
            cnt += result - greedy_result
            sm += greedy_result
            if len(pairs) > len(greedy_pairs):
                more_pairs += 1
        print(f"Blossom algorithm found a bigger matching in {(more_pairs / num * 100):0,.2f}% cases")
        print(f"Blossom algorithm outperformed greedy by {(cnt / sm * 100):0,.2f}%")

    def generate_graph(self, l, r):
        n = random.randint(l, r)
        edges = []
        cnt = 0
        for i in range(n):
            for j in range(i + 1, n):
                if random.randint(1, 4) == 1:
                    cnt += 1
                    edges.append([i, j, random.randint(1, 100)])
        if cnt == 0:
            edges.append([0, 1, 100])
        return edges
