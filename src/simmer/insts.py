"""
Module for instrument class and subclasses.
"""

import glob
import os

import astropy.io.fits as pyfits
import numpy as np
from scipy.ndimage.filters import median_filter

from . import utils as u


class Instrument:
    """
    Instantiates an object that dictates instrument-specific reduction techniques.
    """

    name = None

    npix = (
        10  # Size of rot search; needs to be bigger if initial shifts are off.
    )

    def __init__(self, take_skies=False):
        self.take_skies = take_skies

    def bad_pix(self, image):
        """Read in bp file, cut down to size, replace bad
        pixels with median of surrounding pixels.
        """
        c_im = image.copy()

        for i in range(3):
            filtered = median_filter(c_im, size=10)
            bad = np.where(c_im != c_im)  # check this
            c_im[bad] = filtered[bad]

        return c_im


class ShARCS(Instrument):
    """
    For use on the ShARCS camera on the Shane 3m telescope
    at Lick observatory.
    """

    name = "ShARCS"
    center = (750, 1100)  # row,col
    npix = 600

    plate_scale = 0.033  # arcsec/pixel

    replace_filters = {
        "BrG-2.16": ["Ks", "K"],
        "K+CH4-2.4": ["Ks", "K"],
        "J+CH4-1.2": "J",
        "H2-2.2122": ["Ks", "K"],
    }

    filter_logtohead = {
        "Ks": "Ks",
        "BrG": "BrG-2.16",
        "J+CH4-1.2": "J",
        "K": "Ks",
    }
    filter_headtolog = {"Ks": "K", "BrG-2.16": "BrG", "J": "J+CH4-1.2"}

    file_prefix = "s"
    plim_inds = (250, 350)
    off = (-250, -250)

    def adjust_array(self, array, nims):
        return np.array(
            [
                u.image_subsection(array[dd, :, :], self.npix, self.center)
                for dd in range(nims)
            ]
        )

    def adjust_im(self, image):
        return np.fliplr(image)

    def head(self, file):
        """
        Given a FITS file, returns its head.
        """
        return u.header_subsection(file, self.npix, self.center)

    def filt(self, nims, head, filter_name):
        """
        Given the header of a FITS file, returns its filter.
        """
        if head["FILT1NAM"] == "Unknown":
            filt = filter_name
        else:
            filt = head["FILT1NAM"]
        return filt

    def itime(self, head):
        """
        Given a FITS header, returns the true integration time
        for a file.
        """
        return head["ITIME0"] * 1e-6

    def bad_pix(self, image):
        """Read in bp file, cut down to size, replace bad
        pixels with median of surrounding pixels.
        """
        script_dir = os.path.dirname(
            __file__
        )  # <-- absolute dir the script is in
        rel_path = "badpix.fits"
        bpfile_name = os.path.join(script_dir, rel_path)
        bpfile = pyfits.getdata(bpfile_name, 0)
        bpfile = u.image_subsection(bpfile, self.npix, self.center)

        bad = np.where(bpfile == 1)  # locations of bad pixels

        filtered = median_filter(image, size=7)
        image[bad] = filtered[
            bad
        ]  # replace bad pixels with median of surrounding pixels

        return image

    def adjust_thisimage(self, thisimage, rawfile):
        thisimage = u.image_subsection(thisimage, self.npix, self.center)
        head = u.header_subsection(rawfile, self.npix, self.center)
        return thisimage, head


class PHARO(Instrument):
    """
    For use on the PHARO instrument at Palomar.
    """

    name = "PHARO"
    center = np.nan
    npix = np.nan  # Shouldn't matter
    plate_scale = 0.025
    filter_logtohead = {
        "Ks": "K_short",
        "BrG": "Br-gamma",
        "BrG+H2": "Br-gamma",
        "J": "J",
    }
    filter_headtolog = {"K-short": "Ks", "Br-gamma": "BrG", "J": "J"}
    replace_filters = {
        "BrG-2.16": ["Ks", "K"],
        "K+CH4-2.4": ["Ks", "K"],
        "J+CH4-1.2": "J",
        "H2-2.2122": ["Ks", "K"],
    }
    file_prefix = "sph"
    plim = (462, 562)
    off = (-462, -462)

    def adjust_im(self, image):
        return image

    def adjust_array(self, array, nims):
        return array.astype(float)

    def filt(self, nims, head, filter_name):
        """
        Given the header of a FITS file, returns its filter.
        """
        filt = head["FILTER"]
        return filt

    def head(self, file):
        """
        Returns the head of a FITS file.
        """
        return pyfits.getheader(file)

    def itime(self, head):
        """
        Given a FITS header, returns the true integration time
        for a file.
        """
        return head["T_INT"] / 1000.0

    def adjust_thisimage(self, thisimage):
        thisimage = thisimage.astype(float)
        return thisimage

    # def check_filestructure(self, night, rawfilename, newfilename):

    #     def readpharo(rawfilename, newfilename):
    #         """
    #         Read in the 4-quadrant data and flatten it
    #         """
    #         im_cube = pyfits.getdata(rawfilename)
    #         header = pyfits.getheader(rawfilename)

    #         newfile = np.zeros((1024, 1024))
    #         newfile[0:512, 512:1024] = im_cube[0, :, :] #Lower right
    #         newfile[0:512, 0:512] = im_cube[1, :, :] #Lower left
    #         newfile[512:1024, 0:512] = im_cube[2, :, :] #Upper leftß
    #         newfile[512:1024, 512:1024] = im_cube[3, :, :] #Upper right

    #         hdu = pyfits.PrimaryHDU(newfile, header=header)
    #         hdu.writeto(newfilename, overwrite=True, output_verify='ignore')

    #         return newfile

    #     def convert_night(night):
    #         """
    #         Convert the cubes to flat files for a whole night
    #         """
    #         rawdir = aodirs.basedir() + night + '/'
    #         flist = glob.glob(rawdir + '*.fits')

    #         newdir = aodirs.basedir() + night + '/'
    #         if not os.path.isdir(newdir):
    #             os.mkdir(newdir)

    #         for fpath in flist:
    #             fname = fpath.split('/')[-1]
    #             newfname = newdir + 's' + fname

    #             readpharo(fname, newfname)

    #     readpharo(rawfilename, newfilename)
    #     convert_night(night)
