#!/usr/bin/env python
#-*- coding:utf8 -*-

from capitalFlow import CapitalFlow
import datetime
from pyecharts import Graph
import MySQLdb

db_config = {
	'host':'219.224.169.45',
	'user': 'lizimeng',
	'passwd': 'codegeass',
	'charset': 'utf8',
	'db': 'investor'
}

mats = []

account = '488854682519'

day = datetime.date(2014,3,1)
end = datetime.date(2014,3,31)

conn = MySQLdb.connect(**db_config)
cursor = conn.cursor()
cursor.execute('select distinct day from last_day order by day asc')
days = [x[0] for x in cursor.fetchall()]
cursor.close()
conn.close()

while day<=end:
	if day in days:
		cf = CapitalFlow(account, day)
		mats.append(cf.cf)
	day += datetime.timedelta(1)


# graph
graph = Graph('账户:{0}\t日期:2014年3月'.format(account), width=1000, height=618)
V = [{'name':x, 'symbolSize':28} for x in ['sfe','dce','czce','cffex', 'fund']]
E = []
for mat in mats:
	for i in range(5):
		for j in range(5):
			if mat[i,j]>0:
				E.append({'source':i, 'target':j, 'value':round(mat[i,j]), 
				'lineStyle':{'normal':{'width':min(mat[i,j]/2000+0.8,10)}}})
graph.add('', V, E, graph_repulsion=2000, is_label_show=True, graph_edge_symbol=[None, 'arrow'], graph_edge_symbolsize=28,
		label_text_size=18, label_emphasis_textsize=18, label_emphasis_textcolor='#000', line_color='#00F', line_curve=0.2)
		
graph.render()