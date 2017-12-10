#!/usr/bin/env python
#-*- coding:utf8 -*-

# 引入安装包
import sys, copy, math, types
import MySQLdb
import datetime
import numpy as np
from pyecharts import Graph, Page

db_config = {
	'host': '219.224.169.45',
	'user': 'lizimeng',
	'passwd': 'codegeass',
	'charset': 'utf8',
	'db': 'investor'
}

class CapitalFlow(object):
	'''
	资金流动类
	描述中国期货市场上交易者资金的流动
	目前的版本仅支持一个交易日内一个交易者的市场级资金流动
	
	全局变量:
	tradeday_list	list<datetime.date>		数据涉及时间段内所有交易日列表
	'''
	
	def __init__(self, account, day):
		'''
		参数:
		account		string		交易者的账号
		day			date		交易日
		功能:
		初始化
		'''
		# 检查参数的数据类型
		assert type(account) is types.StringType
		assert type(day) is datetime.date
		
		# 检查日期的范围
		assert datetime.date(2014,1,1)<=day<=datetime.date(2016,12,31)
		
		# 初始化实例属性account
		self.account = account
		
		# 初始化实例属性account
		self.day = day
		
		# 链接数据库
		conn = MySQLdb.connect(**db_config)
		cursor = conn.cursor()
		
		# 求上一个交易日的日期
		sql = 'select lastday from last_day where day=%s'
		cursor.execute(sql, (self.day,))
		self.lastday = cursor.fetchone()[0]
		
		# 入金、出金
		sql = 'select in_money,out_money from zijin where capital_account_new=%s and tradedate=%s'
		cursor.execute(sql, (self.account,self.day))
		self.in_money, self.out_money = cursor.fetchone()
		
		# 交易所列表
		self.exchange_list = ['sfe','dce','czce','cffex']
		
		# 今日结算后的保证金、上日结算后的保证金、持仓收益、平仓收益、手续费
		today_margin_list = []
		lastday_margin_list = []
		drop_profit_list = []
		hold_profit_list = []
		commission_list = []
		
		for exchange in self.exchange_list:
			sql = 'select sum(margin),sum(hold_profit_d) from chicang where capital_account_new=%s and tradedate=%s and seat_code=%s'
			cursor.execute(sql, (self.account,self.day,exchange))
			for row in cursor.fetchall():
				today_margin_list.append(row[0] if row[0] else 0)
				hold_profit_list.append(row[1] if row[1] else 0)
			
			sql = 'select sum(margin) from chicang where capital_account_new=%s and tradedate=%s and seat_code=%s'
			cursor.execute(sql, (self.account,self.lastday,exchange))
			for row in cursor.fetchall():
				lastday_margin_list.append(row[0] if row[0] else 0)
			
			sql = 'select sum(drop_profit_d) from pingcang where capital_account_new=%s and tradedate=%s and seat_code=%s'
			cursor.execute(sql, (self.account,self.day,exchange))
			for row in cursor.fetchall():
				drop_profit_list.append(row[0] if row[0] else 0)
			
			sql = 'select sum(commission) from chengjiao where capital_account_new=%s and tradedate=%s and seat_code=%s'
			cursor.execute(sql, (self.account,self.day,exchange))
			for row in cursor.fetchall():
				commission_list.append(row[0] if row[0] else 0)
		
		assert len(today_margin_list)==len(lastday_margin_list)==len(drop_profit_list)==len(hold_profit_list)==len(commission_list)==len(self.exchange_list)
		
		self.today_margin_array = np.array(today_margin_list, dtype='double')
		self.lastday_margin_array = np.array(lastday_margin_list, dtype='double')
		self.drop_profit_array = np.array(drop_profit_list, dtype='double')
		self.hold_profit_array = np.array(hold_profit_list, dtype='double')
		self.commission_array = np.array(commission_list, dtype='double')
		
		# 关闭数据库
		cursor.close()
		conn.close()
		
		# 计算总收益
		self.profit_array = self.hold_profit_array + self.drop_profit_array
		
		# 保证金追加
		self.exchange_margin_array = self.today_margin_array - self.lastday_margin_array
		
		# 资金流入流出（正表示流出，负表示流入）
		self.flow_array = self.profit_array - self.exchange_margin_array - self.commission_array
		n = len(self.flow_array)
		
		# 拷贝flow_array，把后面对其的修改变为对flow的修改
		flows = copy.deepcopy(self.flow_array)
		
		# 初始化转移矩阵
		self.cf = np.zeros((n+1,n+1))
		
		# 计算总流出量和总流入量
		total_out = sum(filter(lambda x:x>0, self.flow_array))
		total_in = abs(sum(filter(lambda x:x<0, self.flow_array)))
		# 当流出大于流入时，多出的部分流入fund，流量按照比例分配
		if total_out > total_in:
			delta = (total_out - total_in) / total_out
			for i in range(n):
				if flows[i]>0:
					tmp = flows[i] * delta
					flows[i] -= tmp
					self.cf[i,n] = tmp
		elif total_out < total_in:
			delta = (total_in - total_out) / total_in
			for i in range(n):
				if flows[i]<0:
					tmp = abs(flows[i]) * delta
					flows[i] += tmp
					self.cf[n,i] = tmp
		out = []
		_in = []
		total = 0
		for i in range(n):
			if flows[i] > 0:
				out.append(i)
				total += flows[i]
			elif flows[i] < 0:
				_in.append(i)
		for i in _in:
			for j in out:
				tmp = flows[j] / total * abs(flows[i])
				self.cf[j, i] = tmp
		# 可视化
		self.__graph()
	
	def __graph(self):
		'''
		将转移矩阵cf绘制为有向图G，使得G的邻接矩阵为cf
		结果存于实例属性G中
		'''
		# 初始化有向图
		self.G = Graph('账户:{0}\t日期:{1}'.format(self.account, self.day.isoformat()), width=600, height=370)
		# 节点
		V = [{'name':self.exchange_list[i], 'value':round(self.flow_array[i]), 'symbolSize':32} for i in range(4)]
		V.append({'name':'fund', 'symbolSize':32})
		# 边
		E = []
		for i in range(5):
			for j in range(5):
				if self.cf[i,j]>0:
					E.append({'source':i, 'target':j, 'value':round(self.cf[i,j]), 'lineStyle':{'normal':{'width':min(self.cf[i,j]/2000+0.8,10)}}})
		self.G.add('', V, E, graph_repulsion=1000, is_label_show=True, graph_edge_symbol=[None, 'arrow'], graph_edge_symbolsize=30,
				   label_text_size=18, label_emphasis_textsize=18, label_emphasis_textcolor='#000', line_color='#00F')
				
if __name__=='__main__':
	# cf = CapitalFlow('488854682822', datetime.date(2014,3,28))
	# print '               ', cf.exchange_list
	# print 'drop profit    ', cf.drop_profit_array
	# print 'hold profit    ', cf.hold_profit_array
	# print 'exchange margin', cf.exchange_margin_array
	# print 'capital flow   ', cf.flow_array
	# print cf.cf
	conn = MySQLdb.connect(**db_config)
	cursor = conn.cursor()
	cursor.execute('select distinct day from last_day order by day asc')
	days = [x[0] for x in cursor.fetchall()]
	cursor.close()
	conn.close()
	accounts = ['488854682519', '488854682822']
	for account in accounts:
		day = datetime.date(2014,3,1)
		end = datetime.date(2014,4,1)
		page = Page()
		while day < end:
			if day in days:
				cf = CapitalFlow(account, day)
				page.add(cf.G)
			print day
			day += datetime.timedelta(1)
		page.render('{0}.html'.format(account))