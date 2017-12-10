-- 确定profit_daily的主键
-- 从平仓表和持仓表提取主键，因为收益可分为平仓产生和持仓产生s
insert into profit_daily (account,code,date)
select distinct capital_account_new,vari_code,tradedate from pingcang;

insert ignore into profit_daily (account,code,date)
select distinct capital_account_new,vari_code,tradedate from chicang;

-- 计算drop_profit
update profit_daily set drop_profit=(select sum(drop_profit_d) from pingcang
where capital_account_new=account and vari_code=code and tradedate=date);

-- 计算hold_profit
update profit_daily set hold_profit=(select sum(hold_profit_d) from chicang
where capital_account_new=account and vari_code=code and tradedate=date);

-- 计算pos_profit（分持仓、平仓）
update profit_daily set pos_profit=(select sum(drop_profit_d) from pingcang
where capital_account_new=account and vari_code=code and tradedate=date and drop_profit_d>0);

update profit_daily set pos_profit=pos_profit+(select sum(hold_profit_d) from chicang
where capital_account_new=account and vari_code=code and tradedate=date and hold_profit_d>0);

-- 计算neg_profit（分持仓、平仓）
update profit_daily set neg_profit=(select )
