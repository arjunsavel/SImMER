"""
Creates config file from logsheet. Will move into either utils or example folder.
"""

import numpy as np
import pandas as pd


class LogsheetError(ValueError):
    """
    For incorrect values within a logsheet that
    can break `create_config` with opaque error messages.
    """

    pass


def create_config(log, config_file, tab=None):
    """
    Create config csv file out of tab in logsheet.

    Inputs:
        :log: (string) path of the logsheet.
        :config_file: (string) path of the desired concrete file, including the
                    file name.
        :tab: (string) tab of logsheet to be turned into.

    """
    if log[-3:] == "csv":
        logdf = pd.read_csv(log)
    elif log[-4:] == "xlsx" or log[-3:] == "xls":
        logdf = pd.read_excel(
            log,
            sheet_name=tab,
            header=0,
            parse_columns=11,
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
    logdf = logdf[pd.notna(logdf["Start"])]
    savedf = logdf[["Object", "ExpTime", "Filter", "Comments"]]

    nrows = len(logdf)

    filenums = []
    for row in range(0, nrows):
        start = logdf["Start"].iloc[row]
        end = logdf["End"].iloc[row]
        if np.isnan(start) or np.isnan(end):
            raise LogsheetError(
                f"Check for empty start or end entry in row {row}."
            )
        filelist = range(start, end + 1)
        filenums.append(filelist)

    savedf["Filenums"] = pd.Series(filenums)

    savedf.to_csv(config_file, index=False)
