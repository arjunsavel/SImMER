"""
Module containing all functions related to image center-finding
and stacking.
"""

import matplotlib.pylab as plt
import numpy as np
from scipy.ndimage.filters import median_filter
from scipy.ndimage.interpolation import rotate
from scipy.ndimage.interpolation import shift as subpix_shift
from skimage.feature import peak_local_max
import emcee
from numba import njit

from .scipy_utils import *

from simmer.analyze_image import *


def roll_shift(image, shifts, cval=0.0):
    """
    Rolls and shifts image.

    inputs:
        :image: (2-d array) photon counts at each pixel of each science image.
        :shifts: (1-d array of tuples) Enter shifts as (drow, dcol).
    """
    first_roll = np.roll(image, shifts[0], axis=0)
    if shifts[0] >= 0:
        first_roll[0 : shifts[0], :] = cval
    else:
        first_roll[shifts[0] :, :] = cval

    second_roll = np.roll(first_roll, shifts[1], axis=1)
    if shifts[1] >= 0:
        second_roll[:, 0 : shifts[1]] = cval
    else:
        second_roll[:, shifts[1] :] = cval

    return second_roll


def zoom_image(image, rough_center):
    """
    Zooms in around a smaller portion of the image
    for further registration.

    inputs:
        :image: (2-d array) photon counts at each pixel of each science image.
        :rough_center: (2-d array, default None) location of primary star. This
                    argument is only passed in the wide binary case.

    outputs:
        zoomed_image : (2-d array) image zoomed around the provided center.
    """
    scale = round(np.shape(image)[0] / 50)
    zoomed_image = image[
        rough_center[0] - scale : rough_center[0] + scale,
        rough_center[1] - scale : rough_center[1] + scale,
    ]
    return zoomed_image


def register_bruteforce(image, rough_center=None):
    """
    Performs the default image registration scheme. Shifts the center of the
    image to the peak.

    inputs:
        :image: (2-d array) photon counts at each pixel of each science image.
        :rough_center: (2-d array, default None) location of primary star. This
                    argument is only passed in the wide binary case.

    outputs:
        image_centered : (2-d array) image cenered by the rotations method.
    """

    def search_threshold(image):
        """
        Performs a binary search along local max thresholds. Returns coordinates corresponding
        to a threshold that only returns, at most, 3 peaks in the image.

        inputs:
            :image: (2d array) image data to be searched.

        outputs:
            :coordinates: (list) an m x 2 array

        """
        max_val = np.max(image)
        min_val = 0  # no negative values will be our peak

        # now perform binary search; first initialize lower, upper bounds
        lower_bound = min_val
        upper_bound = max_val
        while lower_bound <= upper_bound:
            threshold = np.floor((lower_bound + upper_bound) / 2)
            coordinates = peak_local_max(
                image, min_distance=100, threshold_abs=threshold
            )
            if len(coordinates) > 3:
                lower_bound = threshold + 1
            elif len(coordinates) == 0:
                upper_bound = threshold - 1
            else:
                return coordinates
        return []

    im_shape = np.shape(image)
    cent = (im_shape[0] / 2, im_shape[1] / 2)
    if rough_center is not None:
        small_image = zoom_image(image, rough_center)

        # now do binary search
        small_coordinates = search_threshold(small_image)
        coordinates_y = [
            coord[0] + (rough_center[0] - scale) for coord in small_coordinates
        ]
        coordinates_x = [
            coord[1] + (rough_center[1] - scale) for coord in small_coordinates
        ]
        coordinates = tuple(zip(coordinates_y, coordinates_x))
    else:
        coordinates = search_threshold(image)
    num_rows, num_cols = np.shape(image)
    cent = (int(num_rows / 2), int(num_cols / 2))
    base_position = cent  # if no other information available, use center
    if len(coordinates) == 0:  # if the algorithm failed
        return []  # pass that along

    yshift = base_position[0] - coordinates[0][0]
    xshift = base_position[1] - coordinates[0][1]

    image_centered = roll_shift(image, (yshift, xshift))
    return image_centered


def find_wide_binary(image):
    """
    Performs the first step of image registration for a science image that
    contains a wide binary. User input selects which target is the primary star
    of interest in the first frame of the target.

    inputs:
        :image: (2-d array) photon counts at each pixel of each science image.

    outputs:
        :rough_center: (2-element tuple) rough center of image, as determined
                        by the user.
    """

    def onclick(event):
        click_x, click_y = event.xdata, event.ydata
        rough_center.append((click_y, click_x))

        # Only select one star
        if len(rough_center) == 1:
            fig.canvas.mpl_disconnect(cid)
            plt.close(1)

    fig = plt.figure(1)
    ax = fig.add_subplot(111)
    ax.imshow(image)

    cid = fig.canvas.mpl_connect("button_press_event", onclick)

    rough_center = []
    plt.show(block=1)

    if len(rough_center) == 0:
        raise ValueError(
            "No star selected. If you are currently \
            running this code in a Jupyter environment, please \
            move to the command line/Python interpreter."
        )

    # cast as integers for later slicing
    return np.round(rough_center[0]).astype(int)


def register_saturated(image, searchsize1, newshifts1, rough_center=None):

    """
    Performs image registration when a saturated star is present in
    the science image.

    inputs:
        :image: (2-d array) photon counts at each pixel of each science image.
        :searchsize1: (int) initial size of search for center of image.
        :newshifts1: (list) keeps tracks of x-y shifts.
        :rough_center: (2-d array, default None) location of primary star. This
                    argument is only passed in the wide binary case.

    outputs:
        :image_centered: (2-d array) image centered by the rotations method.
        :rot: the rotation
        :newshifts1: (list) keeps tracks of x-y shifts.
    """
    im_shape = np.shape(image)
    cent = (im_shape[0] / 2, im_shape[1] / 2)
    if rough_center is not None:
        zoomed_image = zoom_image(image, rough_center)
        res1, im1, (xshift1, yshift1) = run_rot(
            zoomed_image, searchsize1, cent, 200
        )
        xshift1 += rough_center[1]
        yshift1 += rough_center[0]
    else:
        res1, im1, (xshift1, yshift1) = run_rot(image, searchsize1, cent, 200)
    if np.max(res1) == 0:
        rot = np.empty(res1.shape)
        rot.fill(np.nan)
    else:
        rot = res1 / np.max(res1)
    newshifts1.append((yshift1, xshift1))
    image_centered = subpix_shift(image, (yshift1, xshift1))
    return image_centered, rot, newshifts1


def rot_search(dat, x_initial, y_initial, xrad, yrad):
    """
    Perform rotational search of an image.

    Inputs:
        :dat: (2d array) image data.
        :x_initial: (int) the initial guess for the x-coordinate of the center.
        :y_initial: (int) the initial guess for the y-coordinate of the center.
        :xrad: (int) radius in x to search.
        :yrad: (int) radius in y to search.

    outputs:
        :(xshift, yshift): (tuple) record of how much the image was shifted in x and y
        :out: (2d array) output shifted image
    """
    # calculate offset from center
    xoffset = dat.shape[1] / 2 - x_initial  # from center of x
    yoffset = dat.shape[0] / 2 - y_initial
    # calcualte roll shifts for all x and y combinations within the
    # xrad, yrad regimes from the offset
    x_grid, y_grid = np.meshgrid(
        np.arange(xoffset + xrad, xoffset - xrad - 1, -1),
        np.arange(yoffset + yrad, yoffset - yrad - 1, -1),
    )

    out = []
    for (xshift, yshift) in zip(x_grid.flatten(), y_grid.flatten()):
        rolled = roll2d(dat, xshift, yshift)
        tot = rotate_sub(rolled)
        out.append(tot)
    out = np.array(out)
    out = np.reshape(out, (2 * yrad + 1, 2 * xrad + 1))

    pix = np.unravel_index(np.argmin(out), out.shape)
    xshift = x_grid[pix]
    yshift = y_grid[pix]

    return (xshift, yshift), out


def roll2d(dat, xshift, yshift):
    """
    Essentially performs numpy roll function in 2 dimensions.

    inputs:
        :dat: (2d array) image data.
        :xshift: (int) shift in the x direction.
        :yshift: (int) shift in the y direction.
    """
    # do x first
    #     for d in dat:
    #         dat = list(map(int, d))
    xshift = int(xshift)
    yshift = int(yshift)
    dat2 = np.roll(dat, xshift, axis=1)
    # zero out the wrapped around values
    if xshift > 0:
        dat2[:, 0:xshift] = 0
    else:
        dat2[
            :, dat.shape[1] + xshift : dat.shape[1]
        ] = 0  # plus sign because xshift is negative
    # now do y in similar fashion
    dat2 = np.roll(dat2, yshift, axis=0)
    if yshift > 0:
        dat2[0:yshift, :] = 0
    else:
        dat2[dat.shape[0] + yshift : dat.shape[0], :] = 0
    return dat2


def rotate_sub(dat):
    """Rotate the image about the center point, then subtract from original and record residuals.
    Does this at set angles.

    inputs:
        :dat: (2d array) image data.

    outputs:
        :total_residuals: (float) the summed total residuals.

    """
    angles = [90, 180, 270]
    total_residuals = 0.0

    for angle in angles:
        rotated_dat = rotate(dat, angle, reshape=False)
        residuals = np.sum(np.abs(dat - rotated_dat))
        total_residuals += residuals
    return total_residuals


def calc_shifts(
    dat, x_initial, y_initial, xrad, yrad, find="max", method="radon"
):
    """Do the radon search and then translate back to image coordinates."""

    if method == "rotate":
        out = rot_search(dat, x_initial, y_initial, xrad, yrad)[1]
    # elif method == 'radon':
    #     out = radonSearch(dat, x0, y0, xrad, yrad)

    # interpolate
    interped_out = imresize(out)

    if find == "max":
        pix = np.unravel_index(np.argmax(interped_out), interped_out.shape)
    elif find == "min":
        pix = np.unravel_index(np.argmin(interped_out), interped_out.shape)

    xcen = dat.shape[1] / 2
    ycen = dat.shape[0] / 2
    xoffset = xcen - x_initial
    yoffset = ycen - y_initial
    # calculate roll shifts for all x and y combinations
    x_grid, y_grid = np.meshgrid(
        np.arange(xoffset + xrad, xoffset - xrad - 1, -0.01),
        np.arange(yoffset + yrad, yoffset - yrad - 1, -0.01),
    )

    xshift = x_grid[pix]
    yshift = y_grid[pix]

    return (xshift, yshift), out


def shift_bruteforce(image, base_position=None, max_shift=200, verbose=False):
    """This will shift the maximum pixel to base_position (i.e. the center of image).
    Make sure base_position is entered as (int,int).

    max_shift: set pixels farther than max_shift from base_position to 0
               to avoid selecting brightened edges as the target star.
    """

    num_rows, num_cols = np.shape(image)
    cent = (int(num_rows / 2), int(num_cols / 2))
    if not base_position:
        base_position = cent  # if no other information available, use center

    #Mask edges to avoid selecting brightened pixels near image boundary
    #Determine maximum shift allowed in pixels (round up)
    imshape = image.shape
    max_shift = np.abs(max_shift)
    ilo = np.max([0, base_position[0] - max_shift])
    ihi  = np.min([imshape[0],base_position[0]+max_shift])
    jlo = np.max([0, base_position[1] - max_shift])
    jhi  = np.min([imshape[0],base_position[1]+max_shift])
    if max_shift == 0:
        if verbose:
            print('ERROR: Max shiftset to 0. Considering full image.')
            print('       Requested max_shift: ', max_shift)
    else:
        masked_image= image.copy()*0.
        masked_image[ilo:ihi, jlo:jhi] = image[ilo:ihi, jlo:jhi]

    # Apply a median filter to the image and find max pixel location.
    # Filter to remove hot pixels and make sure max is star.
    filtered = median_filter(masked_image, size=7)
    maxpix = np.unravel_index(np.nanargmax(filtered), filtered.shape)

    # Now shift that location to the center (or base_position)
    yshift = base_position[0] - maxpix[0]
    xshift = base_position[1] - maxpix[1]

    shifted = roll_shift(image, (yshift, xshift))

    return shifted, (yshift, xshift)


def run_rot(image, searchsize, center, newsize):
    """
    Runs all rotations.
    """
    image[np.where(image < 0.0)] = 0.0
    cut_image = image[
        int(center[0] - newsize / 2) : int(center[0] + newsize / 2),
        int(center[1] - newsize / 2) : int(center[1] + newsize / 2),
    ]
    newcent = (newsize / 2, newsize / 2)

    (xshift, yshift), res = calc_shifts(
        cut_image,
        newcent[0],
        newcent[1],
        searchsize,
        searchsize,
        find="min",
        method="rotate",
    )

    return res, cut_image, (xshift, yshift)


##### new PSF section

@njit(fastmath=True)
def gaus2d3(x=0, y=0, mx=0, my=0, sx=1, sy=1, theta=0):
    x_mid = x - mx
    y_mid = y - my

    sintheta = np.sin(theta)
    costheta = np.cos(theta)

    x_prime = x_mid * costheta - y_mid * sintheta
    y_prime = x_mid * sintheta + y_mid * costheta
    return 1. / (2. * np.pi * sx * sy) * np.exp(
        -((x_prime) ** 2. / (2. * sx ** 2.) + (y_prime) ** 2. / (2. * sy ** 2.)))


@njit
def log_prior(theta):
    mx1, my1, sx, sy, theta, log_f = theta
    if 2 <= mx1 <= 25 \
            and 2 <= my1 <= 25 \
            and 1 <= sx <= 12 \
            and 1 <= sy <= 12 \
            and 0 <= theta <= np.pi / 2 \
            and -10 <= log_f <= 1:
        return 0.0
    return -np.inf

def log_probability(theta, x, y, im1, noise):
    lp = log_prior(theta)
    if not np.isfinite(lp):
        return -np.inf
    return lp + log_likelihood(theta, x, y,im1, noise)


def log_likelihood(theta, X, Y, im1, noise):
    mx1, my1, sx, sy, theta, log_f = theta

    model1 = gaus2d3(X, Y, mx1, my1, sx, sy, theta)
    yerr1 = noise
    sigma21 = yerr1 ** 2 + model1 ** 2 * np.exp(2 * log_f)

    log_l1 = -0.5 * np.sum((im1 - model1) ** 2 / sigma21 + np.log(sigma21))

    return log_l1


def fit_psf(im, source_find='photutils'):
    """
    Performs a basic, flexible PSF fit.
    """

    x_cen, y_cen = run_starfinder(im)

    initial = [x_cen, y_cen, 2, 2, np.pi/4, 0.1]

    # slightly perturb the walkers
    pos = initial + 1e-6 * np.random.randn(24, len(initial))
    nwalkers, ndim = pos.shape

    noise = np.std(im)

    x = np.arange(0, im.shape[0])
    y = np.arange(0, im.shape[1])

    # create a grid for creating the model images
    X, Y = np.meshgrid(x, y)

    sampler = emcee.EnsembleSampler(
        nwalkers, ndim, log_probability, args=(X, Y, im, noise)
    )
    sampler.run_mcmc(pos, 30000, progress=True);

    tau = sampler.get_autocorr_time()

    discard = 3 * np.max(tau)

    thin_factor = np.max(tau) // 2

    flat_samples = sampler.get_chain(discard=discard, thin=thin_factor, flat=True)

    return flat_samples


def run_starfinder(im, **kwargs):
    """

    Outputs
    ------
        :central: (tuple) x, y coordinates of the central source
    """

    sources = find_sources(im, plot=False, **kwargs)
    central_source = find_center(sources, verbose=False)
    return central_source



def register_psf_fit(frames):
    """
    Constructs an empirical PSF for a single target, fitting for all the positions.

    Inputs
    ------
        :frames: (np.ndarray, n_image x n_x x n_y) input array containing all the images at once.

    Outputs
    -------
        :frames_centered: (np.ndarray, n_image x n_x x n_y) same as frames, but centered on the target.
    """

    n_ims = frames.shape[0]
    frames_centered = np.copy(frames)
    samples_list = []

    # iterate through the images, fit all their PSFs.
    for i in range(n_ims):
        im = frames[i, :, :]
        samples = fit_psf(im)
        samples_list += [samples]

        combined_fit = np.prod(samples_list, axis=2)


    x_av, y_av, s1_av, s2_av, theta_av, f1_av =  np.mean(combined_fit, axis=1)

    # "ratio" is the ratio between the semimajor and semiminor axis.
    ratio_av = np.max([s1_av, s2_av]) / np.max([s1_av, s2_av])

    # now we can find the centers based on inputting those parameters to the DAOStarFinder.
    for i in range(n_ims):


        im = frames[i, :, :]
        x_cen, y_cen = run_starfinder(im, theta=theta_av, ratio=ratio_av)

        # todo: refactor so no duplicated code!
        x_initial = im.shape[1] / 2
        y_initial = im.shape[0] / 2
        xoffset = x_cen - x_initial
        yoffset = y_cen - y_initial

        image_centered = subpix_shift(im, (yoffset, xoffset))
        frames_centered[i, :, :] = image_centered

    del frames
    return frames_centered

