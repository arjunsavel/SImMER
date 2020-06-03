"""search for issues in fits file headers similar 
    to s0512.fits from night 2015_10_26."""

from glob import glob

import astropy.io.fits as pyfits


def search_headers(inst, raw_dir, basedir):
    """Function to perform search."""

    nights = glob(raw_dir + "*/")  # all nightly directories
    file = basedir + "/headers_wrong.txt"
    textfile = open(file, "w")

    for night in nights:
        files = glob(night + "*.fits")

        for file in files:
            # load in header:
            head = pyfits.getheader(file)
            keys = head.keys()

            # check keywords:
            key1 = "DATAFILE"
            key2 = "FRAMENUM"

            if key1 and key2 in keys:
                head_k1 = head[key1]
                head_k2 = head[key2]

                if int(head_k1[1:]) != head_k2:
                    print(int(head_k1[1:]), head_k2, file)
                    textfile.write("{}\n".format(file))

            else:
                print("Header Incomplete in file!!! ", file)
                textfile.write(f"{file} HEADER INCOMPLETE\n")

    textfile.close()
