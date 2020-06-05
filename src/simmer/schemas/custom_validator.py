from cerberus import Validator


class SimmerValidator(Validator):
    def _validate_colormaps(self, colormap, field, value):
        """ Test the oddity of a value.

        The rule's arguments are validated against this schema:
        {'type': 'boolean'}
        """
        try:
            cm.get_cmap(colormap)
        except ValueError:  # if the colormap isn't valid
            self._error(field, "Must be an odd number")
