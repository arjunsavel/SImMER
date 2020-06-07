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
import schemas.read_yml as read


class TestYml(unittest.TestCase):
    default_config = {
        "intermediate": {
            "plot": True,
            "output_fits": True,
            "zoom_scale": 0,
            "colorbars": True,
            "colormap": "plasma",
            "scaling": "linear",
        },
        "final_im": {
            "plot": True,
            "output_fits": True,
            "zoom_scale": 0,
            "colorbars": True,
            "colormap": "plasma",
            "scaling": "linear",
        },
        "rots": {
            "plot": True,
            "output_fits": True,
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
        s = validator.SimmerValidator()
        file = open("src/simmer/schemas/plotting_schema")
        parsed_yaml_file = yaml.load(file, Loader=yaml.SafeLoader)
        test_file = open("src/simmer/tests/test_validate.yml")
        test_yaml_file = yaml.load(test_file, Loader=yaml.SafeLoader)
        validated = s.validate(test_yaml_file, parsed_yaml_file)
        file.close()
        test_file.close()
        self.assertTrue(validated)

    def test_empty_yaml(self):
        yml_dict = {"intermediate": {}, "final_im": {}, "rots": {}}
        s = validator.SimmerValidator()
        file = open("src/simmer/schemas/plotting_schema")
        parsed_yaml_file = yaml.load(file, Loader=yaml.SafeLoader)
        s.schema = parsed_yaml_file
        file.close()
        self.assertEqual(s.normalized(yml_dict), self.default_config)

    def test_incomplete_yaml(self):
        yml_dict = {"intermediate": {}, "final_im": {}, "rots": {}}
        s = validator.SimmerValidator()
        file = open("src/simmer/schemas/plotting_schema")
        schema = yaml.load(file, Loader=yaml.SafeLoader)
        file.close()
        normalized = read.normalize(yml_dict, s, schema, self.plot_types)
        self.assertEqual(normalized, self.default_config)

    def test_negative_zoom(self):
        s = validator.SimmerValidator()

        file = open("src/simmer/schemas/plotting_schema")
        parsed_yaml_file = yaml.load(file, Loader=yaml.SafeLoader)

        document = {"final_im": {"zoom_scale": -10}}
        validated = s.validate(document, parsed_yaml_file)
        file.close()
        self.assertFalse(validated)

    def test_wrong_type_zoom(self):
        s = validator.SimmerValidator()

        file = open("src/simmer/schemas/plotting_schema")
        parsed_yaml_file = yaml.load(file, Loader=yaml.SafeLoader)

        document = {"final_im": {"zoom_scale": "some_string"}}
        validated = s.validate(document, parsed_yaml_file)
        file.close()
        self.assertFalse(validated)
