"""
Module for driving large reduction processes.
"""

from glob import glob

import pandas as pd
from tqdm import tqdm

from . import darks, flats, image
from . import plotting as pl
from . import search_headers as search
from . import sky


def all_driver(inst, config_file, raw_dir, reddir, plotting_yml=None):
    """
    Runs all drivers, performing an end-to-end reduction.

    Inputs:
        :inst: (Instrument object) instrument for which data is being reduced.
        :config_file: (string) path of the config file containing plotting
            specifications. Optional.
        :plotting_yml: (string) path to the y
        :raw_dir: (string) path of the directory containing the raw data.
        :reddir: (string) path of the directory to contain the raw data.

    """

    # obtain file list from config file
    config = pd.read_csv(config_file)
    config.Object = config.Object.astype(str)

    if inst.name == "ShARCS":
        search.search_headers(raw_dir)

    if plotting_yml:
        pl.initialize_plotting(plotting_yml)

    darks.dark_driver(raw_dir, reddir, config, inst)
    flats.flat_driver(raw_dir, reddir, config, inst)
    sky.sky_driver(raw_dir, reddir, config, inst)
    methods = image.image_driver(raw_dir, reddir, config, inst)

    star_dirlist = glob(reddir + "*/")
    i = 0  # can't use tqdm on zipped objects, I believe
    for s_dir in tqdm(
        star_dirlist, desc="Running registration", position=0, leave=True
    ):
        image.create_im(s_dir, 10, method=methods[i])
        i += 1


def config_driver(inst, config_file, raw_dir, reddir):
    """
    Runs all_drivers, terminating afrer running sky_driver.

    Inputs:
        :inst: (Instrument object) instrument for which data is being reduced.
        :config_file: (string) path of the config file.
        :raw_dir: (string) path of the directory containing the raw data.
        :reddir: (string) path of the directory to contain the raw data.

    """

    # get file list from config file
    config = pd.read_csv(config_file)
    config.Object = config.Object.astype(str)

    darks.dark_driver(raw_dir, reddir, config, inst)
    flats.flat_driver(raw_dir, reddir, config, inst)
    sky.sky_driver(raw_dir, reddir, config, inst)


def image_driver(inst, config_file, raw_dir, reddir):
    """
    Runs all_drivers, terminating afrer running image_drivers.

    Inputs:
        :inst: (Instrument object) instrument for which data is being reduced.
        :config_file: (string) path of the config file.
        :raw_dir: (string) path of the directory containing the raw data.
        :reddir: (string) path of the directory to contain the raw data.
    """

    # get file list from config file
    config = pd.read_csv(config_file)
    config.Object = config.Object.astype(str)

    image.image_driver(raw_dir, reddir, config, inst)

    # Now do registration
    star_dirlist = glob(reddir + "*/")
    for s_dir in star_dirlist:
        image.create_im(s_dir, 10)
