"""
Creates config file from logsheet. Will move into either utils or example folder.
"""


import warnings

import numpy as np
import pandas as pd


class LogsheetError(ValueError):
    """
    For incorrect values within a logsheet that
    can break `create_config` with opaque error messages.
    """

    pass


def read_logsheet(log, tab=None):
    """
    Reads in a user-defined logsheet, either in CSV or XLSX form.

    Inputs:
        log: (string) path to logsheet.
        tab: (string) sheet of a multiple-page logsheet

    Outputs:
        logdf: (pd.DataFrame) logsheet in Pandas DataFrame.
    """
    if log[-3:] == "csv":
        logdf = pd.read_csv(log)
    elif log[-4:] == "xlsx" or log[-3:] == "xls":

        xl = pd.ExcelFile(log, engine="openpyxl")
        num_sheets = len(xl.sheet_names)
        if num_sheets > 1 and not tab:
            warnings.warn(
                "Warning — more than one tab in logsheet, but no tab selected. Reading entire logsheet."
            )

        logdf = pd.read_excel(
            log,
            sheet_name=tab,
            header=0,
            engine="openpyxl",
            converters={
                "Comments": str,
                "Start": int,
                "End": int,
                "Object": str,
                "Filter": str,
            },
        )
    else:
        raise NotImplementedError(
            "Specified log file is of an " "unsupported file type."
        )

    return logdf


def get_filenums(logdf):
    """
    Inputs:
        logdf: (pd.DataFrame) logsheet in Pandas DataFrame.

    Outputs:
        filenums: (list) numbers associated with each file
            associated with each object.
    """
    nrows = len(logdf)
    filenums = []

    for row in range(0, nrows):
        start = logdf["Start"].iloc[row]
        end = logdf["End"].iloc[row]
        if not np.issubdtype(start, np.integer) or not np.issubdtype(
            end, np.integer
        ):
            raise LogsheetError(
                f"Check that the start and end entries in row {row} are integers and not empty."
            )
        filelist = range(start, end + 1)
        filenums.append(filelist)

    return filenums


def isolate_columns(logdf):
    """
    Isolates the subset of columns in a DataFrame log that are
    relevant to data reduction.

    Inputs:
        logdf: (pd.DataFrame) logsheet in Pandas DataFrame.

    Outputs:
        savedf: (pd.DataFrame) Pandas DataFrame to be used in reduction.
    """
    if "Method" not in logdf.columns:
        savedf = logdf[["Object", "ExpTime", "Filter", "Comments"]]
        savedf['Method'] = "saturated"  # default for now
    else:
        savedf = logdf[["Object", "ExpTime", "Filter", "Comments", "Method"]]

    return savedf


def create_config(log, config_file, tab=None):
    """
    Create config csv file out of tab in logsheet.

    Inputs:
        :log: (string) path of the logsheet.
        :config_file: (string) path of the desired concrete file, including the
                    file name.
        :tab: (string) tab of logsheet to be turned into.

    """
    logdf = read_logsheet(log, tab)

    logdf = logdf[pd.notna(logdf["Start"])]
    # TODO: add error in case a tab was not selected and should have been

    savedf = isolate_columns(logdf)

    filenums = get_filenums(logdf)

    savedf["Filenums"] = pd.Series(filenums)

    savedf.to_csv(config_file, index=False)
