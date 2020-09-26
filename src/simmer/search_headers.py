"""Search for issues in FITS file headers similar
    to s0512.fits from night 2015_10_26, which did not
    contain either/both DATAFILE or/and FRAMENUM in
    the header. These issues are only known to occur
    with ShARCS data."""

from glob import glob

import astropy.io.fits as pyfits


def search_headers(raw_dir, write_dir=None):
    """Function to perform search of FITS headers.

    Inputs:
        :raw_dir: (string) absolute path to directory containing raw data.
        :write_dir: (string) absolute path to directory containing raw data.
                    Defaults to None; if this is the case, it's reassigned to
                    the `raw_dir` directory.

    """
    if not write_dir:
        write_dir = raw_dir

    file = write_dir + "headers_wrong.txt"
    textfile = open(file, "w")

    files = glob(raw_dir + "*.fits")
    files = [
        f
        for f in files
        if "sky" not in f.split("/")[-1]
        and "flat" not in f.split("/")[-1]
        and "dark" not in f.split("/")[-1]
    ]

    for file in files:
        # load in header
        head = pyfits.getheader(file)
        keys = head.keys()

        # check keywords
        key1 = "DATAFILE"
        key2 = "FRAMENUM"
        if key1 in keys and key2 in keys:
            head_k1 = head[key1]
            head_k2 = head[key2]

            if int(head_k1[1:]) != head_k2:
                textfile.write(f"{file}\n")

        else:
            print(f"Header Incomplete in {file}!!! ")
            textfile.write(f"{file} HEADER INCOMPLETE\n")

    textfile.close()
