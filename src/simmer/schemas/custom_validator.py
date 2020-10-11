"""
Includes all custom (i.e., not provided by Cerberus) validators used by SImMER.
"""

import matplotlib.cm as cm
from cerberus import Validator


class SimmerValidator(Validator):
    def _validate_type_mpl(self, value):
        """Test the oddity of a value.

        The rule's arguments are validated against this schema:
        {'type': 'string'}
        """
        try:
            cm.get_cmap(value)
            return True
        except ValueError:  # if the colormap isn't valid
            return False
