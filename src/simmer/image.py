"""
Module to make the image stacking / production occur.
"""


import os
from glob import glob

import astropy.io.fits as pyfits
import numpy as np
from tqdm import tqdm

from . import plotting as pl
from . import registration as reg
from . import utils as u


def image_driver(raw_dir, reddir, config, inst, plotting_yml=None):
    """Do flat division, sky subtraction, and initial alignment via coords in header.
    Returns Python list of each registration method used per star.

    Inputs:
        :raw_dir: (string) directory for the raw data
        :reddir: (string) directory for the reduced data
        :config: (pandas DataFrame) dataframe corresponding to config sheet for data.
        :inst: (Instrument object) instrument for which data is being reduced.
        :plot: (bool) determines whether or not intermediate plots should be produced.

    """
    # Save these images to the appropriate folder.

    if plotting_yml:
        pl.initialize_plotting(plotting_yml)

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

    methods = []

    for star in tqdm(
        stars, desc="Running image driver", position=0, leave=True
    ):
        s_dir = reddir + star + "/"
        if (
            s_dir not in sdirs
        ):  # make sure there's a subdirectory for each star
            os.mkdir(s_dir)

        filts = skies[
            skies.Object == star
        ].Filter.values  # array of filters as strings
        for n, filter_name in enumerate(filts):
            obj = config[config.Object == star]
            #             imlist = literal_eval(obj[obj.Comments != 'sky'].Filenums.values[n])
            imlist = eval(
                obj[obj.Comments != "sky"].Filenums.values[n]
            )  # pylint: disable=eval-used # liter_eval issues
            # cast obj_methods as list so that elementwise comparison isn't performed
            obj_methods = list(config[config.Object == star].Method.values)
            if "saturated" and "wide" in obj_methods:
                methods.append("saturated wide")
            elif "saturated" in obj_methods and "wide" not in obj_methods:
                methods.append("saturated")
            elif "saturated" not in obj_methods and "wide" in obj_methods:
                methods.append("wide")
            else:
                methods.append("default")
            create_imstack(
                raw_dir, reddir, s_dir, imlist, inst, filter_name=filter_name
            )
    return methods


def create_imstack(
    raw_dir, reddir, s_dir, imlist, inst, plotting_yml=None, filter_name=None
):
    """Create the stack of images by performing flat division, sky subtraction.

    Inputs:
        :raw_dir: (string) directory for the raw data
        :reddir: (string) directory for the reduced data
        :s_dir: (string) directory corresponding to a specific star.
        :imlist: (list) list of strings of paths pointing to image files.
        :inst: (Instrument object) instrument for which data is being reduced.
        :plot: (bool) determines whether or not intermediate plots should be produced.
        :fiilter_name: (string) name of the filter used for the images in question.

    Outputs:
        :im_array: (3d array) array of 2d images.
        :shifts_all: recording of all the x-y shifts made
    """
    #     method = 'brute force' # the default
    if plotting_yml:
        pl.initialize_plotting(plotting_yml)

    nims = len(imlist)
    imfiles = u.make_filelist(raw_dir, imlist, inst)

    im_array = u.read_imcube(imfiles)

    im_array = inst.adjust_array(im_array, nims)

    head = inst.head(imfiles[0])
    filt = inst.filt(nims, head, filter_name)

    # if necessary, make directory for filter. Also grab correct flat file
    fdirs = glob(s_dir + "*/")

    sf_dir = s_dir + filt + "/"
    if sf_dir not in fdirs:  # make a directory for each filt
        os.mkdir(sf_dir)

    flatfile = reddir + f"flat_{filt}.fits"
    if (
        inst.name == "PHARO" and filt == "Br-gamma"
    ):  # not sure whether this is generalizable
        flatfile = reddir + "flat_K_short.fits"
    flat = pyfits.getdata(flatfile, 0)

    skyfile = sf_dir + "sky.fits"
    sky = pyfits.getdata(skyfile, 0)
    sky[sky != sky] = 0.0  # set nans from flat=0 pixels to 0 in sky

    shifts_all = []
    for i in range(nims):
        # flat division and sky subtraction
        current_im = im_array[i, :, :]
        flat[flat == 0] = np.nan
        current_im = (
            current_im / flat
        ) - sky  # where flat = 0, this will be nan
        current_head = pyfits.getheader(imfiles[i])

        # bad pixel correction
        current_im = inst.bad_pix(current_im)

        # now deal with headers and shifts
        shifted_im, shifts = reg.shift_bruteforce(
            current_im
        )  # put it at the center

        shifts_all.append(shifts)

        #         if tests: # want to perform tests after dark subtraction and flat-fielding
        #             wides.append(reg.test_wide_binary)
        #             saturateds.append(reg.test_saturated)

        im_array[i, :, :] = shifted_im
        hdu = pyfits.PrimaryHDU(shifted_im, header=current_head)
        hdu.writeto(
            sf_dir + "sh{:02d}.fits".format(i),
            overwrite=True,
            output_verify="ignore",
        )

    pl.plot_array(
        "intermediate", im_array, -10.0, 10000.0, sf_dir, "shift1_cube.png"
    )

    # write shifts to file
    textfile = open(sf_dir + "shifts.txt", "w")
    textfile.write("im, d_row, d_col\n")
    for i, shift in enumerate(shifts_all):
        textfile.write("{},{},{}\n".format(i, *shift))
    textfile.close()
    return im_array, shifts_all


def create_im(s_dir, ssize1, plotting_yml=None, fdirs=None, method="default"):
    """Take the shifted, cut down images from before, then perform registration
    and combine. Tests should happen before this, as this is a per-star basis.
    """
    if plotting_yml:
        pl.initialize_plotting(plotting_yml)

    if not fdirs:
        fdirs = glob(s_dir + "*/")

    for sf_dir in fdirs:  # each filter

        # files = glob(sf_dir + 'sh*.fits') #reduced image files
        files = glob(
            sf_dir + f"s*.fits"
        )  # might need to change to file_prefix
        nims = len(files)
        frames = u.read_imcube(files)
        frames = frames.astype(float)

        arrsize1 = ssize1 * 2 + 1
        rots = np.zeros((nims, arrsize1, arrsize1))
        newshifts1 = []
        # newshifts2 = []
        for i in range(nims):  # each image
            image = frames[i, :, :]
            # image_centered, rot, newshifts1 = reg.register_saturated(image, ssize1, newshifts1)
            # rots[i, :, :] = rot

            if method == "saturated":
                image_centered, rot, newshifts1 = reg.register_saturated(
                    image, ssize1, newshifts1
                )
                rots[i, :, :] = rot
            elif method == "default":
                for j in range(len(image)):
                    for k in range(len(image[i])):  # change to j
                        if image[j][k] < 0.0:
                            image[j][k] = 0.0
                image_centered = reg.register_bruteforce(image)
                if len(image_centered) == 0:
                    print("Resorting to saturated mode.")
                    image_centered, rot, newshifts1 = reg.register_saturated(
                        image, ssize1, newshifts1
                    )
                    rots[i, :, :] = rot
            elif method == "saturated wide":
                rough_center = reg.find_wide_binary(image)
                image_centered = reg.register_bruteforce(
                    image, rough_center=rough_center
                )
            elif method == "wide":
                rough_center = reg.find_wide_binary(image)
                image_centered = reg.register_bruteforce(
                    image, rough_center=rough_center
                )
            frames[i, :, :] = image_centered  # newimage

        final_im = np.nanmedian(frames, axis=0)

        head = pyfits.getheader(files[0])
        hdu = pyfits.PrimaryHDU(final_im, header=head)
        hdu.writeto(
            sf_dir + "final_im.fits", overwrite=True, output_verify="ignore"
        )

        textfile1 = open(sf_dir + "shifts2.txt", "w")
        textfile1.write("im, d_row, d_col\n")
        for i, item in enumerate(newshifts1):
            textfile1.write("{},{},{}\n".format(i, *item))
        textfile1.close()
        pl.plot_array(
            "rots",
            rots,
            0.0,
            1.0,
            sf_dir,
            "rots.png",
            extent=[-ssize1, ssize1, -ssize1, ssize1],
        )
        pl.plot_array(
            "final_im", final_im, 0.0, 10000.0, sf_dir, "final_image.png"
        )
        pl.plot_array(
            "intermediate", frames, 0.0, 10000.0, sf_dir, "centers.png"
        )
