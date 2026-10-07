"""Portable observation-only regressions, separate from the frozen audit census."""
import copy
from fractions import Fraction as F
from itertools import permutations
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
import check
import exact
import produce


def literal_scene(u, repeats=1, rotate=False):
    """Direct coordinates and calibrated row pairs; no artifact matrix helpers."""
    points = [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)] * repeats
    x = [[F(point[i]) + u * sum(point) for point in points] for i in range(3)]
    y = []
    for i, j in [(0, 1), (1, 2), (2, 0)]:
        if rotate:
            y.extend([[F(3, 5) * a + F(4, 5) * b for a, b in zip(x[i], x[j])],
                      [-F(4, 5) * a + F(3, 5) * b for a, b in zip(x[i], x[j])]])
        else:
            y.extend([list(x[i]), list(x[j])])
    gram = [[sum(x[k][i] * x[k][j] for k in range(3))
             for j in range(len(points))] for i in range(len(points))]
    return x, y, gram


def literal_cases():
    return [(u, repeats, rotate, literal_scene(u, repeats, rotate))
            for u in [F(0), F(1, 3), F(1)]
            for repeats in [1, 8] for rotate in [False, True]]


def determinant_literal(a):
    total = F(0)
    for order in permutations(range(len(a))):
        inversions = sum(order[i] > order[j] for i in range(len(a))
                         for j in range(i + 1, len(a)))
        term = F((-1) ** inversions)
        for i, j in enumerate(order):
            term *= a[i][j]
        total += term
    return total


def invalid_inputs():
    _, y, _ = literal_scene(F(1), 8)
    uncentered = copy.deepcopy(y)
    uncentered[0][-1] += 1
    rank_four = copy.deepcopy(y)
    rank_four[0][-2] += 1
    rank_four[0][-1] -= 1
    rank_two = [list(row) for row in y[:2]]
    # The first 30 columns retain rank three; column 30 adds a fourth pivot.
    return [[], y[:3], [y[0], y[1][:-1]], uncentered, rank_two, rank_four]


def mutated_records():
    _, y, _ = literal_scene(F(1))
    failure = exact.encode(produce.data_only(y))
    _, boundary_y, _ = literal_scene(F(1, 3))
    boundary = exact.encode(produce.data_only(boundary_y))
    records = []
    changed = copy.deepcopy(failure)
    changed['effective_covariance'][0][0] = '987'
    records.append(changed)
    changed = copy.deepcopy(failure)
    changed['recovered_gram'][0][0] = '987'
    records.append(changed)
    changed = copy.deepcopy(failure)
    changed['finite_failure_witness']['strict_gap'] = '0'
    records.append(changed)
    changed = copy.deepcopy(boundary)
    changed['scene_recovers_width_four'] = False
    records.append(changed)
    return records


def snapshot():
    records = [exact.encode(produce.data_only(scene[1]))
               for _, _, _, scene in literal_cases()]
    payload = json.loads((ROOT / 'results' / 'certificates.json').read_text(encoding='utf-8'))
    retained = [exact.encode(produce.data_only(exact.mat(item['Y'])))
                for item in payload['data_only_certificates']]
    rejected = []
    for y in invalid_inputs():
        try:
            produce.data_only(y)
        except ValueError as error:
            rejected.append([type(error).__name__, str(error)])
        else:
            rejected.append(['accepted'])
    mutation_results = []
    for record in mutated_records():
        try:
            check.check_data_only(record)
        except ValueError as error:
            mutation_results.append([type(error).__name__, str(error)])
        else:
            mutation_results.append(['accepted'])
    return {'literal_certificates': records, 'retained_certificates': retained,
            'invalid_inputs': rejected, 'mutation_results': mutation_results}


class ObservationOnlyRegression(unittest.TestCase):
    def test_literal_gram_boundary_and_strict_failure(self):
        for u, repeats, rotate, (x, y, gram) in literal_cases():
            with self.subTest(u=u, repeats=repeats, rotate=rotate):
                record = produce.data_only(y)
                self.assertEqual(record['recovered_gram'], gram)
                self.assertEqual(record['scene_recovers_width_four'], u <= F(1, 3))
                check.check_data_only(exact.encode(record))
                if u > F(1, 3):
                    witness = record['finite_failure_witness']
                    true_energy = sum(v * v for row in x for v in row)
                    self.assertEqual(witness['true_energy'], true_energy)
                    self.assertGreater(witness['strict_gap'], 0)
                    self.assertEqual(witness['strict_gap'], true_energy - witness['witness_energy'])
        payload = json.loads((ROOT / 'results' / 'certificates.json').read_text(encoding='utf-8'))
        self.assertEqual(len(payload['data_only_certificates']), 4)
        for original in payload['data_only_certificates']:
            current = exact.encode(produce.data_only(exact.mat(original['Y'])))
            expected = {k: v for k, v in original.items() if k != 'reference_gram'}
            self.assertEqual(current, expected)
            self.assertEqual(current['recovered_gram'], original['reference_gram'])
            check.check_data_only(original)

    def test_complete_rank_rejections_and_checker_mutations(self):
        rank_four = invalid_inputs()[-1]
        self.assertEqual(check.integer_rank([r[:30] for r in rank_four]), 3)
        self.assertNotEqual(determinant_literal([[rank_four[i][j] for j in [0, 1, 2, 30]]
                                                for i in [0, 1, 3, 5]]), 0)
        for y in invalid_inputs():
            with self.assertRaises(ValueError):
                produce.data_only(y)
        for record in mutated_records():
            with self.assertRaises(ValueError):
                check.check_data_only(record)

    def test_one_complete_observation_elimination_and_baseline_inverse(self):
        _, y, _ = literal_scene(F(1), 8)
        original_rref, original_inv = exact.rref, produce.inv
        observation_calls, inversions = [], []

        def counted_rref(matrix):
            if matrix is y:
                observation_calls.append(matrix)
            return original_rref(matrix)

        def counted_inv(matrix):
            inversions.append(copy.deepcopy(matrix))
            return original_inv(matrix)

        with patch.object(exact, 'rref', counted_rref), \
                patch.object(produce, 'rref', counted_rref), \
                patch.object(produce, 'inv', counted_inv):
            record = produce.data_only(y)
        self.assertEqual(len(observation_calls), 1)
        self.assertEqual(inversions.count(record['baseline_metric']), 1)
        self.assertIn('finite_failure_witness', record)
        check.check_data_only(exact.encode(record))


if __name__ == '__main__':
    unittest.main()
