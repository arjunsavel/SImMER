"""
Script for analyzing a reduced image.
Determine location and FWHM of target star,
calculate contrast curve, detect companions,
and determine magnitude ratios between companions and target star.
"""

# CDD
# Created: 5/6/22
# Updated: 5/9/22

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

#learning how to detect stars using astropy
from astropy.stats import sigma_clipped_stats
#from photutils.datasets import load_star_image
from photutils.detection import DAOStarFinder
from astropy.visualization import SqrtStretch

from astropy.visualization.mpl_normalize import ImageNormalize
from photutils.aperture import CircularAperture, CircularAnnulus, ApertureStats
from photutils.aperture import aperture_photometry
from astropy.stats import SigmaClip
from astropy.io import fits

import simmer.contrast as sim_con_curve

#Test file
startname = '/Users/courtney/Documents/data/shaneAO/data-'
datestr = '2019-07-19'
midname = '-AO-Courtney.Dressing/reduced_'
starname = 'T294301883'
filt = 'J'
endname = '/final_im.fits'

filename = startname + datestr + midname + datestr + '/'+starname+'/'+filt+endname
outdir = startname + datestr + midname + datestr + '/'+starname+'/'+filt+'/'

def analyze(filename=filename, maxiter = 10, postol=1, fwhmtol = 0.5, inst = 'ShARCS', outdir='', verbose=True):

    #set defaults
    if inst == 'PHARO':
        plate_scale = 0.025
    else:
        plate_scale = 0.033


    #open the image and load the data
    im = fits.getdata(filename, ext=0)

    #Find target source using rough guesses about image properties
    original_sources = find_sources(im)

    #Find brightest peak
    xcen, ycen = find_center(original_sources, verbose=verbose)

    #Determine FWHM using that center
    fwhm = find_FWHM(im, [xcen,ycen])
    if verbose == True:
        print('Estimated FWHM: ', fwhm)

    #Iterate until coordinates and FWHM agree to within tolerance
    #or until maximum number of iterations is reached
    posdiff = 5
    fwhmdiff = 2
    niter = 1
    while np.logical_and(niter < maxiter, np.logical_or(posdiff > postol, fwhmdiff > fwhmtol)):
        if verbose == True:
            print('Beginning iteration ', niter)

        #Find sources again
        updated_sources = find_sources(im, fwhm=fwhm)
        if verbose == True:
            print('Updated sources')
            print(updated_sources)

        #Find brightest peak again using updated list of stars
        updated_xcen, updated_ycen = find_center(updated_sources, verbose=verbose)

        #Determine FWHM using that center
        updated_fwhm = find_FWHM(im, [updated_xcen,updated_ycen])
        if verbose == True:
            print('Estimated FWHM: ', updated_fwhm)

        #Compute differences
        posdiff = np.sqrt((updated_xcen - xcen)**2. + (updated_ycen - ycen)**2.)
        fwhmdiff = np.sqrt((updated_fwhm - fwhm)**2.)
        if verbose == True:
            print('Current posdiff: ', posdiff)
            print('Current fwhmdiff: ', fwhmdiff)

        #Update reference values
        xcen = updated_xcen
        ycen = updated_ycen
        fwhm = updated_fwhm
        niter += 1

    #Save FWHM, center position to file
    d={'filename': filename, 'xcen': xcen, 'ycen': ycen, 'fwhm': fwhm}
    key_details = pd.DataFrame(data=d,index=[0])
    key_details.to_csv(outdir+'key_details.csv', index=False)

    #Save sources to file
    updated_sources.to_csv(outdir+'detected_stars.csv', index=False)

    #Make contrast curve
    #Use current version of simmer
    contrast_curve = sim_con_curve.contrast_curve_main(im, fwhm, inst, position=[xcen, ycen])
    contrast_curve.to_csv(outdir+'contrast_curve.csv',index=False)

    return im, xcen, ycen, fwhm, updated_sources, contrast_curve


def find_sources(im, sigma=5, fwhm=5, tscale=10, verbose=False, plot=True, **kwargs):
    """
    Determines sources in an image. Based on astropy tutorial here: https://photutils.readthedocs.io/en/stable/detection.html
    """
    mean, median, std = sigma_clipped_stats(im, sigma=sigma)
    if verbose == True:
        print((mean, median, std))

    sources = None
    while np.logical_and(type(sources) == type(None), fwhm < 200):
        if verbose == True:
            print('trying FWHM: ', fwhm)
        #Detect stars >threshold above the background. Needed to adjust FWHM and threshold
        daofind = DAOStarFinder(fwhm=fwhm, threshold=tscale*std, exclude_border=True, **kwargs)
        sources = daofind(im - median)
    #    for col in sources.colnames:
    #        sources[col].info.format = '%.8g'  # for consistent table output
        if verbose == True:
            print(sources)
        fwhm += 1

    if plot:
        # Plot image and mark location of detected sources
        positions = np.transpose((sources['xcentroid'], sources['ycentroid']))
        apertures = CircularAperture(positions, r=4.)
        norm = ImageNormalize(stretch=SqrtStretch(),vmin=0,vmax=100)
        plt.imshow(im, cmap='Greys', origin='lower', norm=norm, interpolation='nearest')
        apertures.plot(color='orange', lw=2.5);
        plt.close()

    #Convert sources to a dataframe
    df = sources.to_pandas()
   # print(len(sources))
    return df

def find_FWHM(image, center, min_fwhm = 2, verbose=False):
    """
    Calculated FWHM from image. Based on code by Steven Giacalone
    inputs:
    image (2d array) pixel values on x-y grid.
    center (1d array) x-y coordinates of the center of the star in the image
    min_fwhm (int) minimum allowed FWHM (avoid errors caused by bright spikes in blurry PSFs)

    outputs:
    FWHM (int) full width at half maximum of star psf
    """
    y, x = np.indices((image.shape))
    r = np.sqrt((x - center[0])**2 + (y - center[1])**2) # distances from center

    HM = np.max(image[r < 5])//2
    diff = np.abs(image - HM)
    closest_x = np.unravel_index(np.argsort(diff.flatten()), image.shape)[0][:10] # 10 pixels closest in value to HM
    closest_y = np.unravel_index(np.argsort(diff.flatten()), image.shape)[1][:10]
    nearest_pixels = r[closest_x, closest_y] # radii of those 10 pixels
    best_idx = np.argmin(nearest_pixels)
    idx = (closest_x[best_idx], closest_y[best_idx])
    FWHM = 2*np.sqrt((center[0]-idx[0])**2 + (center[1]-idx[1])**2)

    #Require FWHM >= min_fwhm
    FWHM = np.max([FWHM, min_fwhm])

    return FWHM

def aperture_photometry(im, df, fwhm):
    """
    Wrapper around photutils. Performs simple aperture photometry on a set of sources.
    adapted from tutorial: https://photutils.readthedocs.io/en/stable/aperture.html
    """

    _, median, _ = sigma_clipped_stats(im, sigma=3.0)
    im -= median  # subtract background from the data

    positions = np.transpose((df['xcentroid'], df['ycentroid']))
    apertures = CircularAperture(positions, r=fwhm)

    phot_table = aperture_photometry(im, apertures)

    annulus_apertures = CircularAnnulus(positions, r_in=fwhm * 2, r_out=fwhm * 3)
    aperstats = ApertureStats(im, annulus_apertures)
    bkg_mean = aperstats.mean # for each position

    aperture_areas = apertures.area_overlap(im)

    total_bkg = bkg_mean * aperture_areas

    phot_bkgsub = phot_table['aperture_sum'] - total_bkg

    phot_table['total_bkg'] = total_bkg
    phot_table['aperture_sum_bkgsub'] = phot_bkgsub

    return phot_table


def find_center(df, verbose=False):
    '''Returns coordinates of star with highest peak'''
    ww = np.where(df['peak'] == np.max(df['peak']))
    xcen = int(np.round(float(df.iloc[ww]['xcentroid'])))
    ycen = int(np.round(float(df.iloc[ww]['ycentroid'])))
    if verbose == True:
        print('Closest pixels to center: ', xcen, ycen)
    return xcen, ycen
