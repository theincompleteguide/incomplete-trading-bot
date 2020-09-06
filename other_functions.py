# encoding: utf-8

# This code is free, THANK YOU!
# It is explained at the guide you can find at www.theincompleteguide.com
# You will also find improvement ideas and explanations

import pandas as pd
import csv, json, time
import os.path
from datetime import datetime
from shutil import copyfile
from scipy.stats import linregress
import numpy as np
import requests
from bs4 import BeautifulSoup
import tulipy as ti

from database import gvars


def block_thread(logger=False,exception=False,thName='',assName=''):
    # this function will lock the thread visually, in case a fatal error happened

    while True:
        if logger:
            logger.info('\n\n\n\n\n\n THREAD %s BLOCKED (%s)\n\n\n\n\n\n' % (thName,assName))
        else:
            print('\n\n\n\n\n\n THREAD %s BLOCKED (%s)\n\n\n\n\n\n' % (thName,assName))

        if exception:
            print(str(exception))

        time.sleep(10)

def million_to_float(string,scale=False):

    try:
        string = string.replace('$','')
        string = string.replace(',','')

        if 'million' in string or 'M' in string:
            string = string.strip(' million')
            string = string.strip('M')
            string = float(string)*1000000

        elif 'billion' in string or 'B' in string:
            string = string.strip(' billion')
            string = string.strip('B')
            string = float(string)*1000000000

        elif 'trillion' in string or 'T' in string:
            string = string.strip(' tillion')
            string = string.strip('T')
            string = float(string)*1000000000000
        elif 'N/A' in string:
            string = 0

        if scale is 'million':
            string = float(string)/1000000
        else:
            string = float(string)

        return round(string,2)
    except Exception as e:
        print(e)

def create_log_folder(path):

    # create the files folder in case it does not exist
    if not os.path.exists(gvars.FILES_FOLDER):
        os.mkdir(gvars.FILES_FOLDER)

    if not os.path.exists(gvars.LOGS_PATH):
        os.mkdir(gvars.LOGS_PATH)

    folderName = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = path  + folderName + '/'

    if not os.path.exists(path):
        os.mkdir(path)

    return path

def load_param(param=False):

    filePath = gvars.PARAMS_PATH
    if not os.path.exists(filePath):
        print('ERROR_PP: params file not found at ' + str(filePath))
        return False

    try:
        with open(filePath) as f:
            data = json.load(f)
    except Exception as e:
        print('WARNING_JS: failed to load json file')
        print(str(e))
        return False

    try:
        if param:
            data = data[param]

        return data
    except Exception as e:
        print('WARNING_PR: params not found at the params file')
        print(str(e))
        return False
