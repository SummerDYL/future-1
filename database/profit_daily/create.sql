-- 收益没有扣除手续费，单位为元
-- 所有rate都是相应的收益除以昨日总保证金
create table profit_daily (
account char(12) comment "账号",
code char(2) comment "商品代码",
date date comment "日期",
profit double comment "总收益",
drop_profit double comment "平仓收益",
hold_profit double comment "持仓收益",
pos_profit double comment "正收益",
nag_profit double comment "负收益",
primary key (account,code,date)
);
