
create table commission_daily (
account char(12),
code char(3),
date date,
commi double commit "总手续费",
open_commi double commit "开仓手续费",
drop_commi double commit "平仓手续费",
primary key (account,code,date)
);