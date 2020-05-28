# encoding: utf-8

# This code is free, THANK YOU!
# It is explained at the guide you can found at www.theincompleteguide.com
# You will also find improvement, ideas and explanations
# You can buy it there, or donate. There's been effort here.

import pandas as pd
from datetime import datetime
from datetime import timedelta
import time, threading, requests, re, random, os
import other_functions
from bs4 import BeautifulSoup
from other_functions import *
import gvars

class AssetHandler:
    def __init__(self):
        self.lockedAssets = set() # assets without a defined strategy
        self.tradeableAssets = set() # assets that may be traded today
        self.availableAssets = set() # assets availabe post filter
        self.usedAssets = set() # taken assets being traded
        self.excludedAssets = {'SPCE'} # excluded assets

        try:
            self.rawAssets = pd.read_csv(gvars.RAW_ASSETS,index_col='ticker')
            print("Raw assets loaded from csv correclty")
        except Exception as e:
            print("Could not load raw assets!")
            print(e)
            block_thread()

        self.filter_most_active_assets()

        th = threading.Thread(target=self.unlock_assets) # the process runs appart
        th.start()

    def find_target_asset(self):

        while True:
            self.availableAssets = self.tradeableAssets
            self.availableAssets -= self.usedAssets
            self.availableAssets -= self.excludedAssets
            self.availableAssets -= self.lockedAssets

            try:
                chosenAsset = random.choice(list(self.availableAssets)) # pick a chosen asset randomly
                self.usedAssets.add(chosenAsset)
                print('Chosen asset: ' + chosenAsset)
                print('%i available assets, %i used assets, %i locked assets\n' % (len(self.availableAssets),len(self.usedAssets),len(self.lockedAssets)))
                return chosenAsset
            except:
                print('No more assets available, waiting for assets to be released...')
                time.sleep(60)

    def make_asset_available(self,ticker):

        try:
            self.usedAssets.remove(ticker)
        except Exception as e:
            print('Could not remove %s from used assets, not found' % ticker)
            print(e)

        self.availableAssets.add(ticker)
        print('Asset %s was made available' % ticker)
        time.sleep(1)

    def lock_asset(self,ticker):
        if type(ticker) is not str:
            raise Exception('ticker is not a string!')

        time = datetime.now()
        self.usedAssets.remove(ticker)
        self.lockedAssets.add(ticker)

    def unlock_assets(self):
        # this function unlocks the locked assets periodically

        print('\nUnlocking service initialized')
        while True:
            print('\n# # # Unlocking assets # # #\n')
            time_before = datetime.now()-timedelta(minutes=30)


            self.tradeableAssets = self.tradeableAssets.union(self.lockedAssets)
            print('%d locked assets moved to tradeable' % len(self.lockedAssets))
            self.lockedAssets = set()

            time.sleep(gvars.sleepTimes['UA'])

    def filter_most_active_assets(self):

        print("\nFiltering assets...")

        # min price filter
        self.filteredAssets = self.rawAssets.loc[self.rawAssets.price >= gvars.filterParams['MIN_SHARE_PRICE']]

        # 90-day avg volume filter
        self.filteredAssets = self.filteredAssets.loc[self.rawAssets.avg_vol >= gvars.filterParams['MIN_AVG_VOL']]

        self.tradeableAssets = set(self.filteredAssets.index.tolist())
        print('%i tradeable assets obtained' % len(self.tradeableAssets))
        print(self.tradeableAssets)
