-- 收益没有扣除手续费，单位为元
create table profit_daily (
account char(12) not null comment "账号",
code char(2) not null comment "品种代码",
date date not null comment "日期",
profit double not null default 0 comment "总收益(含交割)",
drop_profit double not null default 0 comment "平仓收益(含交割)",
hold_profit double not null default 0 comment "持仓收益",
pos_profit double not null default 0 comment "正收益(含交割)",
nag_profit double not null default 0 comment "负收益(含交割)",
primary key (account,code,date)
) comment "用户收益状况";
