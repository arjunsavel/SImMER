"""
Utility functions (used in the registration stage) adapted from SciPy 1.2.0 that have
since been deprecated (see the LICENSE.MD file at the project root directory).
"""

import numpy as np
from PIL import Image


def bytescale(data, high=255, low=0):
    """
    Byte scales an image.

    inputs:
        :data: (ndarray) PIL image data array.
        :cmin: (int)  Bias scaling of small values. Default is ``data.min()``.
        :cmax: (int) Bias scaling of large values. Default is ``data.max()``.
        :high: (int) Scale max value to `high`.  Default is 255.
        :low: (int) Scale min value to `low`.  Default is 0.

    outputs:
        img_array : (uint8 ndarray) The byte-scaled array.
    """
    cmin = data.min()
    cmax = data.max()

    cscale = cmax - cmin
    if cscale == 0:
        cscale = 1

    scale = float(high - low) / cscale
    bytedata = (data - cmin) * scale + low
    return (bytedata.clip(low, high) + 0.5).astype(np.uint8)


def toimage(arr, high=255, low=0):
    """Takes a numpy array and returns a PIL image.
    This function is only available if Python Imaging Library (PIL) is installed.
    The mode of the PIL image depends on the array shape and the `pal` and
    `mode` keywords.
    For 2-D arrays, if `pal` is a valid (N,3) byte-array giving the RGB values
    (from 0 to 255) then ``mode='P'``, otherwise ``mode='L'``, unless mode
    is given as 'F' or 'I' in which case a float and/or integer array is made.
    .. warning::
        This function uses `bytescale` under the hood to rescale images to use
        the full (0, 255) range if ``mode`` is one of ``None, 'L', 'P', 'l'``.
        It will also cast data for 2-D images to ``uint32`` for ``mode=None``
        (which is the default).
    Notes
    -----
    For 3-D arrays if one of the dimensions is 3, the mode is 'RGB'
    by default or 'YCbCr' if selected.
    The numpy array must be either 2 dimensional or 3 dimensional.
    """

    data = np.asarray(arr)
    shape = list(data.shape)
    valid = len(shape) == 2 or (
        (len(shape) == 3) and ((3 in shape) or (4 in shape))
    )
    if not valid:
        raise ValueError(
            "'arr' does not have a suitable array shape for " "any mode."
        )
    if len(shape) == 2:
        shape = (shape[1], shape[0])  # columns show up first
        bytedata = bytescale(data, high=high, low=low)
        image = Image.frombytes("L", shape, bytedata.tostring())
        return image


def imresize(arr):
    """
    Resizes an image.

    inputs
        :arr: (ndarray) The array of image to be resized.

    outputs:
        :im_resized: (ndarray) The resized array of image.
    """

    im = toimage(arr)
    size = tuple((np.array(im.size) * 100.0).astype(int))
    im_resized = im.resize(size, resample=3)
    im_resized = np.array(im_resized)
    return im_resized
