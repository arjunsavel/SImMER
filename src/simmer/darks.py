"""
Functions to work with darks.
"""

import astropy.io.fits as pyfits
import numpy as np
from tqdm import tqdm

from . import plotting as pl
from . import utils as u

def dark_driver(raw_dir, reddir, config, inst, plotting_yml=None):
    """Night should be entered in format 'yyyy_mm_dd' as string.
    This will point toward a config file for the night with darks listed.flat

    Inputs:
        :raw_dir: (string) directory for the raw data
        :reddir: (string) directory for the reduced data
        :config: (pandas DataFrame) dataframe corresponding to config sheet for data.
        :inst: (Instrument object) instrument for which data is being reduced.
        :plotting_yml: (string) path to the plotting configuration file.

    """
    if plotting_yml:
        pl.initialize_plotting(plotting_yml)

    _darks = config[config.Object == "dark"]
    texps = _darks.ExpTime.unique()

    for texp in tqdm(texps, desc="Running darks", position=0, leave=True):
        # literal_eval issues below
        darklist = eval(
            _darks[_darks.ExpTime == texp].Filenums.values[0]
        )  # pylint: disable=eval-used
        create_darks(
            raw_dir, reddir, darklist, inst
        )  # creates a new dark file


def create_darks(raw_dir, reddir, darklist, inst):
    """creates the actual darks from a list of dark file numbers, taking
    the median and writing to a file. Returns the final dark.

    Inputs:
        :reddir: (string) directory for the reduced data
        :darklist: string) list of dark file numbers
        :inst: (Instrument object) instrument for which data is being reduced.
    """

    ndarks = len(darklist)
    darkfiles = u.make_filelist(raw_dir, darklist, inst)

    dark_array = u.read_imcube(darkfiles)

    dark_array = inst.adjust_array(dark_array, ndarks)
    head = inst.head(darkfiles[0])
    itime = inst.itime(head)

    final_dark = np.median(dark_array, axis=0)  # nanmedian?

    pl.plot_array(
        "intermediate",
        dark_array,
        -1.0,
        50.0,
        reddir,
        f"dark_cube_{int(round(itime))}sec.png",
    )

    head.set("DATAFILE", str(darklist))  # add all file names

    hdu = pyfits.PrimaryHDU(
        final_dark, header=head
    )  # can i do this with fits?
    dark_filename = reddir + "dark_{}sec.fits".format(int(round(itime)))
    hdu.writeto(dark_filename, overwrite=True, output_verify="ignore")

    return final_dark
