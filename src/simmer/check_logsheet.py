# AS
# Created: 7/17/19
# Updated: 2/16/20

"""
Capability to check whether logsheet format is conducive to creating a config.
"""

import add_dark_exp as ad
import numpy as np
import pandas as pd


def check_logsheet(inst, log_name, date=None, add_dark_times=False):
    """Checks for common typos/type errors in the logsheet. Should be
    run if an Excel worksheet is sent.

    Inputs:
        :inst: (Instrument object) instrument for which data is being reduced.
        :log_name: (string) path of the logsheet.
        :date: (string) date of interest, assuming that tabs in the file are different dates
        :add_dark_times: (bool) if true, runs the script within add_dark_exp to add the data from the
                        automated dark script to the log sheet.
    """

    def check_date(date, inst, add_dark_times):
        """
        Checks for typos for one day in the observing run,
        assuming each day corresponds to a new sheet.

        Inputs:
            :date: (string) date of interest, assuming that tabs in the file are different dates
            :inst: (Instrument object) instrument for which data is being reduced.
            :add_dark_times: (bool) if true, runs the script within add_dark_exp to add the data from the
                            automated dark script to the log sheet.

        """
        if add_dark_times:
            ad.add_dark_exp(date, inst)
        frame_cols = log_frame.columns
        desired_cols = [
            "Object",
            "Start",
            "End",
            "Expose",
            "ExpTime",
            "Coadds",
            "Filter",
            "Total_tint",
        ]
        missing = []
        for col in desired_cols:
            if not np.isin(col, frame_cols):
                missing.append(col)
        assert len(missing) == 0, f"Missing columns for {missing}."
        print(f"1/9 tests passed for {date}")

        objects = log_frame["Object"].dropna().values
        exptimes = log_frame["ExpTime"].dropna().values
        assert len(exptimes) == len(objects), "Missing an exposure time."
        print(f"2/9 tests passed for {date}")

        filters = log_frame["Filter"].dropna().values
        assert len(filters) == len(
            log_frame[log_frame["Object"] != "dark"]
        ) or len(filters) == len(objects), "Missing a filter."
        print(f"3/9 tests passed for {date}")

        starts = log_frame["Start"].dropna().values
        assert len(starts) == len(objects), "Missing a start exposure."
        print(f"4/9 tests passed for {date}")

        ends = log_frame["End"].dropna().values
        assert len(ends) == len(objects), "Missing a start exposure."
        print(f"5/9 tests passed for {date}")

        coadds = log_frame["Coadds"].dropna().values
        assert len(coadds) == len(objects), "Missing a coadd."
        print(f"6/9 tests passed for {date}")

        assert np.all(exptimes > 0), "There are negative or 0 exposure times."
        print(f"7/9 tests passed for {date}")

        inter = ends - starts
        assert np.all(inter >= 0), "Check the start and end exposures."
        print(f"8/9 tests passed for {date}")

        exposes = log_frame["Expose"].dropna().values
        assert np.all(
            exposes == inter + 1
        ), "Incorrect number of exposures for start and end exposure."
        print(f"9/9 tests passed for {date}")

    if log_name[-3:] == "csv":
        log_frame = pd.read_csv(log_name)
    elif log_name[-4:] == "xlsx" or log[-3:] == "xls":
        log = pd.ExcelFile(log_name)
        log_frame = pd.read_excel(log, date)
    if not date:
        for sheet in log.sheet_names:
            check_date(sheet, inst, add_dark_times=add_dark_times)
    else:
        check_date(date, inst, add_dark_times=add_dark_times)


class checker:
    def __init__(self):
        return

    def check_config(self, filepath):
        try:
            config = pd.read_csv(filepath)
        except FileNotFoundError:
            print("Incorrect file path.")
        # check that it has the right columns
        # check that it has the same rows in each column

    def check_fits(self):
        # go through all the raw data
        # open and close it all, make sure it's all fits
        return

    def check_plot_config():
        return
