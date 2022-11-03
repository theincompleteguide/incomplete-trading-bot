# encoding: utf-8

# This code is free, THANK YOU!
# It is explained at the guide you can find at www.theincompleteguide.com
# You will also find improvement ideas and explanations

class Stock:

    def __init__(self,name='INIT'):
        self.name = name
        self.currentPrice = 0
        self.direction = ''

    def set_name(self,name):
        self.name = name
