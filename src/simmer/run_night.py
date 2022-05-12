"""
Wrapper module for running all of SImMER.
"""

import os
import calendar as calendar

import simmer.insts as insts
import simmer.drivers as drivers
from simmer.tests.tests_reduction import download_folder
import simmer.check_logsheet as check
import simmer.add_dark_exp as ad
import simmer.create_config as config

def run_night(wantdate, add_darks=True, just_images=False, sep_skies=False,  skip_reduction=False, verbose=False):
    #wantdate = desired night to reduce. Format is 'YYYY-MM-DD' (e.g., '2019-09-13')

    #Change these for your local installation
    basedir = '/Users/courtney/Documents/data/shaneAO/' #parent directory for data directories
    dirstart = 'data-' #prefix for data directory names
    dirend = '-AO-Courtney.Dressing/' #suffix for data directory names
    logdir = '/Users/courtney/Dropbox/reducing_shane/logsheets/' #directory for logsheets
    logend = '_shane.csv' #suffix for logsheet files

    #set directories
    rawdir = basedir + dirstart + wantdate + dirend
    reddir = rawdir + 'reduced_'+ wantdate + '/'

    #prepare to reduce ShARCS data
    inst = insts.ShARCS()

    #Determine logsheet name
    y, m, d = wantdate.split('-')
    shortdate = d + calendar.month_abbr[int(m)].lower() + y
    log_name = logdir + shortdate + logend

    #Check that logsheet exists
    if os.path.isfile(log_name) == False:
        print('ERROR. Logsheet does not exist. Attempted to find ', log_name, '.')
    if verbose == True:
        print('Reading logsheet ', log_name)

    #Set up config file from logsheet
    tab = None # this is a CSV, so we don't have a tab name of interest.
    failed_tests = check.check_logsheet(inst, log_name, tab)

    #add darks
    if add_darks == True:
        log_name_with_darks = ad.add_dark_exp(inst, log_name, rawdir, tab,)
        if verbose == True:
            print('Saving logsheet with darks added as: ', log_name_with_darks)
    else:
        log_name_with_darks = log_name

    #make config file!
    config_file = 'config_shane_'+shortdate+'.csv'
    config.create_config(log_name_with_darks, config_file)

    #Reduce the data!
    if skip_reduction == True:
        print('files exist')
        return config_file
    else:
        drivers.all_driver(inst, config_file, rawdir, reddir, just_images=just_images, sep_skies=sep_skies, verbose=verbose)
