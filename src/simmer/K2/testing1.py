import yaml
import unittest
from shutil import copyfile
import os

import numpy as np
import scipy as sp
import pandas as pd
from astropy.stats import SigmaClip
from astropy.stats import sigma_clipped_stats
from astropy.io import fits
import math
import photutils


from CC_py import contrast_curve_3 as cc

'''class ArrayClass:
    
    def __init__(self,size,val):
        rows,cols = (size,size)
        self.size = size
        self.val = val
        self.arr = np.array([[val]*cols]*rows)'''


def all_same(items):
        return all(x == items[0] for x in items)

class TestContrastCurve(unittest.TestCase):


    def test_constant_flux(self):
        rows,cols = (600,600)
        arr = np.array([[1000]*cols]*rows)
        result = cc(arr)
        self.assertTrue(all_same(result[1]))
    
    def test_radius_size(self):
        #arr = ArrayClass(600,0).arr
        rows,cols = (600,600)
        arr = np.array([[1000]*cols]*rows)
        rad1_result = cc(arr,radius_size=2)
        rad3_result = cc(arr,radius_size=3)
        rad_6_result=cc(arr,radius_size=6)
        self.assertTrue(all([len(rad1_result[0])>len(rad3_result[0]),
                             len(rad3_result[0])>len(rad6_result[0])]))
    def test_output_array_dim(self):
        rows,cols = (600,600)
        arr = np.array([[1000]*cols]*rows)
        rad1_result = cc(arr,radius_size=1)
        rad3_result = cc(arr,radius_size=3)
        rad6_result = cc(arr,radius_size=6)
        self.assertTrue(all ([len(rad1_result[0])==len(rad1_result[1]),len(rad3_result[0])==len(rad3_result[1]),
                 len(rad6_result[0])==len(rad6_result[1])]))
    def test_pseudo_star_mag(self):
        rows,cols = (600,600)
        arr = np.array([[1]*cols]*rows)
        arr[299:301,299:301] = 1000
        result = cc(arr)
        correct = [7.5] * (len(result[1])-1)
        self.assertTrue(all([result[1][0] == 0, np.allclose(correct,result[1][1:])]))

    def test_arclength(self):
        rows,cols = (600,600)
        arr = np.array([[1000]*cols]*rows)
        result = cc(arr)
        correct = []
        for i in range(len(result[0])):
            x = i*0.033 + 0.033
            correct.append(x)
        self.assertTrue(np.allclose(correct,result[0]))

    def test_0_vals(self):
        arr = np.zeros((600,600))
        result = cc(arr)
        correct = [np.NaN] * len(result[1])
        self.assertTrue(all_same(correct==result[1]))

if __name__ == '__main__':
    unittest.main()








                    
