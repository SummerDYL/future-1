create table times_daily (
account char(12),
code char(3),
date date,
times int not null default 0 comment "总交易次数",
open_times int not null default 0 comment "开仓次数",
drop_times int not null default 0 comment "平仓次数",
long_times int not null default 0 comment "做多次数",
short_times int not null default 0 comment "做空次数",
today_drop_times int not null default 0 comment "平今次数",
primary key (account,code,date)
);
