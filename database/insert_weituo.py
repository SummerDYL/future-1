#!/usr/bin/env python
#-*- coding:utf8 -*-

import MySQLdb

conn = MySQLdb.connect(host='127.0.0.1', user='root', passwd='19910501', db='investor', charset='utf8')
cursor = conn.cursor()

sql = 'insert into weituo values (' + '%s,'*37 + '%s' + ')'

f = open('/home/lizimeng/investor/WeiTuo2014-2016.csv', 'r')
f.readline()	# 去掉第一行表项
i = 0
while True:
	line = f.readline().strip()
	if line=='':
		break
	line = line.split(',')
	line = [x.strip('"') for x in line]
	line = [x.strip() for x in line]
	line = [x if x else None for x in line]
	cursor.execute(sql, line)
	i += 1
	if i>=200:
		conn.commit()
		i = 0
		
conn.commit()
cursor.close()
conn.close()
