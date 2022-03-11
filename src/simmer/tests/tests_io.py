"""
    isort:skip_file
"""

import yaml
import unittest
from shutil import copyfile
import os

import pandas as pd
import numpy as np
import astropy.io.fits as pyfits
import simmer.add_dark_exp as ad
import simmer.schemas.custom_validator as validator
import simmer.schemas.read_yml as read
import simmer.insts as i
import simmer.create_config as c
import simmer.check_logsheet as check
import simmer.search_headers as search
from simmer.tests.tests_reduction import (
    download_folder,
    delete_folder,
    DataDownloadException,
)

from contextlib import contextmanager
from io import StringIO
import sys


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class TestYml(unittest.TestCase):
    default_config = {
        "intermediate": {
            "plot": True,
            "zoom_scale": 0,
            "colorbars": True,
            "colormap": "plasma",
            "scaling": "linear",
        },
        "final_im": {
            "plot": True,
            "zoom_scale": 0,
            "colorbars": True,
            "colormap": "plasma",
            "scaling": "linear",
        },
        "rots": {
            "plot": True,
            "zoom_scale": 0,
            "colorbars": True,
            "colormap": "plasma",
            "scaling": "linear",
        },
    }

    plot_types = ["intermediate", "final_im", "rots"]

    def test_validator_instantiate(self):
        try:
            validator.SimmerValidator()
            instantiated = True
        except:
            instantiated = False
        self.assertTrue(instantiated)

    def test_validate(self):
        schema_filename = "src/simmer/schemas/plotting_schema.yml"
        yml_filename = "src/simmer/tests/test_validate.yml"
        validated = read.validate_yml(schema_filename, yml_filename)
        self.assertTrue(validated)

    def test_empty_yaml(self):
        yml_dict = {"intermediate": {}, "final_im": {}, "rots": {}}
        ss = validator.SimmerValidator()
        file = open("src/simmer/schemas/plotting_schema.yml")
        parsed_yaml_file = yaml.load(file, Loader=yaml.SafeLoader)
        ss.schema = parsed_yaml_file
        file.close()
        self.assertEqual(ss.normalized(yml_dict), self.default_config)

    def test_negative_zoom(self):
        s = validator.SimmerValidator()

        file = open("src/simmer/schemas/plotting_schema.yml")
        parsed_yaml_file = yaml.load(file, Loader=yaml.SafeLoader)

        document = {"final_im": {"zoom_scale": -10}}
        validated = s.validate(document, parsed_yaml_file)
        file.close()
        self.assertFalse(validated)

    def test_wrong_type_zoom(self):
        s = validator.SimmerValidator()

        file = open("src/simmer/schemas/plotting_schema.yml")
        parsed_yaml_file = yaml.load(file, Loader=yaml.SafeLoader)

        document = {"final_im": {"zoom_scale": "some_string"}}
        validated = s.validate(document, parsed_yaml_file)
        file.close()
        self.assertFalse(validated)

    def test_colormap_validator_valid(self):
        ss = validator.SimmerValidator()
        file = open("src/simmer/schemas/plotting_schema.yml")
        parsed_yaml_file = yaml.load(file, Loader=yaml.SafeLoader)
        document = {"final_im": {"colormap": "viridis"}}
        validated = ss.validate(document, parsed_yaml_file)
        file.close()
        self.assertTrue(validated)

    def test_colormap_validator_invalid(self):
        s = validator.SimmerValidator()
        file = open("src/simmer/schemas/plotting_schema.yml")
        parsed_yaml_file = yaml.load(file, Loader=yaml.SafeLoader)
        s.schema = parsed_yaml_file
        document = {"final_im": {"colormap": "badmap"}}
        try:
            validated = s.validate(document)
        except ValueError:
            validated = False
        file.close()
        self.assertFalse(validated)


class TestConfig(unittest.TestCase):
    def test_create_config_csv(self):
        try:
            download_folder("config_test")
        except:
            raise DataDownloadException(
                "Could not download test data for config_test."
            )
        tab = "Sheet1"
        excel_path = "src/simmer/Examples/PHARO/logsheet.csv"
        c.create_config(excel_path, "created_frame.csv", tab)
        created_frame = pd.read_csv("created_frame.csv")
        compare_frame = pd.read_csv(
            "src/simmer/tests/config_test/compare_frame_csv.csv"
        )
        delete_folder("src/simmer/tests/config_test")

        self.assertTrue(
            created_frame.drop("Method", axis=1).equals(compare_frame)
        )

    def test_create_config_xlsx(self):
        try:
            download_folder("config_test")
        except:
            raise DataDownloadException(
                "Could not download test data for config_test."
            )
        tab = "Sheet1"
        excel_path = "src/simmer/Examples/Shane/logsheet.xlsx"
        c.create_config(excel_path, "created_frame.csv", tab)
        created_frame = pd.read_csv("created_frame.csv")
        compare_frame = pd.read_csv(
            "src/simmer/tests/config_test/created_frame_xlsx.csv"
        )
        delete_folder("src/simmer/tests/config_test")
        self.assertTrue(
            created_frame.drop("Method", axis=1).equals(compare_frame)
        )

    def test_check_logsheet_incorrect(self):
        inst = i.ShARCS()
        excel_path = "src/simmer/Examples/Shane/logsheet_incorrect.xlsx"
        failed = check.check_logsheet(inst, excel_path)
        self.assertTrue(failed == 7)

    def test_check_logsheet_correct(self):
        inst = i.ShARCS()
        excel_path = "src/simmer/Examples/PHARO/logsheet.csv"
        failed = check.check_logsheet(inst, excel_path)
        self.assertTrue(failed == 0)

    def test_add_dark_exposure(self):
        try:
            download_folder("dark_test")
        except:
            raise DataDownloadException(
                "Could not download test data for darks."
            )
        excel_path = "src/simmer/Examples/Shane/logsheet.xlsx"
        copy_path = "src/simmer/Examples/Shane/logsheet_copy.xlsx"
        copyfile(excel_path, copy_path)
        raw_dir = "src/simmer/tests/dark_test/"
        tab = "Sheet1"
        inst = i.ShARCS()
        ad.add_dark_exp(inst, copy_path, raw_dir, tab)
        os.remove(copy_path)
        delete_folder(raw_dir)
        self.assertTrue(True)

    def test_LogsheetError(self):
        try:
            download_folder("config_test")
        except:
            raise DataDownloadException(
                "Could not download test data for config_test."
            )

        tab = "Sheet1"
        logsheet_path = "src/simmer/Examples/PHARO/logsheet.csv"
        frame = pd.read_csv(logsheet_path)

        nan_start_config_path = "src/simmer/tests/nan_start_config_test.csv"

        frame.loc[20, "Start"] = np.nan
        frame.to_csv(nan_start_config_path)

        self.assertRaises(
            c.LogsheetError,
            c.create_config,
            nan_start_config_path,
            "created_frame.csv",
            tab,
        )


class TestPHAROSpecific(unittest.TestCase):
    inst = i.PHARO()

    def test_readpharo_quadrants(self):
        try:
            download_folder("readpharo_test")
        except:
            raise DataDownloadException(
                "Could not download test data for readpharo function."
            )
        raw_dir, new_dir, test_red_dir = (
            "src/simmer/tests/readpharo_test/raw/",
            "src/simmer/tests/readpharo_test/test_newdir/",
            "src/simmer/tests/readpharo_test/test_red/",
        )
        self.inst.read_data(raw_dir, new_dir)
        compare_flattened = pyfits.getdata(test_red_dir + "sph0436.fits")
        zero = np.zeros(np.shape(compare_flattened))
        flattened = pyfits.getdata(new_dir + "sph0436.fits")
        val = np.all(np.allclose(compare_flattened, flattened, equal_nan=True))
        delete_folder("src/simmer/tests/readpharo_test")
        self.assertTrue(val)


class TestShARCSSpecific(unittest.TestCase):
    inst = i.ShARCS()

    def test_search_headers_no_framenum(self):
        """
        Tests the search_headers function against
        the original file that caused the issue.
        """
        try:
            download_folder("search_headers")
        except:
            raise DataDownloadException(
                "Could not download test data for skies."
            )
        raw_dir = "src/simmer/tests/test_search_header/"
        data, header = pyfits.getdata(
            raw_dir + "wrong_header.fits", header=True
        )
        del header["FRAMENUM"]
        pyfits.writeto(
            raw_dir + "wrong_header.fits", data, header, overwrite=True
        )

        with captured_output() as (out, err):
            search.search_headers(raw_dir)
        anticipated_string = "Header Incomplete in src/simmer/tests/test_search_header/wrong_header.fits!!!"
        # This can go inside or outside the `with` block
        output = out.getvalue().strip()
        delete_folder(raw_dir)
        self.assertEqual(output, anticipated_string)

    def test_search_headers_no_datafile(self):
        """
        Tests the search_headers function against
        the original file that caused the issue.
        """
        try:
            download_folder("search_headers")
        except:
            raise DataDownloadException(
                "Could not download test data for skies."
            )
        raw_dir = "src/simmer/tests/test_search_header/"
        data, header = pyfits.getdata(
            raw_dir + "wrong_header.fits", header=True
        )
        del header["DATAFILE"]
        pyfits.writeto(
            raw_dir + "wrong_header.fits", data, header, overwrite=True
        )

        with captured_output() as (out, err):
            search.search_headers(raw_dir)
        anticipated_string = "Header Incomplete in src/simmer/tests/test_search_header/wrong_header.fits!!!"
        # This can go inside or outside the `with` block
        output = out.getvalue().strip()
        delete_folder(raw_dir)
        self.assertEqual(output, anticipated_string)

    def test_search_headers(self):
        try:
            download_folder("sky_test")
        except:
            raise DataDownloadException(
                "Could not download test data for skies."
            )

        raw_dir, write_dir = (
            "src/simmer/tests/sky_test/",
            "src/simmer/tests/sky_test/",
        )
        search.search_headers(raw_dir, write_dir)
        val = True
        f = open(write_dir + "headers_wrong.txt", "r")
        for line in f:
            if "INCOMPLETE" in line:
                val = False
        f.close()
        self.assertTrue(val)
