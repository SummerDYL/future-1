#!/usr/bin/env python
#-*- coding:utf8 -*-

import MySQLdb
conn = MySQLdb.connect(host='127.0.0.1', user='root', passwd='19910501', db='investor', charset='utf8')
cursor = conn.cursor()

sql = "insert into zhanghu values (" + "%s,"*26 + "%s" + ")"

f = open('/home/lizimeng/data/investor/ZhangHu.csv', 'r')
f.readline()
while True:
	row = f.readline()
	row = row.strip()
	if row=='':
		break
	row = row.decode('gbk','ignore')
	row = row.encode('utf8','ignore')
	row = row.split(',')
	row = [x.strip('"') for x in row]
	cursor.execute(sql, row)
conn.commit()
cursor.close()
conn.close()