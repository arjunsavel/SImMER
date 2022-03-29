#CDD
# Created: 3/7/22
# Updated: 3/7/22
# Updated: 3/7/22

"""
Confirm that the values listed in a configuration file match the values in the FITS file headers.
"""

import numpy as np
import pandas as pd
import astropy.io.fits as pyfits
import os as os


from . import utils as u

def validate_config(config, raw_dir, inst, verbose=False):
    if verbose == True:
        print('inspecting directory: ', raw_dir)

    objissues = 0
    expissues = 0
    filtissues = 0
    for ii in np.arange(len(config)):
        #work through each line of config file
        this = config.iloc[ii]
        flist = u.make_filelist(raw_dir, eval(this.Filenums), inst)
        #print('this line: ', np.array(this))
        for file in flist:
            head = pyfits.getheader(file)
            hkeys = np.array(list(head.keys()))
            if verbose == True:
                print('     ', os.path.basename(file), head['Object'], head['RA'], head['DEC'])

                #Check object for everything but flats
            if np.logical_and(this.Object.casefold() != head['Object'].casefold(), this.Object.casefold() != 'flat'):
                if verbose == True:
                    print('ISSUE! ', os.path.basename(file))
                    print('     Object mismatch')
                    print('     Object in header: ', head['Object'])
                    print('     Object in logsheet: ', this.Object)
                    print('     Pointing RA: ', head['RA'])
                    print('     Pointing Dec ', head['DEC'])
                    print('**************************')
                objissues += 1

            #check object for flats
            if this.Object.casefold() == 'flat':
                if np.logical_and(np.logical_and(head['Object'].casefold() != 'flat',head['Object'].casefold() != 'flats'), np.logical_and(head['Object'].casefold().replace(" ","") != 'skyflat',head['Object'].casefold().replace(" ","") != 'domeflat')):
                    if verbose == True:
                        print('ISSUE! ', os.path.basename(file))
                        print('     Object mismatch')
                        print('     Object in header: ', head['Object'])
                        print('     Object in logsheet: ', this.Object)
                        print('     Pointing RA: ', head['RA'])
                        print('     Pointing Dec ', head['DEC'])
                        print('**************************')
                    objissues += 1

            #Compare exposure times. ITIME0 is recorded in microseconds
            if (this.ExpTime != (head['ITIME0']/1e6)):
                if verbose == True:
                    print('ISSUE! ', os.path.basename(file))
                    print('     ExpTime mismatch')
                    print('     ExpTime in header: ', head['ITIME0']/1e6)
                    print('     ExpTime in logsheet: ', this.ExpTime)
                    print('**************************')
                expissues += 1

                #Check filters for everything but darks & J+Ch4-1.2 images
            if this.Object != "dark":
                if np.logical_and(this.Filter != head['FILT1NAM'], this.Filter.casefold().replace(" ","") != 'J+Ch4-1.2'.casefold()):
                    if verbose == True:
                        print('ISSUE! ', os.path.basename(file))
                        print('     Filter mismatch')
                        print('     Filters in header: ', head['FILT1NAM'],head['FILT2NAM'])
                        print('     Filter in logsheet: ', this.Filter)
                        print('**************************')
                    filtissues += 1

                #Check filters for J+Ch1.4
                if this.Filter.casefold().replace(" ","") == 'J+Ch4-1.2':
                    if np.logical_or(head['FILT1NAM'] != 'J', head['FILT2NAM'] != 'Ch4-1.2'):
                        if verbose == True:
                            print('ISSUE! ', os.path.basename(file))
                            print('     Filter mismatch')
                            print('     Filters in header: ', head['FILT1NAM'],head['FILT2NAM'])
                            print('     Filter in logsheet: ', this.Filter)
                            print('**************************')
                        filtissues += 1

    #always print the final summary
    print('#################################')
    print('SUMMARY')
    print('Object mismatches: ', objissues)
    print('Exptime mismatches: ', expissues)
    print('Filter mismatches: ', filtissues)
    print('#################################')
