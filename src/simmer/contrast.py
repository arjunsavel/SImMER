"""
module to calculate contrast curves.

run ``contrast_curve_main'' on data (2D numpy image array)
with a specified full-width half-max (in pixels)
and instrument (string, 'PHARO' or 'ShARCS').

authors: @arjunsavel, @hgill


isort:skip_file
"""
import photutils
import numpy as np
import matplotlib.pyplot as plt
from astropy.table import QTable
from photutils.aperture import (
    CircularAnnulus,
    CircularAperture,
    aperture_photometry,
)

import numpy as np
from astropy.stats import SigmaClip, sigma_clipped_stats

from photutils.datasets import make_gaussian_sources_image
from photutils.datasets import make_noise_image
from photutils.background import StdBackgroundRMS

import pandas as pd

from tqdm import tqdm
import warnings

warnings.simplefilter("ignore")


def contrast_curve_main(data, fwhm, instrument, position=None):
    """
    Main code to run contrast curve analysis.

    Inputs
    ------
        :data: (2D numpy.array, floats) image data.
        :fwhm: (float) full-width half-max of central star [pixels]
        :instrument: (str) instrument with which the the data was taken; determines
                      the plate scale used. ['PHARO' or 'ShARCS'].
        :position: (optional; 1D numpy.array, ints) pixel coordinates of target star.
        If None, target is assumed to be at image center.

    Outputs
    -------
        :separation: (1D np.array, floats) separation from the center of the image
                      over which the contrast curves are calculated [arcseconds]
        :contrast: (1D np.array, floats) contrast of data at calculated separation
                    [delta magnitudes]
        :err: (1D np.array, floats) error on computed contrast
                    [delta magnitudes]
    """
    # assign plate scale
    plate_scale_dict = {"PHARO": 0.025, "ShARCS": 0.0333}

    plate_scale = plate_scale_dict[instrument]

    #set radius_size so that radius is no larger than 1"
    radius_size = np.min([1./plate_scale, fwhm])

#DO NOT TAKE ABSOLUTE VALUE!
    contrast_result = contrast_curve_core(
        data, plate_scale, fwhm=fwhm, radius_size=radius_size, center=position
    )
    separation = contrast_result[0]
    means = contrast_result[1]
    stds = contrast_result[2]

    center_flux = run_ap_phot(data, fwhm, position=position)

    # intiialize the "fake im fluxes" with the central aperture flux.
    all_seps = [0]
    fake_im_fluxes = [center_flux[0]]
    fake_im_stds = [center_flux[1]]

    fake_ims = []

    for i, (all_mean, all_std) in enumerate(zip(means, stds)):
        # initialize fake fluxes for a given annulus
        fake_im_fluxes_an = []
        n_annuli = 12
        for j in range(n_annuli):
            mean = all_mean[j]
            std = all_std[j]
            x, y = np.meshgrid(np.arange(-1000, 1000), np.arange(-1000, 1000)) #was 100x100; CDD made larger for poor FWHMs
            dst = np.sqrt(x * x + y * y)

            # Initializing sigma and muu: size of fake injected source
            sigma = fwhm
            muu = 0.0

            bg_std = std

            noise_image = make_noise_image(
                (2000, 2000), distribution="gaussian", mean=mean, stddev=bg_std
            ) #Was 200x200, but that's too small for some images because the sky annulus falls outside the fake image for high FWHM.
            # Calculating Gaussian array. tuned to a total STD=5
            fake = (
                7 * std * np.exp(-((dst - muu) ** 2 / (2.0 * sigma**2)))
                + noise_image
                + 3
            )

            flux, err = run_ap_phot(fake, fwhm)

            # rescale to a full std of 5
            fixscale = (flux / err) / 5

            flux = flux / fixscale
            fake_im_fluxes_an += [flux]
        fake_im_fluxes += [np.nanmedian(fake_im_fluxes_an)]
        fake_im_stds += [np.nanstd(fake_im_fluxes_an)]
        all_seps += [separation[i]]

    fake_im_fluxes = np.array(fake_im_fluxes)

    err = 2.5 * np.log10(1.0 + (fake_im_stds / fake_im_fluxes))

#DELETE THIS
#    indices = np.arange(len(fake_im_fluxes))
#    separation = fwhm * plate_scale * indices

    contrast = -2.5 * np.log10(fake_im_fluxes / center_flux[0])

    #Save contrast curve as a pandas DataFrame
    df = pd.DataFrame({'arcsec': all_seps, 'dmag': contrast, 'dmrms': err})

    return df #separation, contrast, err


def meanclip(image, clipsig, maxiter=None, converge_num=None):
    iteration = 0
    ct = len(image)
    image = image.flatten()
    subs = np.where(image)[0]
    while True:
        skpix = image[subs]
        iteration += 1
        lastct = ct
        medval = np.median(skpix)
        sig = np.std(skpix)
        wsm = np.where(np.abs(skpix - medval) < clipsig * sig)[0]
        ct = len(wsm)
        subs = subs[wsm]

        if abs(ct - lastct) / lastct <= converge_num or ct == 0:
            break
    skpix = image[subs]
    mean = np.mean(skpix)
    std = np.std(skpix)
    return mean, std


def twoD_weighted_std(data, weights):
    wm = np.sum(weights * data) / (np.sum(weights))
    numerator = np.sum(weights * ((data - wm) ** 2))

    # CDD change to speed up code
    N = np.count_nonzero(weights)

    final = np.sqrt(numerator / (((N - 1) / N) * np.sum(weights)))
    return final

def check_boundaries(data, theta1, theta2):
    """
    everything in an image that isn't between theta 1 and theta 2 goes to nan.
    """
    x, y = np.indices((data.shape))
    center = np.array([(x.max() - x.min()) / 2.0, (y.max() - y.min()) / 2.0])
    theta = np.degrees(np.arctan2(y - center[1], x - center[0])) + 180

    in_theta = (theta < theta1) | (theta > theta2)

    data2 = data.copy()
    data2[in_theta] = np.nan
    return data2


def run_ap_phot(data, fwhm, position=None):
    """
    Given an image and fwhm, performs background-subtracted aperture photometry
    returns raw counts. Unless position is set, aperture photometry will be performed
    around image center.
    """
    if type(position) == type(None):
        position = np.array(data.shape) // 2

    aperture = CircularAperture(position, r=fwhm)

    sky_annulus_aperture = CircularAnnulus(
        position, r_in=fwhm * 3, r_out=fwhm * 3 + 15
    )
    sky_annulus_mask = sky_annulus_aperture.to_mask(method="center")
    sky_annulus_data = sky_annulus_mask.multiply(data)
    sky_annulus_data_1d = sky_annulus_data[sky_annulus_mask.data > 0]
    _, median_sigclip, _ = sigma_clipped_stats(sky_annulus_data_1d)

    aperture_bg = median_sigclip * aperture.area
    phot = aperture_photometry(data, aperture)

    apmag = (phot["aperture_sum"] - aperture_bg)[0]

    skyvar = np.square(np.std(sky_annulus_data))
    phpadu = 1

    sigsq = skyvar / sky_annulus_aperture.area

    error1 = aperture.area * skyvar  # Scatter in sky values
    error2 = (apmag > 0) / phpadu  # Random photon noise
    error3 = sigsq * aperture.area**2  # Uncertainty in mean sky brightness
    magerr = np.sqrt(error1 + error2 + error3)

    return apmag, magerr


def contrast_curve_core(
    star_data,
    plate_scale,
    fwhm=1,
    radius_size=None,
    center=None,
):
    """
    Main function for computing contrast curves.

    Inputs
    ------
        :star_data: (numpy array) image array to work with.
        :fwhm: (float) full-width half-max of target [pixels]
        :radius_size: (float) width of annuli. [pixels]; defaults to FWHM if not set
        :center: (tuple) center of contrast curve computation.
        :instrument: (str) PHARO or ShARCS.
    """

    # make copy of data array
    data = star_data.copy()

#    data = np.abs(data) #DO NOT DO THIS!!!! It's making the standard deviation too small later.

    ################## establish center ########

    x, y = np.indices((data.shape))

    if type(center) == type(None):
        center = np.array(
            [(x.max() - x.min()) / 2.0, (y.max() - y.min()) / 2.0]
        )

    if type(radius_size) == type(None):
        radius_size = fwhm

    ########## set up radial coordinate system ########

    radii = np.sqrt((x - center[0]) ** 2 + (y - center[1]) ** 2)
    radii = radii.astype(np.int64)

    ones = np.ones_like(data)

    number_of_a = int(radii.max() / radius_size)

    pie_edges = np.arange(0, 390, 30)

    ######## set up aperture array ##########
    center_ap = CircularAperture([center[0], center[1]], radius_size)

    all_apers, all_apers_areas, all_masks = (
        [center_ap],
        [center_ap.area],
        [center_ap.to_mask(method="exact")],
    )

    all_data, all_weights = [all_masks[0].multiply(data)], [
        all_masks[0].multiply(ones)
    ]

    all_stds = [twoD_weighted_std(all_data[0], all_weights[0])]

    ######## construct the apertures of the annuli #######
    sigma_clip = SigmaClip(sigma=3.0)
    bkgrms = StdBackgroundRMS(sigma_clip)

    medians = np.zeros((number_of_a, len(pie_edges) - 1))
    stds = np.zeros((number_of_a, len(pie_edges) - 1))
    seps = np.zeros(number_of_a)
    for j in range(int(number_of_a)):
        r_in = j * radius_size + fwhm
        r_out = j * radius_size + radius_size + fwhm
        seps[j] = (r_in+r_out)/2.*plate_scale

        # terminate if completely outside 10 arcseconds
        if (r_in * plate_scale) > 10:
            break

        # create aperture
        aper = CircularAnnulus(
            [center[0], center[1]],
            r_in=r_in,
            r_out=r_out,
        )

        # multiply the data by the aperture mask and store it
        all_apers.append(aper)
        all_apers_areas.append(aper.area)
        mask = aper.to_mask(method="exact")
        all_masks.append(mask)
        mask_data = mask.multiply(data)

        mask_weight = mask.multiply(ones)

        for i, pie_edge_near in enumerate(pie_edges[:-1]):
            pie_edge_far = pie_edges[i + 1]
            mask_data_new = mask_data.copy()
            mask_data_new = check_boundaries(
                mask_data_new, pie_edge_near, pie_edge_far
            )
            medians[j, i] = np.nanmedian(mask_data_new)
            mask_data_masked = mask_data_new[~np.isnan(mask_data_new)]

            mean, std = meanclip(mask_data_masked, 3, converge_num=0.2)
            stds[j, i] = std

    #Return only the medians and stds for distances within the desired range
    seps = seps[0:j]
    medians = medians[0:j,:]
    stds = stds[0:j,:]
    return seps, medians, stds
