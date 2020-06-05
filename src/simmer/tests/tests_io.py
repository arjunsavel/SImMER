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

        file = open("../src/simmer/schemas/plotting.yml")
        parsed_yaml_file = yaml.load(file, Loader=yaml.SafeLoader)

        document = {"final_im": {"zoom": 20}}
        try:
            s.validate(document, parsed_yaml_file)
            validated = True
        except:
            validated = False
        file.close()
        self.assertTrue(validated)

    def test_bad_zoom(self):
        s = validator.SimmerValidator()

        file = open("../src/simmer/schemas/plotting.yml")
        parsed_yaml_file = yaml.load(file, Loader=yaml.SafeLoader)

        document = {"final_im": {"zoom": -10}}
        try:
            s.validate(document, parsed_yaml_file)
            caught = False
        except:
            caught = True
        file.close()
        self.assertTrue(caught)
