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
    Instantiates an object that implements instrument-specific reduction techniques.
    """

    name = None

    npix = (
        10  # Size of rot search; needs to be bigger if initial shifts are off.
    )

    def __init__(self, take_skies=False):
        self.take_skies = take_skies

    def bad_pix(self, image):
        """Read in bad pixel file, cut down to size, and replace NaN
        pixels with median of surrounding pixels.

        Inputs:
            :image: (2D numpy array) image to be filtered for bad pixels.

        Outputs:
            :iamge: (2D numpy array) image, now filtered for bad pixels.
                    Same dimensions as input image.
        """
        c_im = image.copy()

        for i in range(3):
            filtered = median_filter(c_im, size=10)
            nan_indices = np.where(np.isnan(c_im))
            c_im[nan_indices] = filtered[nan_indices]

        return c_im


class ShARCS(Instrument):
    """
    For use on the ShARCS camera on the Shane 3m telescope
    at Lick observatory.
    """

    name = "ShARCS"
    center = (750, 1100)  # row, col
    npix = 1000 #Was 600. Using 1000x1000 prevents vertical and horizontal boundaries in final image.

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

        Inputs:
            :file: (str) path to file.

        """
        return u.header_subsection(file, self.npix, self.center)

    def filt(self, nims, head, filter_name):
        """
        Given the header of a FITS file, returns its filter.

        Inputs:
            :nims: (int) number of images.
            :head: (astropy.io.fits header object) head
                    of object of interest.
            :filter_name: (str) name of filter to use
                    in the event that the filter is
                    unknown in the header.
        Outputs:
            :filt: (str) name of filter used to observe
                    object of interest.
        """
        if head["FILT1NAM"] == "Unknown":
            filt = filter_name
        else:
            filt = head["FILT1NAM"]
        if head["FILT2NAM"] != "Open": #append Ch4-1.2 as needed
            filt = filt + '+'+head["FILT2NAM"]

        return filt

    def itime(self, head):
        """
        Given a FITS header, returns the true integration time
        for a file.

        Inputs:
            :head: (astropy.io.fits header object) head
                    of object of interest.

        Outputs:
            :itime_val: (float) integration time for object of
                    interest.
        """
        itime_val = head["ITIME0"] * 1e-6
        return itime_val

    def bad_pix(self, image):
        """Read in bad pixel file, cut down to size, replace bad
        pixels with median of surrounding pixels.

        Inputs:
            :image: (2D numpy array) image to be filtered for bad pixels.

        Outputs:
            :iamge: (2D numpy array) image, now filtered for bad pixels.
                    Same dimensions as input image.
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

    def read_data(self, night, rawfilename, newfilename):
        raise NotImplementedError(
            "Data should not be read through"
            "this method for ShARCS. Instead,"
            "please run the driver function of "
            "your choice on folders containing "
            "your raw data."
        )


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

        Inputs:
            :nims: (int) number of images.
            :head: (astropy.io.fits header object) head
                    of object of interest.
            :filter_name: (str) name of filter to use
                    in the event that the filter is
                    unknown in the header.
        Outputs:
            :filt: (str) name of filter used to observe
                    object of interest.
        """
        filt = head["FILTER"]
        return filt

    def head(self, file):
        """
        Returns the head of a FITS file.

        Inputs:
            :file: (str) path to FITS file of interest.

        """
        return pyfits.getheader(file)

    def itime(self, head):
        """
        Given a FITS header, returns the true integration time
        for a file.

        Inputs:
            :head: (astropy.io.fits header object) head
                    of object of interest.

        Outputs:
            :itime_val: (float) integration time for object of
                    interest.
        """
        itime_val = head["T_INT"] / 1000.0
        return itime_val

    def adjust_thisimage(self, thisimage):
        thisimage = thisimage.astype(float)
        return thisimage

    def read_data(self, raw_dir, new_dir):
        """
        Reads data.

        Inputs:
            :rawdir: (string) absolute path to directory containing raw data.
                        File path should end with '/'.
            :newdir: (string) absolute path to directory that will contain
                        4-quadrant data. File path should end with '/'.

        Outputs:
            None
        """

        def read_pharo(raw_file_name, new_file_name):
            """
            Read in the 4-quadrant data and flatten it.

            Inputs:
                :raw_file_name: (string) name of raw file.
                :new_file_name: (string) name of flattened 4-quadrant data.
            """
            im_cube = pyfits.getdata(raw_file_name)
            header = pyfits.getheader(raw_file_name)

            newfile = np.zeros((1024, 1024))
            newfile[0:512, 512:1024] = im_cube[0, :, :]  # Lower right
            newfile[0:512, 0:512] = im_cube[1, :, :]  # Lower left
            newfile[512:1024, 0:512] = im_cube[2, :, :]  # Upper left
            newfile[512:1024, 512:1024] = im_cube[3, :, :]  # Upper right

            hdu = pyfits.PrimaryHDU(newfile, header=header)
            hdu.writeto(new_file_name, overwrite=True, output_verify="ignore")

            return newfile

        def convert_night():
            """
            Convert the cubes to flat files for a whole night.
            """
            flist = glob.glob(raw_dir + "*.fits")

            if not os.path.isdir(new_dir):
                os.mkdir(new_dir)

            for fpath in flist:
                fname = fpath.split("/")[-1]
                newfname = new_dir + "s" + fname

                read_pharo(fpath, newfname)

        convert_night()
