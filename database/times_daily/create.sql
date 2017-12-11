create table times_daily (
account char(12),
code char(3),
date date,
times int comment "总交易次数",
open_times int comment "开仓次数",
drop_times int comment "平仓次数",
long_times int comment "做多次数",
short_times int comment "做空次数",
today_drop_times int comment "平今次数",
primary key (account,code,date)
);
