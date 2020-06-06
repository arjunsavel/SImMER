"""
    isort:skip_file
"""

import yaml
import unittest
import sys
import os

sys.path.append(os.getcwd()[:-6])
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


parent_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))

import schemas.custom_validator as validator


class TestYml(unittest.TestCase):
    def test_validator_instantiate(self):
        try:
            validator.SimmerValidator()
            instantiated = True
        except:
            instantiated = False
        self.assertTrue(instantiated)

    def test_validate(self):
        s = validator.SimmerValidator()

        file = open("../schemas/plotting.yml")
        parsed_yaml_file = yaml.load(file, Loader=yaml.SafeLoader)
        test_file = open("test_validate.yml")
        test_yaml_file = yaml.load(test_file, Loader=yaml.SafeLoader)
        validated = s.validate(test_yaml_file, parsed_yaml_file)
        file.close()
        test_file.close()
        self.assertTrue(validated)

    def test_bad_zoom(self):
        s = validator.SimmerValidator()

        file = open("../schemas/plotting.yml")
        parsed_yaml_file = yaml.load(file, Loader=yaml.SafeLoader)

        document = {"final_im": {"zoom_scale": -10}}
        validated = s.validate(document, parsed_yaml_file)
        file.close()
        self.assertFalse(validated)
