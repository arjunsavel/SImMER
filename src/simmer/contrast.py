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
import pdb
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

def contrast_curve_main(data, fwhm, instrument):
    """
    Main code to run contrast curve analysis.
    
    Inputs
    ------
        :data: (2D numpy.array, floats) image data.
        :fwhm: (float) full-width half-max of central star [pixels]
        :instrument: (str) instrument with which the the data was taken; determines
                      the plate scale used. ['PHARO' or 'ShARCS'].
                            
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
    plate_scale_dict = {'PHARO':0.025,
                        'ShARCS':0.0333}
    
    plate_scale = plate_scale_dict[instrument]
    
    contrast_result = contrast_curve_core(np.abs(data), plate_scale, radius_size=fwhm)
    means = contrast_result[0]
    stds = contrast_result[1]

    center_flux = run_ap_phot(data, fwhm)

    # intiialize the "fake im fluxes" with the central aperture flux.
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
            x, y = np.meshgrid(np.arange(-100,100), np.arange(-100,100))
            dst = np.sqrt(x*x+y*y)

            # Initializing sigma and muu: size of fake injected source
            sigma = fwhm
            muu = 0.0

            bg_std = std

            noise_image = make_noise_image((200,200), distribution='gaussian',
                                                   mean=mean, stddev=bg_std)
            # Calculating Gaussian array. tuned to a total STD=5
            fake = 7 * std * np.exp(-( (dst-muu)**2 / ( 2.0 * sigma**2 ) ) ) + noise_image + 3

            flux, err = run_ap_phot(fake, fwhm)

            # rescale to a full std of 5
            fixscale = (flux / err) / 5

            flux = flux/fixscale
            fake_im_fluxes_an += [flux]
        fake_im_fluxes += [np.nanmedian(fake_im_fluxes_an)]
        fake_im_stds += [np.nanstd(fake_im_fluxes_an)]

    fake_im_fluxes = np.array(fake_im_fluxes)

    err = 2.5*np.log10(1.0+ (fake_im_stds/fake_im_fluxes))

    indices = np.arange(len(fake_im_fluxes))
    separation = fwhm * plate_scale * indices

    contrast = -2.5*np.log10(fake_im_fluxes/center_flux[0])
    
    return separation, contrast, err

def meanclip(image, clipsig, maxiter=None, converge_num=None):
    iteration=0
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
        
        if abs(ct - lastct)/lastct <= converge_num or ct == 0:
            break
    skpix = image[subs]
    mean = np.mean(skpix)
    std = np.std(skpix)
    return mean, std

def twoD_weighted_std(data, weights):
    wm = np.sum(weights * data) / (np.sum(weights))
    numerator = np.sum(weights * ((data - wm) ** 2))

    #CDD change to speed up code
    N = np.count_nonzero(weights)

    final = np.sqrt(numerator / (((N - 1) / N) * np.sum(weights)))
    return final

def background_calc(star_data, background_method):

    # Method 1 for background - Everything outside center (bad for companions)
    if background_method == "outside":
        non_center = []
        for i in range(len(star_data)):
            for j in range(len(star_data[i])):
                if i < 265 or i > 335 or j < 265 or j > 335:
                    non_center.append(star_data[i, j])
        background_mean = np.mean(non_center)
        background_std = np.std(non_center)

    # Method 2 for background - 4 Box method (remove a box if it is wonky/high)
    if background_method == "boxes":
        box1, box2, box3, box4 = (
            star_data[100:200, 100:200],
            star_data[100:200, 400:500],
            star_data[400:500, 100:200],
            star_data[400:500, 400:500],
        )
        mean_box1, mean_box2, mean_box3, mean_box4 = (
            np.mean(box1),
            np.mean(box2),
            np.mean(box3),
            np.mean(box4),
        )
        std_box1, std_box2, std_box3, std_box4 = (
            np.std(box1),
            np.std(box2),
            np.std(box3),
            np.std(box4),
        )

        mean_boxes = []
        std_boxes = []
        if mean_box1 < (
            10 * np.mean([std_box2, std_box3, std_box4])
            + np.mean([mean_box2, mean_box3, mean_box4])
        ):
            mean_boxes.append(mean_box1)
            std_boxes.append(std_box1)
        if mean_box2 < (
            10 * np.mean([std_box1, std_box3, std_box4])
            + np.mean([mean_box1, mean_box3, mean_box4])
        ):
            mean_boxes.append(mean_box2)
            std_boxes.append(std_box2)
        if mean_box3 < (
            10 * np.mean([std_box1, std_box2, std_box4])
            + np.mean([mean_box1, mean_box2, mean_box4])
        ):
            mean_boxes.append(mean_box3)
            std_boxes.append(std_box3)
        if mean_box4 < (
            10 * np.mean([std_box2, std_box3, std_box1])
            + np.mean([mean_box2, mean_box3, mean_box1])
        ):
            mean_boxes.append(mean_box4)
            std_boxes.append(std_box4)
        background_mean = np.mean(mean_boxes)
        background_std = np.mean(std_boxes)
    # Method 3 for background - simple astropy
    if background_method == "astropy":
        (
            background_mean,
            background_median,
            background_std,
        ) = sigma_clipped_stats(star_data, sigma=5)

    return [background_mean, background_std]

def check_boundaries(data, theta1, theta2):
    """
    everything in an image that isn't between theta 1 and theta 2 goes to nan.
    """
    x, y = np.indices((data.shape))
    center = np.array(
            [(x.max() - x.min()) / 2.0, (y.max() - y.min()) / 2.0])
    theta = np.degrees(np.arctan2(y - center[1], x - center[0])) + 180
    
    in_theta = (theta < theta1) | (theta > theta2)
    
    data2 = data.copy()
    data2[in_theta] = np.nan
    return data2
        
    
def run_ap_phot(data, fwhm):
    """
    Given an image and fwhm, performs background-subtracted aperture photometry
    
    returns raw counts.
    """
    position = np.array(data.shape)//2
    aperture = CircularAperture(position, r=fwhm)

    sky_annulus_aperture = CircularAnnulus(position, r_in=fwhm * 3, r_out=fwhm*3 + 15)
    sky_annulus_mask = sky_annulus_aperture.to_mask(method='center')
    sky_annulus_data = sky_annulus_mask.multiply(data)
    sky_annulus_data_1d = sky_annulus_data[sky_annulus_mask.data > 0]
    _, median_sigclip, _ = sigma_clipped_stats(sky_annulus_data_1d)

    aperture_bg = median_sigclip * aperture.area
    phot = aperture_photometry(data, aperture)
    
    apmag = (phot['aperture_sum'] - aperture_bg)[0]
    
    skyvar = np.square(np.std(sky_annulus_data))
    phpadu = 1
    
    sigsq = skyvar/sky_annulus_aperture.area

    error1 = aperture.area*skyvar   #Scatter in sky values
    error2 = (apmag > 0)/phpadu  #Random photon noise 
    error3 = sigsq*aperture.area**2  #Uncertainty in mean sky brightness
    magerr = np.sqrt(error1 + error2 + error3)

    return apmag, magerr

def contrast_curve_core(
                        star_data,
                        plate_scale,
                        radius_size=1,
                        center=None,
                        background_method="astropy",
                        find_hots=False,
                        find_center=False,
                        background_mean=None,
                        background_std=None,
                    ):
    """
    Main function for computing contrast curves.
    
    Inputs
    ------
        :star_data: (numpy array) image array to work with.
        :radius_size: (float) width of annuli. [pixels]
        :center: (tuple) center of contrast curve computation.
        :background_method: (str) how to calculate the background.
        :find_hots: (bool) whether to remove potential hot pixels
        :find_center: (bool) whether to compute the center automatically
        :background_mean: (float) prescribed mean of background noise
        :background_std: (float) perscribed std of background noise
        :instrument: (str) PHARO or ShARCS.
    """
    
    

    # clean data slightly
    data = star_data.copy()
    
    data = np.abs(data)
    
    ################## calc background, establish center, find hot pixels ########
    
    if background_mean is None or background_std is None:
        background_mean, background_std = background_calc(data, background_method)
    
    x, y = np.indices((data.shape))

    if type(center) == type(None):
        center = np.array(
            [(x.max() - x.min()) / 2.0, (y.max() - y.min()) / 2.0]
        )
    if find_hots == True:
        hots = hot_pixels(data, center, background_mean, background_std)

    if find_center == True:
        center_vals = find_best_center(data, radius_size, center)
        center = np.array([center_vals[0], center_vals[1]])
        
    
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
    for j in range(int(number_of_a)):
        r_in = j * radius_size + radius_size
        r_out = j * radius_size + 2 * radius_size
        
        # terminate if completely outside 10 arcseconds
        if r_in * plate_scale > 10:
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
            mask_data_new = check_boundaries(mask_data_new, pie_edge_near, pie_edge_far)
            medians[j,i] = np.nanmedian(mask_data_new)
            mask_data_masked = mask_data_new[~np.isnan(mask_data_new)]
            
            mean, std = meanclip(mask_data_masked, 3, converge_num=0.2)
            stds[j, i] = std

    return medians, stds
    