"""
Module for summarizing all reduced data from a night of observing.
"""

import glob

import numpy as np
import pandas as pd
import os as os

from . import utils as u
from . import plotting as pl

import matplotlib.pyplot as plt #for plotting contrast curves

def get_star_filts(flist):
    #Extract star names and filter names from list of filenames
    flist = np.array(flist)
    started = 0
    for ff in np.arange(len(flist)):
        f = flist[ff]
        parts = f.split('/')
        star = parts[-3]
        filt = parts[-2]

        if started == 0:
            snames = star
            filts = filt
            started = 1
        else:
            snames = np.append(snames, star)
            filts = np.append(filts, filt)
    return (snames, filts)

def image_grid(reddir):
    #get list of all final images
    flist = glob.glob(reddir+'**/final_im.fits',recursive=True)
    flist.sort()

    #Get the star names and filters used for each image
    snames, filts = get_star_filts(flist)

    #Produce a grid of images showing all stars and filters
    im_array = u.read_imcube(flist)

    npix=50 # number of pixels to show
    lo=int((600-npix)/2.)
    hi = int((600+npix)/2.)
    pl.plot_array(
            "intermediate", im_array[:,lo:hi, lo:hi], -10.0, 10000.0, reddir, "all_stars.png",snames=snames,filts=filts)

def nightly_contrast_curve(reddir):
    #produce a plot showing all contrast curves
    #get list of all contrast curves
    flist = glob.glob(reddir+'**/contrast_curve.csv',recursive=True)
    flist.sort()

    #Get the star names and filters used for each image
    snames, filts = get_star_filts(flist)

    for ii in np.arange(len(flist)):
        sc = pd.read_csv(flist[ii])

        if filts[ii] == 'Ks':
            fcol = '#ff0000'
        elif filts[ii] == 'BrG-2.16':
            fcol = '#ff5555'
        elif filts[ii] == 'J':
            fcol = '#0000ff'
        elif filts[ii] == 'J+Ch4-1.2':
            fcol = '#5555ff'
        else:
            fcol = '#555555'
        plt.plot(sc.arcsec, sc.dmag,'-',color=fcol)

    plt.xlabel('Separation (")')
    plt.ylabel('Contrast (Magnitudes)')
    # reverse y-axis
    ax = plt.gca()
    ax.set_ylim(ax.get_ylim()[::-1])
    plt.savefig(reddir + 'all_contrast_curves.png', bbox_inches="tight",dpi=300)
    plt.close("all")

def full_summary(reddir):
    #Make all summary plots
    image_grid(reddir)
    nightly_contrast_curve(reddir)
