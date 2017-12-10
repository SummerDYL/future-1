create table margin_daily (
account char(12),
code char(3) comment "特殊字段值all表示所有品种加和",
date date,
margin double,
market_margin double,
primary key (account,code,date)
);