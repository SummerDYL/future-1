#!/usr/bin/env python
#-*- coding:utf8 -*-

'''
期货网络模块
'''

import MySQLdb
import datetime
import numpy as np
from pyecharts import Graph, Bar
from scipy.stats import pearsonr
from const import *

# 皮尔逊相关度
# def corr(X, Y):
	# sumX = 0
	# sumY = 0
	# sumXY = 0
	# sumX2 = 0
	# sumY2 = 0
	# n = len(X)
	# cnt = 0
	# for i in xrange(n):
		# if X[i]==None or Y[i]==None:
			# continue
		# cnt += 1
		# sumX += X[i]
		# sumY += Y[i]
		# sumXY += X[i] * Y[i]
		# sumX2 += X[i]**2
		# sumY2 += Y[i]**2
	# n = cnt
	# if cnt<2 or sumX2-sumX**2/n==0 or sumY2-sumY**2/n==0:
		# return 0
	# else:
		# return (sumXY - sumX*sumY/n) / math.sqrt((sumX2-sumX**2/n)*(sumY2-sumY**2/n))

def corr(X, Y):
	'''
	X和Y是登场的数字型序列
	'''
	n = len(X)
	XX = []
	YY = []
	for i in range(n):
		if X[i] and Y[i]:
			XX.append(X[i])
			YY.append(Y[i])
	if len(XX)<=1:
		return 0
	else:
		return pearsonr(XX, YY)[0]
		
		
# 添加数据库连接参数
db_config['db'] = 'commodity'

class Network(object):
	@classmethod
	def tradingCommodityList(cls, begin, end):
		'''
		require: begin和end须为datetime.date类型的变量
		function: 返回begin到end之间进行交易的品种列表
		modified: null
		'''
		result = []
		conn = MySQLdb.connect(**db_config)
		cursor = conn.cursor()
		cursor.execute('select distinct code from contract_daily where date between %s and %s', (begin, end))
		for row in cursor.fetchall():
			result.append(row[0].encode('utf8','ignore'))
		cursor.close()
		conn.close()
		return result

	@classmethod
	def tradingDateList(cls, begin, end):
		'''
		require: begin和end须为datetime.date类型的变量
		function: 返回begin到end之间所有交易日期的列表（按升序排列）
		modified: null
		'''
		result = []
		conn = MySQLdb.connect(**db_config)
		cursor = conn.cursor()
		cursor.execute('select distinct date from contract_daily where date between %s and %s order by date asc', (begin, end))
		for row in cursor.fetchall():
			result.append(row[0])
		cursor.close()
		conn.close()
		return result

	def __init__(self, begin, end, standard):
		'''
		require: begin、end为datetime.date对象，且'20140101'<=begin<=end<='20161231';
		type为string对象，且type in ['close', 'settle', 'volume']
		function: 初始化实例，type为建立网络的期货指标，begin和end限定了时间范围;
		type='close'表示用主力合约收盘价建立网络，type='settle'表示用主力合约结算价建立网络，
		type='volume'表示用所有合约成交量之和建立网络
		modified: begin, end, type, commodities, days, matrix
		'''
		assert type(begin) is datetime.date
		assert type(end) is datetime.date
		assert type(standard) is str and standard in ['log_volume','diff_log_close', 'diff_log_settle','log_settle']
		# 起始日期
		self.begin = begin
		# 终止日期
		self.end = end
		# 建立网络选取的指标: settle(主力合约结算价)、close(主力合约收盘价)、volume(总成交量)
		self.standard = standard
		# 涉及的商品
		self.commodities = self.__class__.tradingCommodityList(self.begin, self.end)
		# 涉及的交易日
		self.days = self.__class__.tradingDateList(self.begin, self.end)
		# 根据type，建立关系矩阵
		self.__Matrix()
		
	def __Matrix(self):
		'''
		require: begin,end,type符合条件，days,commodities正确计算
		function: 根据type，建立邻接矩阵，存于self.matrix
		modified: self.matrix
		'''
		# 商品数量
		n = len(self.commodities)
		# 初始化邻接矩阵，由于自相关系数必为1，所以初始化为单位矩阵
		self.matrix = np.eye(n)
		# 链接数据库
		conn = MySQLdb.connect(**db_config)
		cursor = conn.cursor()
		# 根据不同的type，检索原始数据
		data = []
		if self.standard=='log_volume':
			sql = 'select date,log(sum(volume)+1) from contract_daily \
			where code=%s and date between %s and %s group by date order by date asc'
		elif self.standard=='diff_log_settle' or self.standard=='log_settle':
			sql = 'select contract_daily.date,log(contract_daily.settle+1) from contract_daily,main_contract \
			where contract_daily.code=%s and contract_daily.date between %s and %s and \
			contract_daily.code=main_contract.code and contract_daily.date=main_contract.date and \
			contract_daily.delivery=main_contract.delivery order by date asc'
		elif self.standard=='diff_log_close':
			sql = 'select contract_daily.date,log(contract_daily.close+1) from contract_daily,main_contract \
			where contract_daily.code=%s and contract_daily.date between %s and %s and \
			contract_daily.code=main_contract.code and contract_daily.date=main_contract.date and \
			contract_daily.delivery=main_contract.delivery order by date asc'
		for com in self.commodities:
			_list = []
			tmp = {}
			# 检索数据库
			cursor.execute(sql, (com, self.begin, self.end))
			for row in cursor.fetchall():
				tmp[row[0]] = row[1]
			# 初步处理数据，使之与日期列表一一对应
			for day in self.days:
				if day in tmp:
					_list.append(tmp[day])
				else:
					_list.append(None)
			# 对于差分类指标，还需要处理为差分队列
			if self.standard[:4]=='diff':
				_list = [_list[i]-_list[i-1] if _list[i] and _list[i-1] else None for i in range(1,len(_list))]
			data.append(_list)
		# 关闭数据库
		cursor.close()
		conn.close()
		# 计算每对商品的相关系数
		for i in range(n):
			for j in range(i+1,n):
				r = corr(data[i], data[j])
				self.matrix[i,j] = r
				self.matrix[j,i] = r

	def graph(self, positive_threshold=0.65, nagetive_threshold=-0.65):
		'''
		require: 正确初始化，0<=positive_threshold<=1 and -1<=nagetive_threshold<=0
		function: 根据matrix，绘制echarts.Graph实例并返回
		modified: null
		'''
		graph = Graph('{0}~{1}'.format(self.begin, self.end), width=900, height=700)
		exchanges = ['shfe', 'dce', 'czce']
		nodes = [{'name': code2name[x], 'category':exchanges.index(code2exchange[x])} for x in self.commodities]
		edges = []
		n = len(self.commodities)
		for i in range(n):
			for j in range(i+1,n):
				if self.matrix[i,j] >= positive_threshold or self.matrix[i,j] <= nagetive_threshold:
					edges.append({'source':i, 'target':j, 'value':round(self.matrix[i,j], 3)})
		graph.add('', nodes, edges, exchanges, layout="force", repulsion=8000, is_label_show=True, label_text_size=14,  
				  line_curve=0.2, label_text_color=None, label_emphasis_textcolor=None, label_emphasis_textsize=14)
		return graph

	def histogram(self):
		'''
		require: 正确初始化
		function: 统计所有商品对的相关系数，生成柱状统计图
		modified: null
		'''
		width = 0.05
		bins = int(2.0/width)
		attr = ['%.2f~%.2f'%(-1.+i*width, -1.+(i+1)*width) for i in range(bins)]
		data = [0]*bins
		n = len(self.commodities)
		for i in range(n):
			for j in range(i+1, n):
				data[int((self.matrix[i,j]+1.)/width)] += 1
		bar = Bar('{0}~{1}'.format(self.begin, self.end), width=900, height=500)
		bar.add('', attr, data)
		return bar