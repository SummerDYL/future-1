create table times_daily (
account char(12),
code char(3),
date date,
times int not null default 0 comment "总交易次数(含交割)",
open_times int not null default 0 comment "开仓次数",
drop_times int not null default 0 comment "平仓次数(含交割)",
long_times int not null default 0 comment "做多次数",
short_times int not null default 0 comment "做空次数",
today_drop_times int not null default 0 comment "平今次数(含交割)",
primary key (account,code,date)
) comment "用户交易频次";
