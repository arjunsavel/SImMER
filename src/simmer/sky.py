"""
Functions to work with skies.
"""

import os
from glob import glob

import astropy.io.fits as pyfits
import numpy as np
from tqdm import tqdm
import re as re

from . import plotting as pl
from . import utils as u

def sky_driver(raw_dir, reddir, config, inst, sep_skies = False, plotting_yml=None):
    """Night should be entered in format 'yyyy_mm_dd' as string.
    This will point toward a config file for the night with flats listed.

    Inputs:
        :raw_dir: (string) directory for the raw data
        :reddir: (string) directory for the reduced data
        :config: (pandas DataFrame) dataframe corresponding to config sheet for data.
        :inst: (Instrument object) instrument for which data is being reduced.
        :sep_skies: (Boolean) if true, skies for observations of star STAR are recorded with Object = "STAR sky". If false, observations were taken using a dither pattern and can be used as the skies.
        :plotting_yml: (string) path to the plotting configuration file.
    """

    if inst.take_skies:
        skies = config[config.Comments == "sky"]
    else:
        skies = config[
            (config.Object != "flat")
            & (config.Object != "dark")
            & (config.Object != "setup")
        ]

    stars = skies.Object.unique()
    sdirs = glob(reddir + "*/")

    #Split into sky frames and star frames for observations taken by nodding
    if sep_skies == True:
        keep = np.zeros(len(stars)) + 1
        for kk in np.arange(len(keep)):
            if("sky" in stars[kk]):
                keep[kk] = 0

        wsky = np.where(keep == 0)
        wstar = np.where(keep == 1)
        skynames = stars[wsky]
        starnames = stars[wstar]

    else:
        starnames = stars
        skynames = stars

    if plotting_yml:
        pl.initialize_plotting(plotting_yml)

    for starname in tqdm(starnames, desc="Running skies", position=0, leave=True):
        s_dir = reddir + starname + "/"
        if (
            s_dir not in sdirs
        ):  # make sure there's a subdirectory for each star
            os.mkdir(s_dir)

        #determine object name for skies
        if sep_skies == True:
            skyname = starname+' sky'
        else:
            skyname = starname

        filts = skies[
            skies.Object == skyname
        ].Filter.values  # array of filters as strings

        for n, filter_name in enumerate(filts):
            skylist = eval(

                skies[skies.Object == skyname].Filenums.values[n]
            )
            create_skies(
                raw_dir, reddir, s_dir, skylist, inst, filter_name=filter_name
            )


def create_skies(
    raw_dir, reddir, s_dir, skylist, inst, plotting_yml=None, filter_name=None
):
    """Create a sky from a single list of skies.
    sf_dir is the reduced directory for the specific star and filter.

    Inputs:
        :raw_dir: (string) directory for the raw data
        :reddir: (string) directory for the reduced data
        :s_dir: (string) directory corresponding to a specific star.
        :skylist: (list) list of strings of paths pointing to sky files.
        :inst: (Instrument object) instrument for which data is being reduced.
        :plotting_yml: (string) path to the plotting configuration file.

    Outputs:
        :final_sky: (2D array) medianed sky image.
    """
    if plotting_yml:
        pl.initialize_plotting(plotting_yml)

    nskies = len(skylist)

    skyfiles = u.make_filelist(raw_dir, skylist, inst)

    sky_array = u.read_imcube(skyfiles)

    sky_array = inst.adjust_array(sky_array, nskies)

    head = inst.head(skyfiles[0])
    filt = inst.filt(nskies, head, filter_name)

    # if necessary, make directory for filter. Also grab correct flat file
    fdirs = glob(s_dir + "*/")

    sf_dir = s_dir + filt + "/"
    if sf_dir not in fdirs:  # make a dir for each filt
        os.mkdir(sf_dir)
    flatfile = reddir + f"flat_{filt}.fits"
    if inst.name == "PHARO" and filt == "Br-gamma":
        flatfile = reddir + "flat_K_short.fits"  # no BrG flats in Palomar data

    #For ShARCS, use Ks flat instead of BrG-2.16 if necessary
    if (inst.name == "ShARCS" and filt == "BrG-2.16"):
        if os.path.exists(flatfile) == False:
            flatfile = reddir + 'flat_Ks.fits'

    #For ShARCS, use J flat instead of J+Ch4-1.2 if necessary
    if (inst.name == "ShARCS" and filt == "J+Ch4-1.2"):
        if os.path.exists(flatfile) == False:
            flatfile = reddir + 'flat_J.fits'

    flat = pyfits.getdata(flatfile, 0)

    for i in range(nskies):
        flat[flat == 0] = np.nan
        sky_array[i, :, :] = sky_array[i, :, :] / flat

    # final_sky = u.median_outlier_reject(sky_array, 2.0) #2sigma outlier rejection?
    final_sky = np.median(sky_array, axis=0)

    pl.plot_array(
        "intermediate", sky_array, -10.0, 100.0, sf_dir, "sky_cube.png"
    )

    head.set("DATAFILE", str(skylist))  # add all file names

    hdu = pyfits.PrimaryHDU(final_sky, header=head)
    hdu.writeto(sf_dir + "sky.fits", overwrite=True, output_verify="ignore")

    return final_sky
