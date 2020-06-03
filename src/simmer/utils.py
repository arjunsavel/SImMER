"""
This module provides utility functions for the reduction pipeline.
"""

import numpy as np
import matplotlib.colors as co
import matplotlib.pyplot as plt
import astropy.io.fits as pyfits


def find_angle(loc1, loc2):
    """
    Calculated the angle between two locations on a grid.
    
    Inputs:
        :loc1: (tuple) first location.
        :relative: (tuple) second location.
                    
    Outputs:
        :angle : (float) real-valued angle between loc1 and loc2.
    """
    angle = np.atan(loc1[1] / loc2[1])
    return angle


def make_filelist(directory, numlist, inst):
    """Turn a list of numbers into a list of properly formatted filenames.

    Inputs:
        :directory: (string) path leading to directory of interest.
        :numlist: (list) list of numbers corresponding to fits files.
        :inst: (Instrument object) instrument for which data is being reduced.

    Outputs:
        :filelist: (list) list of strings pertaining to files of interest
    """

    filelist = [directory + inst.file_prefix + "{:04d}.fits".format(d) for d in numlist]
    return filelist


def read_imcube(filelist):
    """Reads a stack of fits files into an image cube of dimensions (nims, xpix, ypix).
    
    Inputs:
        :filelist: (list) list of strings pertaining to files of interest.

    Outputs:
        :im_array: (3D array) array of 2D arrays pertaining to the files in filelist.

    """

    im_array = np.array([pyfits.getdata(file, 0) for file in filelist])

    return im_array


def image_subsection(input_image, npix, center):
    """reads in a full image array, selects the relevant subsection of the array,
    and returns the new array, transposed for use with Python.
    input_image must be 2D

    Inputs:
        :input_image: (2D array) image of which a subsection is desired.
        :center: (tuple) center of image, with format (x, y)
        :npix: (float) value for size of return image. If non-square image desired, enter as list.
    
        :default: center = (750, 1100)
        :npix: = 600 for inscribed region or npix = 1000 for circumscribing region
        
        :transposed: = np.rot90(input_image.T,2)
        :transposed: = np.rot90(input_image,2)
        :center: = (2047-center[0],2047-center[1]

    Outputs:
        :subsection: (2d array) subsection of original image.

    )"""

    npix = np.array(npix)
    if np.size(npix) == 1:
        npix = [npix, npix]
    half = [int(n / 2) for n in npix]

    subsection = input_image[
        center[0] - half[0] : center[0] + half[0],
        center[1] - half[1] : center[1] + half[1],
    ]

    return subsection


def header_subsection(input_image_file, npix, center):
    """
    Reads out the header of a subsection.

    Inputs:
        :input_image: (2D array) image of which a subsection is desired.
        :center: (tuple) center of image, with format (x, y)
        :npix: (float) value for size of return image. If non-square image desired, enter as list.
    
    Outputs:
        :header: (FITS header) header of the image file, adjusted accordingly.

    
    """
    header = pyfits.getheader(input_image_file)
    # hdulist = fits.open(input_image_file)
    # header = wcs.WCS(hdulist[0].header)

    header["CRPIX1"] = npix / 2 - (center[1] - header["CRPIX1"])  # x=col
    header["CRPIX2"] = npix / 2 - (center[0] - header["CRPIX2"])  # y=row
    header["NAXIS1"] = 600
    header["NAXIS2"] = 600

    return header


def plot_array(
    im_array, vmin, vmax, directory, filename, extent=None
):  # pylint: disable=too-many-arguments
    """
    Plots arrays produced in the process of the pipeline.

    Inputs:
        :im_array: (3D array) array of 2D images.
        :vmin: (int) minimum for linear color mapping of plots.
        :vmax: (int) maximum for linear color mapping of plots.
        :directory: (str) path to directory to which the image file will be saved.
        :filename: (str) name of file to which the image will be saved.
        :extent: (tuple) from matplotlib documentation: controls the bounding box in data coordinates that
                                the image will fill specified as (left, right, bottom, top) in data coordinates

    Outputs:
        :fig: (Matplotlib figure) plotted figure.

    """

    def plot_few():
        fig = plt.figure(figsize=(30, 6))
        for i in range(array_len):
            ax = fig.add_subplot(
                1, array_len, i + 1
            )  # pylint: disable=invalid-name # common axis name!
            pltim = np.rot90(im_array[i, :, :], 2)
            cim = ax.imshow(
                pltim,
                origin="lower",
                cmap="plasma",
                norm=co.Normalize(vmin=vmin, vmax=vmax),
                extent=extent,
            )
            ax.tick_params(axis="both", which="major", labelsize=20)
        return fig, cim

    def plot_many():
        nrows = 4
        ncols = int(np.ceil((array_len / 4.0)))
        rowheight = nrows * 10
        colheight = ncols * 10

        fig = plt.figure(figsize=(colheight, rowheight))
        for i in range(array_len):
            ax = fig.add_subplot(
                nrows, ncols, i + 1
            )  # pylint: disable=invalid-name # common axis name!
            pltim = np.rot90(im_array[i, :, :], 2)

            cim = ax.imshow(
                pltim,
                origin="lower",
                cmap="plasma",
                norm=co.Normalize(vmin=vmin, vmax=vmax),
                extent=extent,
            )
            ax.tick_params(axis="both", which="major", labelsize=40)
        return fig, cim

    array_len = np.shape(im_array)[0]

    if array_len <= 5:
        fig, cim = plot_few()

    else:  # 11 images? 13 images? make it 4xn
        fig, cim = plot_many()

    fig.subplots_adjust(right=0.8)
    cbar_ax = fig.add_axes([0.85, 0.15, 0.05, 0.7])
    cbar = fig.colorbar(cim, cax=cbar_ax)
    cbar.ax.tick_params(labelsize=50)

    plt.savefig(directory + filename)
    plt.close("all")
    return fig


# def general_bad_pix(image):
#    sh = np.shape(image)
#    bp_im = image.copy()
#    px = 5
#
#    for r in range(sh[0]):
#        for c in range(sh[1]):
#            left = np.max([0, c-px]) #left of image, or 5 less than current pixel
#            right = np.min([sh[1], c+px]) #right of image or 5 more than current pixel
#            bott = np.max([0, r-px]) #bottom of image or 5 less than current pixel
#            top = np.min([sh[0], c+px]) #top of image or 5 more than current pixel
#
#            region = image[bott:top, left:right]
#            region_size = np.size(region)
#
#            nans = np.sum(np.isnan(region))
#            if nans == region_size:
#                #all these pixels are shitty, set value to 0
#                bp_im[r,c] = 0.
#            else:
#                r_med = np.nanmedian(region)
#                if image[r,c] > 5.*r_med or np.isnan(image[r,c]):
#                    bp_im[r,c] = r_med
#
#    return bp_im
