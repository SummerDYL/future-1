#-*- coding:utf8 -*-

import MySQLdb, sys


sql = 'insert into chengjiao values ('+'%s,'*43 + '%s' +')'

conn = MySQLdb.connect(host="127.0.0.1", user="root", passwd="19910501", db="investor")
cursor = conn.cursor()

f = open('/home/lizimeng/investor/ChengJiao2014-2016.csv', 'r')
line_no = 0
for row in f.readlines()[1:]:
	line_no += 1
	row = row.strip()
	if row == '':
		break
	row = row.split(',')
	row = [x.strip('"') for x in row]
	for i in range(44):
		if row[i]=='':
			row[i] = None
	try:
		cursor.execute(sql, tuple(row))
	except Exception, e:
		print line_no
		print row
		print e
		sys.exit(1)
	
conn.commit()
cursor.close()
conn.close()
