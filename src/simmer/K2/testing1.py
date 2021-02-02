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


#from CC_test_py import contrast_curve_3 as cc

'''class ArrayClass:
    
    def __init__(self,size,val):
        rows,cols = (size,size)
        self.size = size
        self.val = val
        self.arr = np.array([[val]*cols]*rows)'''


class TestContrastCurve(unittest.TestCase):

    def test_constant_flux(self):
        rows,cols = (600,600)
        arr = np.array([[1000]*cols]*rows)
        result = cc(arr)
        self.assertTrue(result[1][0] == result[1][-1])
    
    def test_radius_size(self):
        #arr = ArrayClass(600,0).arr
        rows,cols = (600,600)
        arr = np.array([[1000]*cols]*rows)
        rad2_result = cc(arr,radius_size=2)
        rad3_result = cc(arr,radius_size=3)
        self.assertTrue(len(rad3_result[0]) < len(rad2_result[0]))
        

if __name__ == '__main__':
    unittest.main()
