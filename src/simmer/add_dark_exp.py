"""
For ShARCS, the darks are often produced by an automated script at
the end of a night. This module adds these frames to the log sheet.
"""


# AS
# Created: 2/11/19
# Updated: 2/11/19

import glob
import os
from ast import literal_eval

import astropy.io.fits as pyfits
import numpy as np
import pandas as pd
from openpyxl import load_workbook


def add_dark_exp(inst, log, raw_dir, tab=None):
    """Adds dark exposures to the end of log sheet if not specified.

    Inputs:
        :tab: (string) tab of Excel sheet to be used.
        :inst: (Instrument object) instrument for which data is being reduced.
        :log: (string path of the logsheet.
        :raw_dir: (string) path of the directory containing the raw data.
    """

    def get_number(file):
        """For a Shane FITS filename, returns a number given its filename.

        Inputs:
            :file: (string) name of file of interest.
        """
        if file[1] == "0":
            #check below needed because python raises an invalid token error when numbers have leading zeros
            if file[2] == "0":
                number = literal_eval(file[3:5])  # just a safer eval
            else:
                number = literal_eval(file[2:5])  # just a safer eval
        else:
            number = literal_eval(file[1:5])
        return number

    def find_end(column):
        """Finds the end of a column.

        Inputs:
            :column: (pandas Series) column of DataFrame being searched.

        Outputs:
            :end: (int) index of end of column
        """
        for i, item in enumerate(column):
            if not isinstance(item, str) and not isinstance(item, int):
                end = i
                return end
        end = len(column)
        return end

    def log_to_csv(log, tab, end, dark_log):
        """Writes a log to a csv file in current directory.

        Inputs:
            :log: (Excel sheet) logsheet to be analyzed.
            :tab: (string) tab of Excel sheet to be used.
            :end: (int) previous end of columns.
            :new_frame: (pandas DataFrame) new frame to be written into.
        """
        if tab:
            book = load_workbook(log)
            writer = pd.ExcelWriter(log, engine="openpyxl")
            writer.book = book
            writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
            dark_log.to_excel(
                writer, tab, index=False, startrow=end, header=False
            )
            writer.save()
            writer.close()

        else:
            #Save log with darks to a new file so that we don't end up adding
            #darks over and over if we rerun the pipeline
            parts = log.split('.')
            outlog = parts[0] + '_with_darks.'+parts[-1]
            current_log = pd.read_csv(log)

            #add the darks to the end of the data frame
            full_log = current_log.append(dark_log, ignore_index=True)
            full_log.to_csv(outlog, index=False, header=True)
            return outlog



    find_itimes(inst, raw_dir)
    if tab:
        initial_frame = pd.read_excel(
            pd.ExcelFile(log, engine="openpyxl"), tab, engine="openpyxl"
        )
    else:
        initial_frame = pd.read_csv(log)
    # testing that writing works well.
    # then going to create a new dataframe for the darks and append it.

    itimes_file = pd.read_csv(
        raw_dir + "_dark_itimes.txt", sep=" ", header=None
    )
    itimes_file.columns = ["file_name", "itime"]

    sorted_darks = itimes_file.sort_values(by=["file_name"])
    itimes = np.array(sorted_darks["itime"])
    files = np.array(sorted_darks["file_name"])
    starts = []
    ends = []
    objects = []
    exptime = []
    exposes = []

    previous_itime = np.nan #setting to a value that can't possibly match a real exposure time.
    for i, (itime, file) in enumerate(zip(itimes, files)):
        if itime != previous_itime:
            previous_itime = itime
            exptime += [itime]
            starts += [get_number(file)]
            objects += ["dark"]
            if i != 0:
                end_file = files[i - 1]
                ends += [get_number(end_file)]
                exposes += [get_number(end_file) - starts[len(starts) - 2] + 1]
    end_file = files[len(files) - 1]
    ends += [get_number(end_file)]
    exposes += [get_number(end_file) - starts[len(starts) - 1] + 1]


    #comment some of these out; when frame is merged with an existing log,
    #any missing columns should be filled in. NOTE: This probably breaks the excel version,
    #but works for the csv version.
    data_dict = {
        "Object": objects,
        "Start": starts,
        "End": ends,
        "ExpTime": exptime,

        "Coadds": np.full(len(objects), 1),
        "Expose": exposes,
        #"Total_tint": np.full(len(objects), np.nan),
        #"Filter": np.full(len(objects), np.nan),
        #"""Dither (")""": np.full(len(objects), np.nan),
        #"Aperture": np.full(len(objects), np.nan),
        #"TUB": np.full(len(objects), np.nan),
        #"Airmass": np.full(len(objects), np.nan),
        #"PT": np.full(len(objects), np.nan),
        #"KepMag": np.full(len(objects), np.nan),
        #"Companion": np.full(len(objects), np.nan),
        #"Comments": np.full(len(objects), np.nan),

    }

    # if these columns aren't added, .xlsx files will break here!
    if log[-3:] != "csv":
        keys_to_add = [
            "Coadds",
            "Total_tint",
            "Filter",
            """Dither (")""",
            "Aperture",
            "TUB",
            "Airmass",
            "PT",
            "KepMag",
            "Companion",
            "Comments",
        ]
        for key in keys_to_add:
            data_dict[key] = np.full(len(objects), np.nan)

    new_frame = pd.DataFrame(data=data_dict)

    end = find_end(initial_frame["Object"])


    outlog = log_to_csv(log, tab, end, new_frame)

    return outlog



def find_itimes(inst, raw_dir):
    """Read headers for all darks and make a list showing exposure times.

    Inputs:
        :inst: (Instrument object) instrument for which data is being reduced.
        :raw_dir: (string) path of the directory containing the raw data.

    """
    # Set directories
    outdir = raw_dir

    files = glob.glob(raw_dir + inst.file_prefix + "*.fits")
    with open(outdir + "_dark_itimes.txt", "w") as outfile:
        for file in files:
            # load in header:
            head = pyfits.getheader(file)

            hkeys = np.array(list(head.keys()))

            # Strangely, there are one or two files without the "OBJECT" keyword
            # in the header. This check prevents crashes.
            integrations = np.where(hkeys == "TRUITIME")
            objects = np.where(hkeys == "OBJECT")
            if np.logical_and(
                len(hkeys[integrations]) > 0, len(hkeys[objects]) > 0
            ):
                obj = head["OBJECT  "]

                if obj == "dark":
                    #                     if lastitime != itime:
                    #                         lastitime = itime
                    itime = float(round(inst.itime(head),2))
                    outfile.write(
                        os.path.basename(file) + " " + str(itime) + "\n"
                    )
