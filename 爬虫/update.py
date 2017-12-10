#!/usr/bin/env python
#-*- coding:utf8 -*-

'''
Usage:
	python update.py exchange [date1 [date2]]
	exchange: 本次运行被更新的交易所，如果更新全部交易所，则填入"all"
	date1: 如果没有date1，则更新昨天的数据；如果没有date2，则跟新date1这一天的数据
	date2: 如果存在date2，则跟新date1到date2之间所有日期的数据
'''

import MySQLdb, sys, datetime, requests, re, time
from DBUtils.SimplePooledDB import PooledDB

# 数据库链接参数
db_config = {
	'host': 'localhost',
	'user': 'root',
	'passwd': 'codegeass',
	'db': 'future',
	'charset': 'utf8'
}

# 大连交易所商品名称与代码对照表
name2code = {
	'豆粕'     : 'm',
	'豆油'     : 'y',
	'豆一'     : 'a',
	'豆二'     : 'b',
	'棕榈油'   : 'p',
	'玉米'     : 'c',
	'玉米淀粉' : 'cs',
	'鸡蛋'     : 'jd',
	'胶合板'   : 'bb',
	'纤维板'   : 'fb',
	'聚乙烯'   : 'l',
	'聚氯乙烯' : 'v',
	'聚丙烯'   : 'pp',
	'焦炭'     : 'j',
	'焦煤'     : 'jm',
	'铁矿石'   : 'i',
}



# 数据库连接池，第二个参数为最大连接数
pool = PooledDB(MySQLdb, 120, **db_config)

# 异常类
class ParameterError(Exception):
	'''
		当参数出现错误(类型或范围)时触发
	'''
	def __init__(self, message):
		super(ParameterError, self).__init__(message)

class UsageError(Exception):
	'''
		当命令行参数错误时触发
	'''
	def __init__(self):
		super(UsageError, self).__init__(__doc__)
		
class NetError(Exception):
	'''
		当获取数据不能时触发
	'''
	def __init__(self, exchange, date):
		super(NetError, self).__init__(exchange+'\t'+date.isoformat())

# 日行情数据类
class DailyData(object):
	def __init__(self, date, exchange):
		'''
			初始化创建实例
			date: 数据的日期
			exchange: 交易所（需使用代码）
		'''
		self.date = date
		# 检查date的类型
		if not isinstance(date, datetime.date):
			raise ParameterError("date is not instance of datetime.date")
		# 检查date的范围
		if not datetime.date(2011,1,1)<=date<=datetime.date.today():
			raise ParameterError("date is out of range")
		
		self.exchange = exchange
		if exchange=='SHFE':
			self.__SHFE()
		elif exchange=='DCE':
			self.__DCE()
		elif exchange=='CZCE':
			self.__CZCE()
		else:
			raise ParameterError("exchange is wrong")
			
	def store(self):
		'''
			将self.data的内容存入数据库
			如果数据库中存在，则删除，保存新数据
		'''
		# 建立数据库连接
		conn = pool.connection()
		cursor = conn.cursor()
		# 存入数据库
		# probe_sql = "select * from contract_daily where date=%s and code=%s and delivery=%s"
		clean_sql = "delete from contract_daily where date=%s and code=%s and delivery=%s"
		insert_sql = "insert into contract_daily (date,code,delivery,settle,open,close,high,low,volume,oi,turnover) values ("+"%s,"*10+"%s"+")"
		for row in self.data:
			# 清理旧数据
			cursor.execute(clean_sql, tuple([self.date]+row[:2]))
			conn.commit()
			# 插入新数据
			cursor.execute(insert_sql, tuple([self.date]+row))
			conn.commit()
		# 关闭连接
		cursor.close()
		conn.close()
	
	def __SHFE(self):
		'''
			爬取上海数据并整理存入self.data
			结果数据的格式为
			[
				[code, delivery, settle, open, close, high, low, volume, oi, turnover],
				...
			]
		'''
		# 初始化
		self.data = []
		# 周末必定没有交易，直接返回结束
		if self.date.isoweekday() in [6,7]:
			return
		# 数据的url
		url = "http://www.shfe.com.cn/data/dailydata/kx/kx{}.dat".format(self.date.strftime('%Y%m%d'))
		# 尝试从网络爬去数据的次数
		T = 5
		# 爬原始数据，直到得到数据或超出次数，每次失败会休眠一段时间再次尝试
		while T>0:
			r = requests.get(url)
			if r.status_code==200:
				break
			time.sleep(2)
			T -= 1
		if T==0:
			return
		rawData = r.json()['o_curinstrument']
		for row in rawData:
			code = row['PRODUCTID'].strip()[:-2]    # 去掉_f
			if code not in ['ag','al','au','bu','cu','fu','hc','pb','rb','ru','wr','zn']:
				continue
			deli = row['DELIVERYMONTH']
			if deli==u'小计':
				continue
			settle = row['SETTLEMENTPRICE']
			open = row['OPENPRICE']
			close = row['CLOSEPRICE']
			high = row['HIGHESTPRICE']
			low = row['LOWESTPRICE']
			volume = row['VOLUME']
			oi = row['OPENINTEREST']
			turnover = None    # 上海交易所的数据中没有每日合约的成交额
			line = [code, deli, settle, open, close, high, low, volume, oi, turnover]
			line = map(lambda x: x if x!=u'' else None, line)
			self.data.append(line) 
	
	def __DCE(self):
		'''
			爬取大连数据并整理存入self.data
		'''
		self.data = []
		# 周末必定没有交易，直接返回结束
		if self.date.isoweekday() in [6,7]:
			return
		# 数据的URL
		url = 'http://www.dce.com.cn/publicweb/quotesdata/exportDayQuotesChData.html'
		# 使用post方式获取数据
		postData = {
			'dayQuotes.variety':'all', 
			'dayQuotes.trade_type':'0', 
			'year': self.date.year, 
			'month':self.date.month-1, 
			'day':self.date.day, 
			'exportFlag':'txt'
		}
		T = 5
		while T>0:
			r = requests.post(url, data=postData)
			if r.status_code==200:
				rawData = r.text.encode('utf8', 'ignore')
				break
			T -= 1
			time.sleep(2)
		if T==0:
			raise NetError('DCE', self.date)
		if len(rawData)<200:
			return
		for row in rawData.split('\n'):
			row = re.split('\s*', row)
			if row[0] not in name2code:
				continue
			code = name2code[row[0]]
			deli = row[1]
			settle = re.sub(',','',row[7])
			volume = re.sub(',','',row[10])
			oi = re.sub(',','',row[11])
			turnover = re.sub(',','',row[13])
			high = re.sub(',','',row[3])
			high = None if high=='0' else high
			low = re.sub(',','',row[4])
			low = None if low=='0' else low
			open = re.sub(',','',row[2])
			open = None if open=='0' else open
			close = re.sub(',','',row[5])
			self.data.append([code, deli, settle, open, close, high, low, volume, oi, turnover])
		
	def __CZCE(self):
		'''
			爬取郑州数据并整理存入self.data
		'''
		pass
	

if __name__=='__main__':
	# 处理命令行参数
	# 检查参数个数
	if len(sys.argv)<2 or len(sys.argv)>4:
		raise UsageError()
	# 确定交易所
	exchange = sys.argv[1].upper()
	if exchange in ['SHFE', 'DCE', 'CZCE']:
		exchange = [exchange]
	elif exchange=='ALL':
		exchange = ['SHFE', 'DCE', 'CZCE']
	else:
		raise UsageError()
	# 确定时间范围
	if len(sys.argv)==2:
		begin = datetime.date.today()
		begin -= datetime.timedelta(1)
		end = begin
	elif len(sys.argv)==3:
		begin = sys.argv[2]
		if not re.match('^\d{8}$',begin):
			raise UsageError()
		try:
			year = int(begin[:4])
			month = int(begin[4:6])
			day = int(begin[6:])
			begin = datetime.date(year, month, day)
			end = begin
		except:
			raise UsageError()
	elif len(sys.argv)==4:
		begin = sys.argv[2]
		if not re.match('^\d{8}$', begin):
			raise UsageError()
		try:
			year = int(begin[:4])
			month = int(begin[4:6])
			day = int(begin[6:])
			begin = datetime.date(year, month, day)
		except:
			raise UsageError()
		
		end = sys.argv[3]
		if not re.match('^\d{8}$', end):
			raise UsageError()
		try:
			year = int(end[:4])
			month = int(end[4:6])
			day = int(end[6:])
			end = datetime.date(year, month, day)
		except:
			raise UsageError()
			
	# 正式开始功能
	day = begin
	while day<=end:
		for ex in exchange:
			dd = DailyData(day, ex)
			# print dd.data
			dd.store()
		print day.isoformat()
		day += datetime.timedelta(1)
		
	print 'finish'

