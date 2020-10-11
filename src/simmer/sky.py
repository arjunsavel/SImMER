"""
Functions to work with skies.
"""

import os
from glob import glob

import astropy.io.fits as pyfits
import numpy as np
from tqdm import tqdm

from . import plotting as pl
from . import utils as u

CENTER = (750, 1100)  # row,col
NPIX = 600


def sky_driver(raw_dir, reddir, config, inst, plotting_yml=None):
    """Night should be entered in format 'yyyy_mm_dd' as string.
    This will point toward a config file for the night with flats listed.

    Inputs:
        :raw_dir: (string) directory for the raw data
        :reddir: (string) directory for the reduced data
        :config: (pandas DataFrame) dataframe corresponding to config sheet for data.
        :inst: (Instrument object) instrument for which data is being reduced.
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

    if plotting_yml:
        pl.initialize_plotting(plotting_yml)

    for star in tqdm(stars, desc="Running skies", position=0, leave=True):

        s_dir = reddir + star + "/"
        if (
            s_dir not in sdirs
        ):  # make sure there's a subdirectory for each star
            os.mkdir(s_dir)

        filts = skies[
            skies.Object == star
        ].Filter.values  # array of filters as strings
        for n, filter_name in enumerate(filts):
            # CDD change
            # skylist = literal_eval(skies[skies.Object == s].Filenums.values[n])
            # literal_eval issues below
            skylist = eval(
                skies[skies.Object == star].Filenums.values[n]
            )  # pylint: disable=eval-used
            # end CDD change
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
    flat = pyfits.getdata(flatfile, 0)

    for i in range(nskies):
        flat[flat == 0] = np.nan
        sky_array[i, :, :] = sky_array[i, :, :] / flat

    # final_sky = u.median_outlier_reject(sky_array, 2.0) #2sigma outlier rejection?
    final_sky = np.median(sky_array, axis=0)

    pl.plot_array(
        "intermediate", sky_array, -10.0, 100.0, sf_dir, "sky_cube.png"
    )
    # CDD change
    #  head.update('DATAFILE', str(skylist)) #add all file names
    head.set("DATAFILE", str(skylist))  # add all file names
    # end CDD change

    hdu = pyfits.PrimaryHDU(final_sky, header=head)
    hdu.writeto(sf_dir + "sky.fits", overwrite=True, output_verify="ignore")

    return final_sky
