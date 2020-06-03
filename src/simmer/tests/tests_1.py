import inspect
import os
import sys
import unittest
import urllib.request
import zipfile
from glob import glob

sys.path.append(os.getcwd()[:-6])
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


parent_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))

import astropy.io.fits as pyfits
import darks
import drivers
import flats
import image
import insts as i
import numpy as np
import pandas as pd
import sky


# sys.path.insert(0, os.getcwd())
# parent_dir = os.path.dirname(current_dir)
# current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))


def download_folder(folder, path=None):
    """
	Downloads a .zip file from this projects S3 testing bucket, unzips it, and deletes
	the .zip file.

	Inputs:
		folder : (string) name of the folder to be downloaded.
	"""

    def retrieve_extract(path):
        with zipfile.ZipFile(folder + ".zip", "r") as zip_ref:
            zip_ref.extractall(path)

    folder_url = (
        f"https://simmertesting.s3-us-west-1.amazonaws.com/{folder}.zip"
    )
    urllib.request.urlretrieve(folder_url, folder + ".zip")
    if path:
        retrieve_extract(path)
    elif "src" in os.listdir():  # if we're actually running tests
        retrieve_extract("src/simmer/tests/")
    else:  # we're running this in an arbitrary directory
        retrieve_extract("")
    os.remove(folder + ".zip")


def delete_folder(folder):
    if os.listdir(folder):
        for f in os.listdir(folder):
            if folder[-1] == "/":
                path = folder + f
            else:
                path = folder + "/" + f
            if os.path.isfile(path):
                os.remove(path)
            else:  # if it's a directory!
                delete_folder(path)
    os.rmdir(folder)


class TestCreation(unittest.TestCase):

    inst = i.ShARCS()

    def test_create_darks(self):
        print("Testing darks")
        download_folder("dark_test")
        raw_dir, reddir = (
            "src/simmer/tests/dark_test/",
            "src/simmer/tests/dark_test/",
        )
        compare_dark = pyfits.getdata(raw_dir + "compare_dark.fits", 0)
        zero = np.zeros(np.shape(compare_dark))  # only testing flats
        darklist = range(1357, 1360)
        result = darks.create_darks(raw_dir, reddir, darklist, self.inst)
        delete_folder(raw_dir)
        self.assertCountEqual(np.ravel(result - compare_dark), np.ravel(zero))

    def test_create_flats(self):
        print("Testing flats")
        download_folder("flat_test")
        raw_dir, reddir = (
            "src/simmer/tests/flat_test/",
            "src/simmer/tests/flat_test/",
        )
        compare_flat = pyfits.getdata(raw_dir + "compare_flat.fits", 0)
        zero = np.zeros(np.shape(compare_flat))  # only testing flats
        flatlist = range(1108, 1114)
        result = flats.create_flats(
            raw_dir, reddir, flatlist, np.nan, self.inst, test=True
        )

        delete_folder(raw_dir)
        self.assertCountEqual(np.ravel(result - compare_flat), np.ravel(zero))

    def test_create_skies(self):
        print("Testing skies")
        download_folder("sky_test")
        raw_dir, reddir = (
            "src/simmer/tests/sky_test/",
            "src/simmer/tests/sky_test/",
        )
        compare_sky = np.loadtxt(raw_dir + "compare_sky.txt")
        s_dir = raw_dir
        skylist = range(1218, 1222)
        result = sky.create_skies(raw_dir, reddir, s_dir, skylist, self.inst)
        zero = np.zeros(np.shape(compare_sky))

        delete_folder(raw_dir)
        self.assertCountEqual(np.ravel(result - compare_sky), np.ravel(zero))

    def test_create_imstack(self):
        print("Testing imstack")
        download_folder("sky_test")
        raw_dir, reddir = (
            "src/simmer/tests/sky_test/",
            "src/simmer/tests/sky_test/",
        )
        imlist = range(1218, 1222)
        s_dir = raw_dir
        result, shifts_all = image.create_imstack(
            raw_dir, reddir, s_dir, imlist, self.inst
        )
        compare_list = [
            "compare_create_imstack_0",
            "compare_create_imstack_1",
            "compare_create_imstack_2",
            "compare_create_imstack_3",
        ]
        compare_imstack = np.array(
            [np.loadtxt(raw_dir + file) for file in compare_list]
        )
        zero = np.zeros(np.shape(compare_imstack))
        delete_folder(raw_dir)
        self.assertCountEqual(
            np.ravel(result - compare_imstack), np.ravel(zero)
        )

    def test_create_im_default(self):
        print("Testing default image creation")
        download_folder("sky_test")
        raw_dir, reddir = (
            "src/simmer/tests/sky_test/",
            "src/simmer/tests/sky_test/",
        )
        s_dir = raw_dir
        compare_final_im = pyfits.getdata(
            raw_dir + "Ks/compare_final_im_default.fits", 0
        )
        image.create_im(s_dir, 10, method="default")
        final_im = pyfits.getdata(raw_dir + "Ks/final_im.fits", 0)
        zero = np.zeros(np.shape(final_im))
        val = np.all(np.ravel(final_im - compare_final_im) == np.ravel(zero))
        delete_folder(raw_dir)
        self.assertTrue(val)

    def test_create_im_saturated(self):
        print("Testing saturated image creation")
        download_folder("sky_test")
        raw_dir, reddir = (
            "src/simmer/tests/sky_test/",
            "src/simmer/tests/sky_test/",
        )
        s_dir = raw_dir
        compare_final_im = pyfits.getdata(
            raw_dir + "Ks/compare_final_im.fits", 0
        )
        image.create_im(s_dir, 10, method="saturated")
        final_im = pyfits.getdata(raw_dir + "Ks/final_im.fits", 0)
        zero = np.zeros(np.shape(final_im))
        val = np.all(np.allclose(final_im, compare_final_im))
        delete_folder(raw_dir)
        self.assertTrue(val)


class TestDrivers(unittest.TestCase):
    inst = i.ShARCS()

    def test_dark_driver(self):
        print("Testing dark driver")
        download_folder("dark_test")
        raw_dir, reddir = (
            "src/simmer/tests/dark_test/",
            "src/simmer/tests/dark_test/",
        )
        config = pd.read_csv(os.getcwd() + "/src/simmer/tests/test_config.csv")
        darks.dark_driver(raw_dir, reddir, config, self.inst)
        val = "dark_3sec.fits" in os.listdir(raw_dir)
        delete_folder(raw_dir)
        self.assertTrue(val)

    def test_flat_driver(self):
        print("Testing flat driver")
        download_folder("flat_test")
        raw_dir, reddir = (
            "src/simmer/tests/flat_test/",
            "src/simmer/tests/flat_test/",
        )
        config = pd.read_csv(os.getcwd() + "/src/simmer/tests/test_config.csv")
        source = raw_dir + "flat_J.fits"
        dest = raw_dir + "temp.fits"
        os.rename(source, dest)
        flats.flat_driver(raw_dir, reddir, config, self.inst)
        val = "flat_J.fits" in os.listdir(raw_dir)
        os.remove(raw_dir + "flat_J.fits")
        os.rename(dest, source)
        delete_folder(raw_dir)
        self.assertTrue(val)

    def test_sky_driver(self):
        print("Testing sky driver")
        download_folder("sky_test")
        raw_dir, reddir = (
            "src/simmer/tests/sky_test/",
            "src/simmer/tests/sky_test/",
        )
        config = pd.read_csv(os.getcwd() + "/src/simmer/tests/test_config.csv")
        sky.sky_driver(raw_dir, reddir, config, self.inst)
        val = "sky.fits" in os.listdir(raw_dir + "/K09203794/Ks")
        delete_folder(raw_dir)
        self.assertTrue(val)

    def test_image_driver(self):
        print("Testing image driver")
        download_folder("image_test")
        raw_dir, reddir = (
            "src/simmer/tests/image_test/",
            "src/simmer/tests/image_test/",
        )
        config = pd.read_csv(os.getcwd() + "/src/simmer/tests/test_config.csv")
        method = image.image_driver(raw_dir, reddir, config, self.inst)
        remove_files = [
            "sh00.fits",
            "sh01.fits",
            "sh02.fits",
            "sh03.fits",
            "shifts.txt",
        ]
        val = np.all(
            [r in os.listdir(raw_dir + f"K09203794/Ks") for r in remove_files]
        )
        delete_folder(raw_dir)
        self.assertTrue(val)


class TestIntegration(unittest.TestCase):
    p = i.PHARO()

    def test_PHARO_all_drivers(self):
        print("Testing PHARO integration")  # need better way to get config?
        download_folder("PHARO_integration")
        raw_dir, reddir = (
            os.getcwd() + "/src/simmer/tests/PHARO_integration/",
            os.getcwd() + "/src/simmer/tests/PHARO_integration/",
        )
        config_file = os.getcwd() + "/config.csv"
        drivers.all_driver(self.p, config_file, raw_dir, reddir)
        compare_final_im = pyfits.getdata(raw_dir + "compare_final_im.fits", 0)
        final_im = pyfits.getdata(
            raw_dir + "HIP49081/Br-gamma/final_im.fits", 0
        )
        zero = np.zeros(np.shape(final_im))
        val = np.all(np.allclose(final_im, compare_final_im, equal_nan=True))

        delete_folder(raw_dir)
        self.assertTrue(val)

    def test_PHARO_config_drivers(self):
        print(
            "Testing PHARO config integration"
        )  # need better way to get config?
        download_folder("PHARO_config_driver")
        raw_dir, reddir = (
            os.getcwd() + "/src/simmer/tests/PHARO_config_driver/",
            os.getcwd() + "/src/simmer/tests/PHARO_config_driver/",
        )
        config_file = os.getcwd() + "/config.csv"
        drivers.config_driver(self.p, config_file, raw_dir, reddir)
        sky = pyfits.getdata(raw_dir + "HIP49081/Br-gamma/sky.fits", 0)
        compare_sky = pyfits.getdata(
            raw_dir + "HIP49081/Br-gamma/compare_sky.fits", 0
        )
        zero = np.zeros(np.shape(compare_sky))
        val = np.all(np.allclose(compare_sky, sky, equal_nan=True))

        delete_folder(raw_dir)
        self.assertTrue(val)

    def test_PHARO_image_drivers(self):
        print(
            "Testing PHARO image integration"
        )  # need to actually point to correct folder, change aodirs
        download_folder("PHARO_image_driver")
        raw_dir, reddir = (
            os.getcwd() + "/src/simmer/tests/PHARO_image_driver/",
            os.getcwd() + "/src/simmer/tests/PHARO_image_driver/",
        )
        config_file = os.getcwd() + "/config.csv"
        drivers.image_driver(self.p, config_file, raw_dir, reddir)
        remove_files = [
            "sh00.fits",
            "sh01.fits",
            "sh02.fits",
            "sh03.fits",
            "shifts.txt",
        ]
        val = np.all(
            [
                r in os.listdir(raw_dir + "HIP49081/Br-gamma/")
                for r in remove_files
            ]
        )

        file_dir = os.getcwd() + "/src/simmer/tests/PHARO_image_driver/"
        delete_folder(raw_dir)
        self.assertTrue(val)
