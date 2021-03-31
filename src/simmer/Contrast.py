import math
import os

import numpy as np
import photutils
import scipy as sp
import scipy.optimize
from astropy.io import fits
from astropy.stats import SigmaClip, sigma_clipped_stats
from photutils.aperture import (
    CircularAnnulus,
    CircularAperture,
    aperture_photometry,
)


def twoD_weighted_std(data, weights):
    wm = np.sum(weights * data) / (np.sum(weights))
    numerator = np.sum(weights * ((data - wm) ** 2))
    N = 0
    for i in weights:
        for j in i:
            if j > 0:
                N += 1
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
        print("box means:", mean_boxes, "box stds:", std_boxes)
    # Method 3 for background - simple astropy
    if background_method == "astropy":
        (
            background_mean,
            background_median,
            background_std,
        ) = sigma_clipped_stats(star_data, sigma=5)

    return [background_mean, background_std]


def first_cc_val_neg(param, *args):

    center_x, center_y = param
    data = args[0]
    radius_size = args[1]
    ones = np.array([[1] * 600] * 600)

    center_ap = CircularAperture([center_x, center_y], radius_size)
    center_area = center_ap.area
    center_mask = center_ap.to_mask(method="exact")
    center_data = center_mask.multiply(data)
    center_weights = center_mask.multiply(ones)
    center_std = twoD_weighted_std(center_data, center_weights)
    center_val = (np.sum(center_data)) / center_area + 5 * center_std

    first_ap = CircularAnnulus(
        [center_x, center_y], r_in=radius_size, r_out=2 * radius_size
    )
    first_area = first_ap.area
    first_mask = first_ap.to_mask(method="exact")
    first_data = first_mask.multiply(data)
    first_weights = first_mask.multiply(ones)
    first_std = twoD_weighted_std(first_data, first_weights)
    first_val = (np.sum(first_data)) / first_area + 5 * first_std

    result = -2.5 * math.log(first_val / center_val, 10)

    return -1 * (result)


def find_best_center(data, radius_size, starting_center=[299.5, 299.5]):
    x_min, x_max = starting_center[0] - 5, starting_center[0] + 6
    y_min, y_max = starting_center[1] - 5, starting_center[1] + 6
    center = scipy.optimize.differential_evolution(
        first_cc_val_neg,
        ((x_min, x_max), (y_min, y_max)),
        args=(data, radius_size),
    )
    print(
        "Best Center at",
        [center.x[0], center.x[1]],
        "with first delta mag of",
        -1 * first_cc_val_neg((center.x[0], center.x[1]), data, radius_size),
    )
    return (
        center.x[0],
        center.x[1],
        first_cc_val_neg((center.x[0], center.x[1]), data, radius_size),
    )


def ConCur(
    star_data,
    radius_size=1,
    center=None,
    background_method="astropy",
    find_hots=False,
    find_center=False,
):

    data = star_data.copy()

    background_mean, background_std = background_calc(data, background_method)

    x, y = np.indices((data.shape))

    if not center:
        center = np.array(
            [(x.max() - x.min()) / 2.0, (y.max() - y.min()) / 2.0]
        )

    if find_hots == True:
        hots = hot_pixels(data, center, background_mean, background_std)

    if find_center == True:
        center_vals = find_best_center(data, radius_size, center)
        center = np.array([center_vals[0], center_vals[1]])

    radii = np.sqrt((x - center[0]) ** 2 + (y - center[1]) ** 2)
    radii = radii.astype(np.int)

    ones = np.array([[1] * len(data)] * len(data[0]))

    number_of_a = radii.max() / radius_size

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

    for j in range(int(number_of_a)):
        aper = CircularAnnulus(
            [center[0], center[1]],
            r_in=(j * radius_size + radius_size),
            r_out=(j * radius_size + 2 * radius_size),
        )
        all_apers.append(aper)
        all_apers_areas.append(aper.area)
        mask = aper.to_mask(method="exact")
        all_masks.append(mask)
        mask_data = mask.multiply(data)
        mask_weight = mask.multiply(ones)
        all_data.append(mask_data)
        all_weights.append(mask_weight)
        all_stds.append(twoD_weighted_std(mask_data, mask_weight))
    phot_table = aperture_photometry(data, all_apers)

    center_val = np.sum(all_data[0]) / all_apers_areas[0] + 5 * all_stds[0]

    delta_mags = []
    for i in range(len(phot_table[0]) - 3):
        try:
            delta_mags.append(
                -2.5
                * math.log(
                    (
                        np.sum(all_data[i]) / all_apers_areas[i]
                        + 5 * all_stds[i]
                    )
                    / center_val,
                    10,
                )
            )
        except ValueError:
            print(
                "annulus",
                i,
                "relative flux equal to",
                (np.sum(all_data[i]) / all_apers_areas[i] + 5 * all_stds[i])
                / center_val,
                "...it is not included",
            )
            delta_mags.append(np.NaN)

    arc_lengths = []
    for i in range(len(delta_mags)):
        arc_lengths.append(
            (i * 0.033 + 0.033) * radius_size
        )  # make sure center radius size is correct
    arc_lengths = np.array(arc_lengths)
    lim_arc_lengths = arc_lengths[arc_lengths < 10]
    delta_mags = delta_mags[: len(lim_arc_lengths)]
    delta_mags = np.array(delta_mags)
    if delta_mags[1] < 0:
        print(
            "Warning: first annulus has negative relative flux of value,",
            "%.5f" % delta_mags[1],
            "consider changing center or radius size",
        )

    return (lim_arc_lengths, delta_mags, all_stds)
