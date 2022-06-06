"""
Script to find all contrast curve .csv files,
read them, and re-write them in the TRICERATOPS
contrast folder using the required data format.
"""

# CDD
# Created: 5/28/22
# Updated: 5/28/22

import numpy as np
import pandas as pd
import os as os
import glob as glob

#Defaults
verbose = False


#Files and directories
tridir = '/Users/courtney/Documents/data/toi_paper_data/contrast_curves_for_triceratops/'

#Get list of final images
namestr = '/Users/courtney/Documents/data/shaneAO/*/reduced*/*/*/contrast_curve.csv'
flist = glob.glob(namestr)

print('Files: ', len(flist))

#Loop through these files!
counter = 0
for ff in np.arange(len(flist)):

    file = flist[ff]

    #Use current filename to set final filename
    parts = file.split('/')
    filt = parts[-2] #filter is second to last part of filename
    tic = parts[-3] #TIC is third to last part of filename
    night = parts[-4].split('reduced_')[1] #reduced_[NIGHT] is fourth to last part of filename


    #Don't include Kepler or K2 targets
    if tic[0] == 'K': #Catch Kepler or K2 prefixes
        continue
    if tic[0] == 'E': #catch EPIC prefixes
        continue

    #Remove T or TIC prefix
    if 'TIC' in tic:
        if verbose:
            print('TIC name: ', tic)
        tic = tic.split('TIC')[1]
        if verbose:
            print('renamed as : ', tic)


    if 'T' in tic:
        if verbose:
            print('T name: ', tic)
        tic = tic.split('T')[1]
        if verbose:
            print('renamed as : ', tic)

    #Recast to drop leading zeros and spaces
    tic = str(int(tic))

    #Set output file
    outname = tic+'_'+filt+'_'+night+'_contrast_curve.csv'

    #Read in the contrast curve
    c = pd.read_csv(file)

    #Drop the error column
    c = c[['arcsec','dmag']]

    #Don't keep any rows with missing values
    c = c.dropna()

    #Write TRICERATOPS-friendly output file
    c.to_csv(tridir+outname,index=False,header=False)
    counter += 1

print('Saved ', counter, ' contrast curves in TRICERATOPS format.')
