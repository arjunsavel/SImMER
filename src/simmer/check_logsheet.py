# AS
# Created: 7/17/19
# Updated: 2/16/20
# Updated: 6/16/20

"""
Capability to check whether logsheet format is conducive to creating a config.
"""

import numpy as np
import pandas as pd

from . import add_dark_exp as ad


def check_logsheet(inst, log_name, tab=None, add_dark_times=False):
    """Checks for common typos/type errors in the logsheet. Should be
    run if an Excel worksheet is sent.

    Inputs:
        :inst: (Instrument object) instrument for which data is being reduced.
        :log_name: (string) path of the logsheet.
        :tab: (string) tab of interest,
        :add_dark_times: (bool) if true, runs the script within add_dark_exp to add the data from the
                        automated dark script to the log sheet.
    Outputs:
        :failed: (int) number of failed logsheet checks.
    """

    def check_tab(inst, add_dark_times, tab=None):
        """
        Checks for typos for one day in the observing run,
        assuming each day corresponds to a new sheet.

        Inputs:
            :inst: (Instrument object) instrument for which data is being reduced.
            :add_dark_times: (bool) if true, runs the script within add_dark_exp to add the data from the
                            automated dark script to the log sheet.
            :tab: (string) tab of interest. None for a CSV.


        """
        if add_dark_times:
            ad.add_dark_exp(inst, log, raw_dir, tab=None)
        frame_cols = log_frame.columns
        desired_cols = [
            "Object",
            "Start",
            "End",
            "Expose",
            "ExpTime",
            "Filter",
        ]
        missing = []
        failed = 0
        for col in desired_cols:
            if not np.isin(col, frame_cols):
                missing.append(col)
        if len(missing) != 0:
            print(f"Missing columns for {missing}.")
            failed += 1

        objects = log_frame["Object"].dropna().values
        exptimes = log_frame["ExpTime"].dropna().values
        if len(exptimes) != len(objects):
            print("Missing an exposure time.")
            failed += 1

        filters = log_frame["Filter"].dropna().values
        if len(filters) != len(log_frame[log_frame["Object"] != "dark"]):
            print("Missing a filter.")
            failed += 1

        starts = log_frame["Start"].dropna().values
        if len(starts) != len(objects):
            print("Missing a start exposure.")
            failed += 1

        ends = log_frame["End"].dropna().values
        if len(ends) != len(objects):
            print("Missing an end exposure.")
            failed += 1

        coadds = log_frame["Coadds"].dropna().values
        if len(coadds) != len(objects):
            print("Missing a coadd.")
            failed += 1

        if not np.all(exptimes > 0):
            print("There are negative or 0 exposure times.")
            failed += 1
        try:
            inter = ends - starts
            if not np.all(inter >= 0):
                print("Check the start and end exposures.")
                failed += 1
        except ValueError:
            print("Check the start and end exposures.")
            failed += 1

        exposes = log_frame["Expose"].dropna().values
        try:
            if not np.all(exposes == inter + 1):
                print(
                    "Incorrect number of exposures for start and end exposure."
                )
                failed += 1
        except UnboundLocalError:
            print("Incorrect number of exposures for start and end exposure.")
            failed += 1
        print(f"{9-failed}/9 logsheet checks passed.")
        return failed

    failed = 0
    if log_name[-3:] == "csv":
        log_frame = pd.read_csv(log_name)
        failed += check_tab(inst, add_dark_times=add_dark_times)
    elif log_name[-4:] == "xlsx" or log_name[-3:] == "xls":
        log = pd.ExcelFile(log_name, engine="openpyxl")
        if not tab:
            for sheet in log.sheet_names:
                log_frame = pd.read_excel(log, sheet, engine="openpyxl")
                failed += check_tab(
                    inst, add_dark_times=add_dark_times, tab=sheet
                )
        else:
            log_frame = pd.read_excel(log, tab, engine="openpyxl")
            failed += check_tab(inst, add_dark_times=add_dark_times, tab=tab)
    return failed
