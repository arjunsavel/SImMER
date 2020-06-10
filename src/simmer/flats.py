"""
Functions to work with flats.
"""
import astropy.io.fits as pyfits
import numpy as np
from tqdm import tqdm

from . import plotting as pl
from . import utils as u

CENTER = (750, 1100)  # row,col
MPIX = 600


def flat_driver(raw_dir, reddir, config, inst, plotting_yml=None):
    """Sets up and runs create_flats.

    Inputs:
        :raw_dir: (string) directory for the raw data
        :reddir: (string) directory for the reduced data
        :config: (pandas DataFrame) dataframe corresponding to config sheet for data.
        :inst: (Instrument object) instrument for which data is being reduced.
        :plot: (bool) determines whether or not intermediate plots should be produced.

    """
    if plotting_yml:
        pl.initialize_plotting(plotting_yml)

    _flats = config[config.Object == "flat"]
    filts = _flats.Filter.tolist()
    for filter_name in tqdm(
        filts, desc="Running flats", position=0, leave=True
    ):
        # literal_eval issues below
        flatlist = eval(
            _flats[_flats.Filter == filter_name].Filenums.values[0]
        )  # pylint: disable=eval-used
        itime = _flats[_flats.Filter == filter_name].ExpTime.values[0]
        darkfile = reddir + f"dark_{int(round(itime))}sec.fits"
        create_flats(
            raw_dir, reddir, flatlist, darkfile, inst, filter_name=filter_name
        )


def create_flats(
    raw_dir, reddir, flatlist, darkfile, inst, filter_name=None, test=False
):
    """Create a flat from a single list of flat files.

    Inputs:
        :raw_dir: (str) directory where the raw data is stored.
        :reddir: (str) directory where the reduced data is stored.
        :flatlist: (list) list of integers corresponding to flats.
        :inst: (inst object) instrument for which data is being reduced.
        :center: (tuple) two-element tuple dictating where the center of each image is.
        :npix: (int) number of pixels in image.
        :pl: (Bool) determines whether plots are produced.
        :filter: filter name given if head['FILT1NAM'] == 'Unknown'
    """
    nflats = len(flatlist)
    flatfiles = u.make_filelist(raw_dir, flatlist, inst)
    flat_array = u.read_imcube(flatfiles)
    flat_array = inst.adjust_array(flat_array, nflats)
    head = inst.head(flatfiles[0])
    filt = inst.filt(nflats, head, filter_name)

    if test:
        dark = 0.0
    else:
        dark = pyfits.getdata(darkfile, 0)
    for i in range(nflats):
        flat_array[i, :, :] = flat_array[i, :, :] - dark
        flat_array[i, :, :] = flat_array[i, :, :] / np.median(
            flat_array[i, :, :]
        )

    final_flat = np.median(flat_array, axis=0)
    final_flat = final_flat / np.median(final_flat)

    pl.plot_array(
        "intermediate", flat_array, -2.0, 2.0, reddir, f"flat_cube_{filt}.png"
    )

    # CDD update
    #  head.update('DATAFILE', str(flatlist)) #add all file names
    head.set("DATAFILE", str(flatlist))  # add all file names
    # end CDD update

    hdu = pyfits.PrimaryHDU(final_flat, header=head)
    hdu.writeto(
        reddir + f"flat_{filt}.fits", overwrite=True, output_verify="ignore"
    )

    return final_flat
