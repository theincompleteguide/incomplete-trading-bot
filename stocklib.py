# encoding: utf-8


class Stock:

    def __init__(self,name='INIT'):
        self.name = name
        self.currentPrice = 0
        self.direction = ''

    def set_name(self,name):
        self.name = name
