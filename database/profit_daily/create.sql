-- 收益没有扣除手续费，单位为元
-- 所有rate都是相应的收益除以昨日总保证金
create table profit_daily (
account char(12) not null comment "账号",
code char(2) not null comment "商品代码",
date date not null comment "日期",
profit double not null default 0 comment "总收益",
drop_profit double not null default 0 comment "平仓收益",
hold_profit double not null default 0 comment "持仓收益",
pos_profit double not null default 0 comment "正收益",
nag_profit double not null default 0 comment "负收益",
primary key (account,code,date)
);
