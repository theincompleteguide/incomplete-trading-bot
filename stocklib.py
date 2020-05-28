# encoding: utf-8

# This code is free, THANK YOU!
# It is explained at the guide you can found at www.theincompleteguide.com
# You will also find improvement, ideas and explanations
# You can buy it there, or donate. There's been effort here.

class Stock:

    def __init__(self,name='INIT'):
        self.name = name
        self.currentPrice = 0
        self.direction = ''

    def set_name(self,name):
        self.name = name
