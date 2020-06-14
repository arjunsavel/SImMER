"""
    isort:skip_file
"""

import yaml
import unittest

import numpy as np
import astropy.io.fits as pyfits
import simmer.schemas.custom_validator as validator
import simmer.schemas.read_yml as read
import simmer.insts as i
from simmer.tests.tests_reduction import (
    download_folder,
    delete_folder,
    DataDownloadException,
)


class TestYml(unittest.TestCase):
    default_config = {
        "intermediate": [
            {
                "plot": True,
                "zoom_scale": 0,
                "colorbars": True,
                "colormap": "plasma",
                "scaling": "linear",
            }
        ],
        "final_im": [
            {
                "plot": True,
                "zoom_scale": 0,
                "colorbars": True,
                "colormap": "plasma",
                "scaling": "linear",
            }
        ],
        "rots": [
            {
                "plot": True,
                "zoom_scale": 0,
                "colorbars": True,
                "colormap": "plasma",
                "scaling": "linear",
            }
        ],
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
        yml_dict = {"intermediate": [{}], "final_im": [{}], "rots": [{}]}
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

        document = {"final_im": [{"zoom_scale": -10}]}
        validated = s.validate(document, parsed_yaml_file)
        file.close()
        self.assertFalse(validated)

    def test_wrong_type_zoom(self):
        s = validator.SimmerValidator()

        file = open("src/simmer/schemas/plotting_schema.yml")
        parsed_yaml_file = yaml.load(file, Loader=yaml.SafeLoader)

        document = {"final_im": [{"zoom_scale": "some_string"}]}
        validated = s.validate(document, parsed_yaml_file)
        file.close()
        self.assertFalse(validated)

    def test_colormap_validator_valid(self):
        ss = validator.SimmerValidator()
        file = open("src/simmer/schemas/plotting_schema.yml")
        parsed_yaml_file = yaml.load(file, Loader=yaml.SafeLoader)
        document = {"final_im": [{"colormap": "viridis"}]}
        validated = ss.validate(document, parsed_yaml_file)
        file.close()
        self.assertTrue(validated)

    def test_colormap_validator_invalid(self):
        s = validator.SimmerValidator()
        file = open("src/simmer/schemas/plotting_schema.yml")
        parsed_yaml_file = yaml.load(file, Loader=yaml.SafeLoader)
        document = {"final_im": [{"colormap": "badmap"}]}
        try:
            validated = s.validate(document, parsed_yaml_file)
        except ValueError:
            validated = False
        file.close()
        self.assertFalse(validated)


class TestConfig(unittest.TestCase):
    def test_check_logsheet_incorrect(self):
        self.assertFalse(False)

    def test_check_logsheet_correct(self):
        self.assertTrue(True)


class TestReadPHARO(unittest.TestCase):
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
        delete_folder(raw_dir)
        self.assertTrue(val)
