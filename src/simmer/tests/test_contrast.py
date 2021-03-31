import yaml
import numpy as np
import scipy as sp
from astropy.stats import SigmaClip
from astropy.stats import sigma_clipped_stats
from astropy.io import fits
import math
from numpy import random
import photutils
import unittest
from photutils import datasets
from astropy.table import Table
from simmer.contrast import ConCur as cc
from simmer.contrast import twoD_weighted_std as wstd
from simmer.contrast import find_best_center


def all_same(items):
    return np.all(x == items[0] for x in items)


class TestContrastCurve(unittest.TestCase):
    def test_constant_flux(self):
        arr = np.array([[1000] * 600] * 600)
        result = cc(arr)
        self.assertTrue(all_same(result[1]))

    def test_zero_vals(self):
        arr = np.array([[0] * 600] * 600)
        result = cc(arr)
        bools = []
        for i in result[1]:
            bools.append(np.isnan(i))
        self.assertTrue(np.all(bools))

    def test_radius_size(self):
        arr = np.array([[1000] * 600] * 600)
        rad1_result = cc(arr, radius_size=1)
        rad3_result = cc(arr, radius_size=3)
        rad6_result = cc(arr, radius_size=6)
        self.assertTrue(
            np.all(
                [
                    len(rad1_result[0]) > len(rad3_result[0]),
                    len(rad3_result[0]) > len(rad6_result[0]),
                ]
            )
        )

    def test_best_center(self):
        table = Table()
        table["flux"] = [1000]
        table["x_mean"] = [299.5]
        table["y_mean"] = [299.5]
        arr = datasets.make_gaussian_sources_image((600, 600), table)
        result = find_best_center(arr, 3, [299.5, 299.5])
        self.assertTrue(np.allclose((result[0], result[1]), [299.5, 299.5]))

    def test_twoD_weighted_std_constants(self):
        numbers = np.array([[20] * 600] * 600)
        weights = np.array([[1] * 600] * 600)
        self.assertEqual(0, wstd(numbers, weights))

    def test_twoD_weighted_std_known_simple(self):
        numbers = np.array([[1, 1, 1], [2, 2, 2], [3, 3, 3]])
        weighers = np.array([[1, 1, 1], [0, 0, 0], [1, 1, 1]])
        self.assertTrue(np.isclose(wstd(numbers, weighers), 1.095445115))


if __name__ == "__main__":
    unittest.main()
