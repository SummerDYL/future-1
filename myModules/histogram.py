#!/usr/bin/env python
#-*- coding:utf8 -*-
from pyecharts import Bar

class Histogram(object):
	def __init__(self, data, bin_num, wid):
		self.data = data
		self.bin_num = bin_num
		Max = max(data)
		Min = min(data)
		self.bin_width = int((Max - Min)/bin_num/wid)*wid + wid if 1.0*(Max - Min)/bin_num%wid >= wid/2.0 else int((Max - Min)/bin_num/wid)*wid
		if self.bin_width==0:
			self.bin_width = wid
		self.start = int(Min/wid)*wid + wid if 1.0*Min%wid >= wid/2.0 else int(Min/wid)*wid
		self.bin_num = int((Max-self.start) / self.bin_width) + 1
		
	def get_X(self):
		return ['%g~%g'%(self.start+i*self.bin_width, self.start+(i+1)*self.bin_width) 
				for i in range(self.bin_num)]
				
	def get_Y(self):
		result = [0]*self.bin_num
		for x in self.data:
			x -= self.start
			result[int(x/self.bin_width)] += 1
		return result
		
	def get_echarts(self, title):
		bar = Bar(title, width=1000)
		bar.add("", self.get_X(), self.get_Y(), is_datazoom_show=True)
		return bar
		
if __name__=='__main__':
	import random
	data = []
	for i in xrange(10**4):
		data.append(random.randint(0, 5000))
	hist = Histogram(data, 20, 50)
	hist.get_echarts("test").render()
	