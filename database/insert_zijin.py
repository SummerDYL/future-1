#!/usr/bin/env python
# -*- coding:utf8 -*-


import MySQLdb, sys

conn = MySQLdb.connect(host="127.0.0.1", user="root", passwd="19910501", db="investor")
cursor = conn.cursor()

f = open("/home/lizimeng/investor/Zijin2014-2016.csv", 'r')
f.readline()
sql = 'insert into zijin values (' + '%s,'*38 + '%s' + ')'
while True:
	row = f.readline().strip()
	if row=='':
		break
	row = row.split(',')
	row = [x.strip('"') for x in row]
	row = [x if x!='' else None for x in row]
	cursor.execute(sql, tuple(row))
conn.commit()
cursor.close()
conn.close()

	
